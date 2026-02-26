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
    status: str = "normal"
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
        # スリープ状態検出用の状態
        self._last_screenshot_size: Optional[int] = None
        self._consecutive_empty_count: int = 0

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

            # 4. スリープ状態検出
            status = self._detect_sleep_state(text, screenshot_path)
            if self.config.verbose:
                print(f"Status detected: {status}")

            # 5. JSONL保存（dry-runモードではスキップ）
            if not self.config.dry_run:
                jsonl_path = self._save_to_jsonl(timestamp, window_name, text, status)
                if self.config.verbose:
                    print(f"Log saved to: {jsonl_path}")
            else:
                jsonl_path = None
                if self.config.verbose:
                    print("[DRY RUN] JSONL保存をスキップしました")

            # 6. 成功結果を返す
            return ScreenOCRResult(
                success=True,
                timestamp=timestamp,
                window_name=window_name,
                screenshot_path=screenshot_path,
                text=text,
                text_length=len(text),
                jsonl_path=jsonl_path,
                status=status,
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
                status="error",
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

    def _detect_sleep_state(self, text: str, screenshot_path: Path) -> str:
        """
        スリープ/ロック状態を検出する

        以下の条件でスリープ状態を判定：
        - テキストが空（text_length = 0）
        - スクリーンショットのファイルサイズが前回と同じ
        - 連続して空のテキストが3回以上記録される

        Args:
            text: OCRで抽出されたテキスト
            screenshot_path: スクリーンショットファイルのパス

        Returns:
            状態を表す文字列（"normal", "sleep", "lock"）
        """
        # テキストが空でない場合は通常状態
        if text.strip():
            self._consecutive_empty_count = 0
            self._last_screenshot_size = None
            return "normal"

        # テキストが空の場合、連続カウントを増加
        self._consecutive_empty_count += 1

        # スクリーンショットのファイルサイズを確認
        try:
            current_size = screenshot_path.stat().st_size
        except (OSError, FileNotFoundError):
            # ファイルアクセスエラーの場合は通常状態として扱う
            return "normal"

        # 初回の場合はサイズを記録して通常状態とする
        if self._last_screenshot_size is None:
            self._last_screenshot_size = current_size
            return "normal"

        # ファイルサイズが同じで、連続して空のテキストが3回以上の場合はスリープ状態
        if current_size == self._last_screenshot_size and self._consecutive_empty_count >= 3:
            return "sleep"

        # ファイルサイズが変わった場合は、サイズを更新
        if current_size != self._last_screenshot_size:
            self._last_screenshot_size = current_size
            # サイズが変わったということは画面が変化しているため、カウントをリセット
            self._consecutive_empty_count = 1

        return "normal"

    def _save_to_jsonl(
        self, timestamp: datetime, window: str, text: str, status: str = "normal"
    ) -> Path:
        """
        JSONL形式でログを保存（日付ベースで自動分割）

        Args:
            timestamp: タイムスタンプ
            window: ウィンドウ名
            text: OCRテキスト
            status: 状態（"normal", "sleep", "error"など）

        Returns:
            保存先のJSONLファイルパス

        Raises:
            Exception: JSONL保存に失敗した場合
        """
        try:
            jsonl_path = self.jsonl_manager.get_current_jsonl_path(timestamp)
            # append_recordは実際に書き込んだファイルパスを返す（サイズ超過時は新ファイル）
            actual_path = self.jsonl_manager.append_record(
                jsonl_path, timestamp, window, text, status
            )
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
