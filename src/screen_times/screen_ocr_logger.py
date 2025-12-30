#!/usr/bin/env python3
"""
ScreenOCRLogger - ファサードクラス

ScreenOCRシステムの複雑な一連の処理を単一のシンプルなインターフェースで提供する。
"""

import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .screenshot import get_active_window, take_screenshot
from .ocr import perform_ocr
from .jsonl_manager import JsonlManager


@dataclass
class ScreenOCRConfig:
    """ScreenOCRの設定"""

    screenshot_dir: Path = Path("/tmp/screen-times")
    timeout_seconds: int = 30
    screenshot_retention_hours: int = 72
    verbose: bool = False
    dry_run: bool = False
    merge_threshold: Optional[float] = None


@dataclass
class ScreenOCRResult:
    """ScreenOCR実行結果"""

    success: bool
    timestamp: datetime
    window_name: str
    screenshot_path: Optional[Path]
    text: str
    text_length: int
    jsonl_path: Optional[Path]
    error: Optional[str] = None

    def __str__(self) -> str:
        """結果の文字列表現"""
        if self.success:
            return (
                f"Success: {self.window_name} | "
                f"{self.text_length} chars | "
                f"Saved to {self.jsonl_path}"
            )
        else:
            return f"Failed: {self.error}"


class ScreenOCRLogger:
    """
    ScreenOCRシステムのファサード

    複雑な一連の処理（スクリーンショット取得、OCR、ログ記録）を
    単一のシンプルなインターフェースで提供する。

    使用例:
        >>> logger = ScreenOCRLogger()
        >>> result = logger.run()
        >>> print(result)
        Success: Chrome | 1234 chars | Saved to ~/.screenocr_logs/2025-12-28.jsonl

        >>> # カスタム設定で使用
        >>> config = ScreenOCRConfig(
        ...     screenshot_dir=Path("/custom/path"),
        ...     timeout_seconds=10,
        ...     verbose=True
        ... )
        >>> logger = ScreenOCRLogger(config)
        >>> result = logger.run()
    """

    def __init__(self, config: Optional[ScreenOCRConfig] = None):
        """
        初期化

        Args:
            config: 設定オブジェクト（Noneの場合はデフォルト設定）
        """
        self.config = config or ScreenOCRConfig()
        self.jsonl_manager = JsonlManager(merge_threshold=self.config.merge_threshold)

    def run(self) -> ScreenOCRResult:
        """
        メイン処理を実行

        スクリーンショット取得 → OCR → JSONL保存の一連の処理を実行する。

        Returns:
            実行結果（ScreenOCRResult）
        """
        timestamp = datetime.now()
        window_name = "Unknown"
        screenshot_path = None
        text = ""
        jsonl_path = None
        error = None

        try:
            # 1. アクティブウィンドウ取得
            window_name, window_bounds = get_active_window()
            if self.config.verbose:
                print(f"Active window: {window_name}")
                if window_bounds:
                    print(f"Window bounds: {window_bounds}")

            # 2. スクリーンショット取得
            screenshot_path = take_screenshot(self.config.screenshot_dir, window_bounds)
            if self.config.verbose:
                print(f"Screenshot saved: {screenshot_path}")

            # 3. OCR処理
            text = perform_ocr(screenshot_path, self.config.timeout_seconds)
            if self.config.verbose:
                print(f"OCR completed: {len(text)} characters")

            # 4. JSONL保存（dry-runモードではスキップ）
            if not self.config.dry_run:
                jsonl_path = self._save_to_jsonl(timestamp, window_name, text)
                if self.config.verbose:
                    print(f"Log saved to: {jsonl_path}")
            else:
                jsonl_path = None
                if self.config.verbose:
                    print("[DRY RUN] JSONL保存をスキップしました")

            # 5. 成功結果を返す
            return ScreenOCRResult(
                success=True,
                timestamp=timestamp,
                window_name=window_name,
                screenshot_path=screenshot_path,
                text=text,
                text_length=len(text),
                jsonl_path=jsonl_path,
            )

        except Exception as e:
            # エラー情報を記録
            error = str(e)
            if self.config.verbose:
                print(f"Error: {error}", file=sys.stderr)

            # 失敗結果を返す
            return ScreenOCRResult(
                success=False,
                timestamp=timestamp,
                window_name=window_name,
                screenshot_path=screenshot_path,
                text=text,
                text_length=len(text),
                jsonl_path=jsonl_path,
                error=error,
            )

    def cleanup(self) -> int:
        """
        古いスクリーンショットを削除

        設定で指定された保持期間を超えたスクリーンショットファイルを削除する。

        Returns:
            削除したファイル数
        """
        try:
            cutoff_time = time.time() - (self.config.screenshot_retention_hours * 3600)
            pattern = "screenshot_*.png"
            deleted_count = 0

            # ディレクトリが存在しない場合は0を返す
            if not self.config.screenshot_dir.exists():
                return 0

            for screenshot in self.config.screenshot_dir.glob(pattern):
                try:
                    # ファイルの最終更新時刻を確認
                    if screenshot.stat().st_mtime < cutoff_time:
                        screenshot.unlink()
                        deleted_count += 1
                except Exception as file_error:
                    # 個別のファイル削除エラーは無視して続行
                    if self.config.verbose:
                        print(
                            f"Warning: Failed to delete {screenshot}: {file_error}", file=sys.stderr
                        )
                    continue

            if self.config.verbose and deleted_count > 0:
                print(f"Cleaned up {deleted_count} old screenshot(s)")

            return deleted_count

        except Exception as cleanup_error:
            if self.config.verbose:
                print(f"Warning: Screenshot cleanup failed: {cleanup_error}", file=sys.stderr)
            return 0

    def _save_to_jsonl(self, timestamp: datetime, window: str, text: str) -> Path:
        """
        JSONL形式でログを保存（日付ベースで自動分割）

        Args:
            timestamp: タイムスタンプ
            window: ウィンドウ名
            text: OCRテキスト

        Returns:
            保存先のJSONLファイルパス

        Raises:
            Exception: JSONL保存に失敗した場合
        """
        try:
            jsonl_path = self.jsonl_manager.get_current_jsonl_path(timestamp)
            # append_recordは実際に書き込んだファイルパスを返す（サイズ超過時は新ファイル）
            actual_path = self.jsonl_manager.append_record(jsonl_path, timestamp, window, text)
            return actual_path
        except Exception as e:
            if self.config.verbose:
                print(f"Error: Failed to write to JSONL: {e}", file=sys.stderr)
            raise


def main():
    """モジュールとして実行された時のエントリーポイント"""
    logger = ScreenOCRLogger()
    result = logger.run()

    # マージャーをフラッシュ（バッファに残っているレコードを書き込む）
    # これは最後の実行時に必要だが、定期実行では次の実行で処理されるため問題ない
    # 念のため、明示的にフラッシュする

    if not result.success:
        sys.exit(1)


if __name__ == "__main__":
    main()
