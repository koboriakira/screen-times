#!/usr/bin/env python3
"""
ScreenOCR Logger - Main Script

毎分スクリーンショットを取得し、Vision FrameworkでOCR処理を行い、
JSONL形式でログを記録するメインスクリプト。

ファサードパターンを使用してシンプルなインターフェースで実行する。
"""

import sys
from pathlib import Path

from .screen_ocr_logger import ScreenOCRLogger, ScreenOCRConfig


# 設定
SCREENSHOT_DIR = Path("/tmp/screen-times")
TIMEOUT_SECONDS = 30  # OCRタイムアウト（日本語認識のため長めに設定）
SCREENSHOT_RETENTION_HOURS = 72  # スクリーンショット保持期間（時間）


def main():
    """メイン処理"""
    try:
        # 設定を準備
        config = ScreenOCRConfig(
            screenshot_dir=SCREENSHOT_DIR,
            timeout_seconds=TIMEOUT_SECONDS,
            screenshot_retention_hours=SCREENSHOT_RETENTION_HOURS,
            verbose=True,  # 詳細ログを出力
        )

        # ファサードを初期化
        logger = ScreenOCRLogger(config)

        # メイン処理を実行
        result = logger.run()

        # 結果を表示
        if result.success:
            print(f"Screenshot will be kept for {SCREENSHOT_RETENTION_HOURS} hours")
        else:
            print(f"Fatal error: {result.error}", file=sys.stderr)
            sys.exit(1)

        # 古いスクリーンショットをクリーンアップ
        logger.cleanup()

    except Exception as main_error:
        print(f"Fatal error: {main_error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
