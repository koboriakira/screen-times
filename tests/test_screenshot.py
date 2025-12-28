#!/usr/bin/env python3
"""
スクリーンショット取得の統合テスト
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from screen_times.screenshot import take_screenshot


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS only")
class TestTakeScreenshot:
    """スクリーンショット取得のテスト"""

    def test_take_screenshot_success(self):
        """正常なスクリーンショット取得のテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot_dir = Path(tmpdir)
            result = take_screenshot(screenshot_dir)

            # スクリーンショットファイルが作成されたことを確認
            assert result.exists()
            assert result.parent == screenshot_dir
            assert result.name.startswith("screenshot_")
            assert result.name.endswith(".png")

    def test_take_screenshot_directory_creation(self):
        """ディレクトリが存在しない場合の作成テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot_dir = Path(tmpdir) / "new_dir"

            # ディレクトリが存在しないことを確認
            assert not screenshot_dir.exists()

            # スクリーンショット取得
            result = take_screenshot(screenshot_dir)

            # ディレクトリが作成され、ファイルが作成されたことを確認
            assert screenshot_dir.exists()
            assert result.exists()

    @patch("screen_times.screenshot.subprocess.run")
    def test_take_screenshot_command_error(self, mock_run):
        """screencaptureコマンドエラーのテスト"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "screencapture")

        screenshot_dir = Path("/tmp/test")
        screenshot_dir.mkdir(exist_ok=True)

        with pytest.raises(subprocess.CalledProcessError):
            take_screenshot(screenshot_dir)
