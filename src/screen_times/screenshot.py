#!/usr/bin/env python3
"""
スクリーンショット取得モジュール

アクティブウィンドウの検出とスクリーンショット撮影を担当
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_active_window() -> tuple[str, Optional[tuple[int, int, int, int]]]:
    """
    AppleScript経由でアクティブウィンドウ名と位置を取得

    Returns:
        (アプリケーション名, ウィンドウ位置 (x, y, width, height) または None)
    """
    script_path = Path(__file__).parent / "resources" / "screenshot_window.applescript"

    try:
        result = subprocess.run(
            ["osascript", str(script_path)], capture_output=True, text=True, timeout=3, check=True
        )
        app_name = result.stdout.strip() or "Unknown"

        # PyObjCでウィンドウ情報を取得
        try:
            from Quartz import (
                CGWindowListCopyWindowInfo,
                kCGWindowListOptionOnScreenOnly,
                kCGNullWindowID,
            )

            # 画面上の全ウィンドウ情報を取得
            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly, kCGNullWindowID
            )

            # アクティブなアプリのウィンドウを探す
            # 正規化して比較用の文字列を作成
            normalized_app_name = app_name.lower().replace("-", "").replace(" ", "")

            for window in window_list:
                owner_name = window.get("kCGWindowOwnerName", "")
                layer = window.get("kCGWindowLayer", 0)

                # レイヤー0（通常のウィンドウ）のみ対象
                if layer != 0:
                    continue

                # 正規化して比較
                normalized_owner = owner_name.lower().replace("-", "").replace(" ", "")

                # 部分一致または完全一致で判定
                # (例: "wezterm-gui" と "WezTerm"、"Electron" と "Code")
                if (
                    normalized_app_name in normalized_owner
                    or normalized_owner in normalized_app_name
                    or normalized_app_name == normalized_owner
                ):
                    bounds = window.get("kCGWindowBounds", {})
                    if bounds:
                        x = int(bounds["X"])
                        y = int(bounds["Y"])
                        w = int(bounds["Width"])
                        h = int(bounds["Height"])
                        print(
                            f"Debug: Matched window - Owner: {owner_name}, "
                            f"Bounds: ({x}, {y}, {w}, {h})",
                            file=sys.stderr,
                        )
                        return (app_name, (x, y, w, h))

            return (app_name, None)

        except Exception as bounds_error:
            print(f"Warning: Could not get window bounds: {bounds_error}", file=sys.stderr)
            return (app_name, None)

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as get_window_error:
        print(f"Warning: Failed to get active window: {get_window_error}", file=sys.stderr)
        return ("Unknown", None)


def take_screenshot(
    screenshot_dir: Path, window_bounds: Optional[tuple[int, int, int, int]] = None
) -> Path:
    """
    スクリーンショットを取得

    Args:
        screenshot_dir: スクリーンショット保存先ディレクトリ
        window_bounds: ウィンドウの位置とサイズ (x, y, w, h)。Noneの場合は画面全体

    Returns:
        スクリーンショットのパス
    """
    # ディレクトリが存在しない場合は作成
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = screenshot_dir / f"screenshot_{timestamp}.png"

    try:
        if window_bounds:
            x, y, w, h = window_bounds
            # -R オプションで特定の領域をキャプチャ
            cmd = ["screencapture", "-x", "-R", f"{x},{y},{w},{h}", str(screenshot_path)]
        else:
            # 画面全体をキャプチャ（フォールバック）
            cmd = ["screencapture", "-x", str(screenshot_path)]

        subprocess.run(cmd, check=True, timeout=5)

        if not screenshot_path.exists():
            raise FileNotFoundError(f"Screenshot was not created: {screenshot_path}")

        return screenshot_path
    except (
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
        FileNotFoundError,
    ) as screenshot_error:
        print(f"Error: Failed to take screenshot: {screenshot_error}", file=sys.stderr)
        raise
