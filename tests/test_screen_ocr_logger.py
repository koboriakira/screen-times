#!/usr/bin/env python3
"""
ScreenOCRLogger（ファサードクラス）のユニットテスト
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from screen_times.screen_ocr_logger import ScreenOCRLogger, ScreenOCRConfig, ScreenOCRResult


class TestScreenOCRConfig:
    """ScreenOCRConfig設定クラスのテスト"""

    def test_default_config(self):
        """デフォルト設定のテスト"""
        config = ScreenOCRConfig()
        assert config.screenshot_dir == Path("/tmp/screen-times")
        assert config.timeout_seconds == 30
        assert config.screenshot_retention_hours == 72
        assert config.verbose is False

    def test_custom_config(self):
        """カスタム設定のテスト"""
        config = ScreenOCRConfig(
            screenshot_dir=Path("/custom/path"),
            timeout_seconds=10,
            screenshot_retention_hours=48,
            verbose=True,
        )
        assert config.screenshot_dir == Path("/custom/path")
        assert config.timeout_seconds == 10
        assert config.screenshot_retention_hours == 48
        assert config.verbose is True


class TestScreenOCRResult:
    """ScreenOCRResult結果クラスのテスト"""

    def test_success_result_str(self):
        """成功結果の文字列表現テスト"""
        result = ScreenOCRResult(
            success=True,
            timestamp=datetime(2025, 12, 28, 10, 30, 0),
            window_name="Chrome",
            screenshot_path=Path("/tmp/screenshot.png"),
            text="Test text",
            text_length=9,
            jsonl_path=Path("/tmp/log.jsonl"),
            status="normal",
        )

        str_repr = str(result)
        assert "Success" in str_repr
        assert "Chrome" in str_repr
        assert "9 chars" in str_repr
        assert "/tmp/log.jsonl" in str_repr

    def test_failed_result_str(self):
        """失敗結果の文字列表現テスト"""
        result = ScreenOCRResult(
            success=False,
            timestamp=datetime(2025, 12, 28, 10, 30, 0),
            window_name="Chrome",
            screenshot_path=None,
            text="",
            text_length=0,
            jsonl_path=None,
            status="error",
            error="Test error message",
        )

        str_repr = str(result)
        assert "Failed" in str_repr
        assert "Test error message" in str_repr


class TestScreenOCRLogger:
    """ScreenOCRLoggerファサードクラスのテスト"""

    def test_init_with_default_config(self):
        """デフォルト設定での初期化テスト"""
        logger = ScreenOCRLogger()
        assert logger.config is not None
        assert logger.config.screenshot_dir == Path("/tmp/screen-times")
        assert logger.jsonl_manager is not None

    def test_init_with_custom_config(self):
        """カスタム設定での初期化テスト"""
        config = ScreenOCRConfig(screenshot_dir=Path("/custom/path"), timeout_seconds=10)
        logger = ScreenOCRLogger(config)
        assert logger.config.screenshot_dir == Path("/custom/path")
        assert logger.config.timeout_seconds == 10

    @patch("screen_times.screen_ocr_logger.perform_ocr")
    @patch("screen_times.screen_ocr_logger.take_screenshot")
    @patch("screen_times.screen_ocr_logger.get_active_window")
    def test_run_success(self, mock_get_window, mock_take_screenshot, mock_perform_ocr):
        """正常なrun実行のテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # モックの設定
            mock_get_window.return_value = ("TestApp", (0, 0, 800, 600))
            mock_screenshot_path = Path(tmpdir) / "test_screenshot.png"
            mock_screenshot_path.touch()  # ダミーファイル作成
            mock_take_screenshot.return_value = mock_screenshot_path
            mock_perform_ocr.return_value = "Test OCR text"

            # 設定とロガーの作成
            config = ScreenOCRConfig(screenshot_dir=Path(tmpdir), verbose=False)
            logger = ScreenOCRLogger(config)

            # 実行
            result = logger.run()

            # 検証
            assert result.success is True
            assert result.window_name == "TestApp"
            assert result.text == "Test OCR text"
            assert result.text_length == 13
            assert result.screenshot_path == mock_screenshot_path
            assert result.jsonl_path is not None
            assert result.error is None

            # モックが正しく呼ばれたことを確認
            mock_get_window.assert_called_once()
            mock_take_screenshot.assert_called_once()
            mock_perform_ocr.assert_called_once()

    @patch("screen_times.screen_ocr_logger.perform_ocr")
    @patch("screen_times.screen_ocr_logger.take_screenshot")
    @patch("screen_times.screen_ocr_logger.get_active_window")
    def test_run_failure(self, mock_get_window, mock_take_screenshot, mock_perform_ocr):
        """run実行時のエラーハンドリングテスト"""
        # モックの設定（例外を発生させる）
        mock_get_window.side_effect = Exception("Test error")

        # 設定とロガーの作成
        config = ScreenOCRConfig(verbose=False)
        logger = ScreenOCRLogger(config)

        # 実行
        result = logger.run()

        # 検証
        assert result.success is False
        assert result.error == "Test error"
        assert result.text == ""
        assert result.jsonl_path is None

    @patch("screen_times.screen_ocr_logger.perform_ocr", side_effect=Exception("OCR failed"))
    @patch("screen_times.screen_ocr_logger.take_screenshot")
    @patch("screen_times.screen_ocr_logger.get_active_window")
    def test_run_ocr_failure(self, mock_get_window, mock_take_screenshot, mock_perform_ocr):
        """OCR処理失敗時のテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # モックの設定
            mock_get_window.return_value = ("TestApp", (0, 0, 800, 600))
            mock_screenshot_path = Path(tmpdir) / "test_screenshot.png"
            mock_screenshot_path.touch()
            mock_take_screenshot.return_value = mock_screenshot_path

            # 設定とロガーの作成
            config = ScreenOCRConfig(screenshot_dir=Path(tmpdir), verbose=False)
            logger = ScreenOCRLogger(config)

            # 実行
            result = logger.run()

            # 検証
            assert result.success is False
            assert "OCR failed" in result.error

    def test_cleanup_no_files(self):
        """クリーンアップ（ファイルなし）のテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScreenOCRConfig(screenshot_dir=Path(tmpdir), verbose=False)
            logger = ScreenOCRLogger(config)

            # クリーンアップ実行
            deleted_count = logger.cleanup()

            # 検証
            assert deleted_count == 0

    def test_cleanup_with_old_files(self):
        """クリーンアップ（古いファイルあり）のテスト"""
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot_dir = Path(tmpdir)

            # 古いファイルを作成（保持期間を超えている）
            old_file = screenshot_dir / "screenshot_old.png"
            old_file.touch()

            # ファイルのタイムスタンプを古くする
            old_time = time.time() - (74 * 3600)  # 74時間前
            import os

            os.utime(old_file, (old_time, old_time))

            # 新しいファイルも作成（保持期間内）
            new_file = screenshot_dir / "screenshot_new.png"
            new_file.touch()

            # 設定とロガーの作成（保持期間72時間）
            config = ScreenOCRConfig(
                screenshot_dir=screenshot_dir, screenshot_retention_hours=72, verbose=False
            )
            logger = ScreenOCRLogger(config)

            # クリーンアップ実行
            deleted_count = logger.cleanup()

            # 検証
            assert deleted_count == 1
            assert not old_file.exists()
            assert new_file.exists()

    def test_cleanup_nonexistent_directory(self):
        """存在しないディレクトリのクリーンアップテスト"""
        config = ScreenOCRConfig(screenshot_dir=Path("/nonexistent/path"), verbose=False)
        logger = ScreenOCRLogger(config)

        # クリーンアップ実行（エラーなく完了すべき）
        deleted_count = logger.cleanup()

        # 検証
        assert deleted_count == 0

    @patch("screen_times.screen_ocr_logger.perform_ocr")
    @patch("screen_times.screen_ocr_logger.take_screenshot")
    @patch("screen_times.screen_ocr_logger.get_active_window")
    def test_run_with_verbose_output(
        self, mock_get_window, mock_take_screenshot, mock_perform_ocr, capsys
    ):
        """verbose=Trueでのログ出力テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # モックの設定
            mock_get_window.return_value = ("TestApp", (0, 0, 800, 600))
            mock_screenshot_path = Path(tmpdir) / "test_screenshot.png"
            mock_screenshot_path.touch()
            mock_take_screenshot.return_value = mock_screenshot_path
            mock_perform_ocr.return_value = "Test text"

            # 設定とロガーの作成
            config = ScreenOCRConfig(screenshot_dir=Path(tmpdir), verbose=True)  # verbose有効化
            logger = ScreenOCRLogger(config)

            # 実行
            _ = logger.run()

            # 標準出力を確認
            captured = capsys.readouterr()
            assert "Active window: TestApp" in captured.out
            assert "Screenshot saved:" in captured.out
            assert "OCR completed:" in captured.out
            assert "Status detected:" in captured.out
            assert "Log saved to:" in captured.out

    @patch("screen_times.screen_ocr_logger.perform_ocr")
    @patch("screen_times.screen_ocr_logger.take_screenshot")
    @patch("screen_times.screen_ocr_logger.get_active_window")
    def test_detect_sleep_state_normal(
        self, mock_get_window, mock_take_screenshot, mock_perform_ocr
    ):
        """通常状態の検出テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # モックの設定
            mock_get_window.return_value = ("TestApp", (0, 0, 800, 600))
            mock_screenshot_path = Path(tmpdir) / "test_screenshot.png"
            mock_screenshot_path.write_text("dummy content")  # ダミーファイル作成
            mock_take_screenshot.return_value = mock_screenshot_path
            mock_perform_ocr.return_value = "Some text content"  # 空でないテキスト

            # 設定とロガーの作成
            config = ScreenOCRConfig(screenshot_dir=Path(tmpdir), verbose=False)
            logger = ScreenOCRLogger(config)

            # 実行
            result = logger.run()

            # 検証
            assert result.success is True
            assert result.status == "normal"
            assert result.text == "Some text content"

    @patch("screen_times.screen_ocr_logger.perform_ocr")
    @patch("screen_times.screen_ocr_logger.take_screenshot")
    @patch("screen_times.screen_ocr_logger.get_active_window")
    def test_detect_sleep_state_sleep(
        self, mock_get_window, mock_take_screenshot, mock_perform_ocr
    ):
        """スリープ状態の検出テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # モックの設定
            mock_get_window.return_value = ("Electron", (0, 0, 800, 600))
            mock_screenshot_path = Path(tmpdir) / "test_screenshot.png"
            # 同じサイズのファイルを作成
            mock_screenshot_path.write_bytes(b"x" * 90000)  # 90KB（88KBに近いサイズ）
            mock_take_screenshot.return_value = mock_screenshot_path
            mock_perform_ocr.return_value = ""  # 空のテキスト

            # 設定とロガーの作成
            config = ScreenOCRConfig(screenshot_dir=Path(tmpdir), verbose=False)
            logger = ScreenOCRLogger(config)

            # 複数回実行してスリープ状態を検出させる
            results = []
            for i in range(4):  # 4回実行
                # 同じサイズのファイルを維持
                mock_screenshot_path.write_bytes(b"x" * 90000)
                result = logger.run()
                results.append(result)

            # 検証：consecutive_empty_count >= 3 でスリープ検出
            # 1回目: count=1, last_size=None→記録 → normal
            # 2回目: count=2, same size → normal
            # 3回目: count=3, same size, >=3 → sleep
            assert results[0].status == "normal"
            assert results[1].status == "normal"
            assert results[2].status == "sleep"
            assert results[3].status == "sleep"

    @patch("screen_times.screen_ocr_logger.perform_ocr")
    @patch("screen_times.screen_ocr_logger.take_screenshot")
    @patch("screen_times.screen_ocr_logger.get_active_window")
    def test_detect_sleep_state_recovery(
        self, mock_get_window, mock_take_screenshot, mock_perform_ocr
    ):
        """スリープ状態からの復帰テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # モックの設定
            mock_get_window.return_value = ("TestApp", (0, 0, 800, 600))
            mock_screenshot_path = Path(tmpdir) / "test_screenshot.png"
            mock_take_screenshot.return_value = mock_screenshot_path

            # 設定とロガーの作成
            config = ScreenOCRConfig(screenshot_dir=Path(tmpdir), verbose=False)
            logger = ScreenOCRLogger(config)

            # 1. スリープ状態を作り出す（空のテキスト、同じファイルサイズで3回）
            mock_perform_ocr.return_value = ""
            for i in range(3):
                mock_screenshot_path.write_bytes(b"x" * 90000)
                result = logger.run()

            # 4回目でスリープ状態になる
            mock_screenshot_path.write_bytes(b"x" * 90000)
            result = logger.run()
            assert result.status == "sleep"

            # 2. 復帰：テキストが検出される
            mock_perform_ocr.return_value = "Recovered text"
            mock_screenshot_path.write_bytes(b"y" * 100000)  # 異なるサイズ
            result = logger.run()

            # 検証：復帰により normal 状態になる
            assert result.status == "normal"
            assert result.text == "Recovered text"

    def test_detect_sleep_state_error_status(self):
        """エラー時のステータステスト"""
        config = ScreenOCRConfig(verbose=False)
        logger = ScreenOCRLogger(config)

        with patch(
            "screen_times.screen_ocr_logger.get_active_window", side_effect=Exception("Test error")
        ):
            result = logger.run()

            # 検証
            assert result.success is False
            assert result.status == "error"
            assert result.error == "Test error"
