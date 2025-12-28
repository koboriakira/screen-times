#!/usr/bin/env python3
"""
OCR処理のテストスクリプト

特定の画像ファイルに対してOCR処理を実行し、結果を確認
"""

import sys
from pathlib import Path

# scriptsディレクトリから相対的にインポート
sys.path.insert(0, str(Path(__file__).parent))
from ocr import perform_ocr


def test_ocr(image_path: str):
    """
    指定された画像に対してOCR処理を実行

    Args:
        image_path: 画像ファイルのパス
    """
    path = Path(image_path)
    if not path.exists():
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)

    print(f"Processing: {image_path}")
    print("-" * 80)

    # OCR実行（タイムアウトを長めに設定）
    text = perform_ocr(path, timeout_seconds=30)

    print("\n" + "=" * 80)
    print("OCR Result:")
    print("=" * 80)
    print(text)
    print("=" * 80)
    print(f"\nTotal characters: {len(text)}")
    print(f"Total lines: {len(text.splitlines())}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_ocr.py <image_path>")
        sys.exit(1)

    test_ocr(sys.argv[1])
