#!/usr/bin/env python3
"""
ログ分析ツール

JSONL形式のログを解析し、日次/週次/月次レポートを生成する
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple


def parse_args():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(
        description="ScreenOCR Logger のログを分析してレポートを生成"
    )
    
    # 期間指定
    period_group = parser.add_mutually_exclusive_group()
    period_group.add_argument(
        "--date",
        type=str,
        metavar="YYYY-MM-DD",
        help="特定の日付を分析"
    )
    period_group.add_argument(
        "--week",
        action="store_true",
        help="過去7日間を分析"
    )
    period_group.add_argument(
        "--month",
        action="store_true",
        help="当月を分析"
    )
    
    # その他のオプション
    parser.add_argument(
        "--log-file",
        type=str,
        default=str(Path.home() / ".screenocr_logger.jsonl"),
        help="ログファイルのパス（デフォルト: ~/.screenocr_logger.jsonl）"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="上位N件のウィンドウ/キーワードを表示（デフォルト: 10）"
    )
    parser.add_argument(
        "--keywords",
        type=int,
        default=20,
        metavar="N",
        help="抽出するキーワード数（デフォルト: 20）"
    )
    parser.add_argument(
        "--no-keywords",
        action="store_true",
        help="キーワード抽出をスキップ"
    )
    
    return parser.parse_args()


def get_date_range(args) -> Tuple[datetime, datetime]:
    """日付範囲を取得"""
    now = datetime.now()
    
    if args.date:
        # 特定の日付
        target_date = datetime.strptime(args.date, "%Y-%m-%d")
        start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif args.week:
        # 過去7日間
        end = now
        start = now - timedelta(days=7)
    elif args.month:
        # 当月
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    else:
        # デフォルト: 今日
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    
    return start, end


def load_logs(log_file: str, start: datetime, end: datetime) -> List[Dict]:
    """指定期間のログを読み込む"""
    logs = []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    timestamp = datetime.fromisoformat(entry['timestamp'])
                    
                    if start <= timestamp <= end:
                        logs.append(entry)
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    # 不正な行はスキップ
                    continue
    except FileNotFoundError:
        print(f"エラー: ログファイルが見つかりません: {log_file}", file=sys.stderr)
        sys.exit(1)
    
    return logs


def analyze_windows(logs: List[Dict]) -> Dict[str, int]:
    """ウィンドウごとの記録回数を集計"""
    window_counts = Counter()
    
    for entry in logs:
        window = entry.get('window', 'Unknown')
        window_counts[window] += 1
    
    return dict(window_counts)


def analyze_text_stats(logs: List[Dict]) -> Dict[str, float]:
    """テキスト統計を計算"""
    total_entries = len(logs)
    total_chars = sum(entry.get('text_length', 0) for entry in logs)
    
    return {
        'total_entries': total_entries,
        'total_chars': total_chars,
        'avg_chars': total_chars / total_entries if total_entries > 0 else 0,
    }


def extract_keywords(logs: List[Dict], top_n: int = 20, min_length: int = 3) -> List[Tuple[str, int]]:
    """テキストから頻出キーワードを抽出"""
    import re
    
    word_counter = Counter()
    
    # 除外する一般的な単語（ストップワード）
    stopwords = {
        # 英語
        'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
        'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
        'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
        'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
        # 日本語（助詞など）
        'の', 'に', 'は', 'を', 'た', 'が', 'で', 'て', 'と', 'し', 'れ',
        'さ', 'ある', 'いる', 'も', 'する', 'から', 'な', 'こと', 'として',
        'い', 'や', 'れる', 'など', 'なっ', 'ない', 'この', 'ため', 'その',
        # 記号
        'www', 'http', 'https', 'com', 'org', 'html', 'css', 'js',
    }
    
    for entry in logs:
        text = entry.get('text', '')
        if not text:
            continue
        
        # 単語を抽出（英数字と日本語）
        # 英語: 単語境界で分割
        english_words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # 日本語: 連続するひらがな・カタカナ・漢字
        japanese_words = re.findall(r'[ぁ-んァ-ヶ一-龥]+', text)
        
        # 単語をカウント（最小長とストップワードでフィルタ）
        for word in english_words + japanese_words:
            if len(word) >= min_length and word.lower() not in stopwords:
                word_counter[word] += 1
    
    return word_counter.most_common(top_n)


def format_duration(minutes: int) -> str:
    """分を時間:分形式にフォーマット"""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}時間{mins}分"
    else:
        return f"{mins}分"


def calculate_window_time(window_counts: Dict[str, int], interval_minutes: int = 1) -> Dict[str, int]:
    """ウィンドウごとの推定時間を計算（分単位）"""
    return {window: count * interval_minutes for window, count in window_counts.items()}


def print_report(logs: List[Dict], window_counts: Dict[str, int], 
                text_stats: Dict[str, float], keywords: List[Tuple[str, int]],
                start: datetime, end: datetime, args):
    """レポートを出力"""
    
    # ヘッダー
    if args.date:
        period_str = f"Daily Activity Report: {args.date}"
    elif args.week:
        period_str = f"Weekly Activity Report: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
    elif args.month:
        period_str = f"Monthly Activity Report: {start.strftime('%Y年%m月')}"
    else:
        period_str = f"Daily Activity Report: {start.strftime('%Y-%m-%d')}"
    
    print(f"{'=' * len(period_str)}")
    print(period_str)
    print(f"{'=' * len(period_str)}")
    print()
    
    # データがない場合
    if not logs:
        print("この期間のログデータがありません。")
        return
    
    # 基本統計
    print("📊 基本統計")
    print(f"  総キャプチャ数: {text_stats['total_entries']:,} 回")
    print(f"  総文字数: {text_stats['total_chars']:,} 文字")
    print(f"  平均文字数: {text_stats['avg_chars']:.1f} 文字/回")
    print()
    
    # アクティブウィンドウ
    print("🪟 アクティブウィンドウ")
    window_times = calculate_window_time(window_counts)
    total_minutes = sum(window_times.values())
    
    # 上位N件を表示
    sorted_windows = sorted(window_times.items(), key=lambda x: x[1], reverse=True)
    for i, (window, minutes) in enumerate(sorted_windows[:args.top], 1):
        percentage = (minutes / total_minutes * 100) if total_minutes > 0 else 0
        duration_str = format_duration(minutes)
        print(f"  {i:2d}. {window:<30} ({duration_str:>12}, {percentage:5.1f}%)")
    
    if len(sorted_windows) > args.top:
        other_count = len(sorted_windows) - args.top
        other_minutes = sum(minutes for _, minutes in sorted_windows[args.top:])
        other_percentage = (other_minutes / total_minutes * 100) if total_minutes > 0 else 0
        duration_str = format_duration(other_minutes)
        print(f"      その他 {other_count} 件              ({duration_str:>12}, {other_percentage:5.1f}%)")
    
    print()
    
    # キーワード
    if not args.no_keywords and keywords:
        print("🔑 頻出キーワード")
        # 4列で表示
        cols = 4
        for i in range(0, len(keywords), cols):
            row = keywords[i:i+cols]
            formatted_row = [f"{word:<12} ({count:>4})" for word, count in row]
            print("  " + "  ".join(formatted_row))
        print()
    
    # 時間範囲
    if logs:
        first_timestamp = datetime.fromisoformat(logs[0]['timestamp'])
        last_timestamp = datetime.fromisoformat(logs[-1]['timestamp'])
        print("⏰ 記録時間範囲")
        print(f"  開始: {first_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  終了: {last_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        duration = last_timestamp - first_timestamp
        hours = duration.total_seconds() / 3600
        print(f"  期間: {hours:.1f} 時間")


def main():
    """メイン処理"""
    args = parse_args()
    
    # 日付範囲を取得
    start, end = get_date_range(args)
    
    # ログを読み込み
    logs = load_logs(args.log_file, start, end)
    
    # 分析
    window_counts = analyze_windows(logs)
    text_stats = analyze_text_stats(logs)
    
    # キーワード抽出
    keywords = []
    if not args.no_keywords:
        keywords = extract_keywords(logs, top_n=args.keywords)
    
    # レポート出力
    print_report(logs, window_counts, text_stats, keywords, start, end, args)


if __name__ == "__main__":
    main()
