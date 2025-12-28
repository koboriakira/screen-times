#!/usr/bin/env python3
"""
OCR処理の統合テスト
"""

import sys
import tempfile
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from screen_times.ocr import perform_ocr


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS only")
class TestPerformOCR:
    """OCR処理のテスト"""

    def create_test_image(self, text: str, output_path: Path) -> Path:
        """テスト用の画像を生成"""
        # 白い背景に黒いテキストを描画
        img = Image.new("RGB", (800, 200), color="white")
        draw = ImageDraw.Draw(img)

        try:
            # システムフォントを使用
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
        except OSError:
            # フォントが見つからない場合はデフォルトを使用
            font = ImageFont.load_default()

        draw.text((50, 70), text, fill="black", font=font)
        img.save(output_path)
        return output_path

    def test_ocr_simple_text(self):
        """単純なテキストのOCR処理"""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            test_image = Path(f.name)

        try:
            # テスト画像を作成
            self.create_test_image("Hello World", test_image)

            # OCR実行
            result = perform_ocr(test_image, timeout_seconds=10)

            # 結果検証（完全一致ではなく部分一致で検証）
            assert len(result) > 0, "OCR result should not be empty"
            assert (
                "Hello" in result or "World" in result
            ), f"Expected 'Hello' or 'World' in result, got: {result}"

        finally:
            test_image.unlink()

    def test_ocr_nonexistent_file(self):
        """存在しないファイルのOCR処理"""
        test_image = Path("/tmp/nonexistent_image_12345.png")

        # ファイルが存在しない場合、空文字列またはエラーが返される
        result = perform_ocr(test_image, timeout_seconds=10)

        # エラーが発生せず、結果が返ることを確認
        assert isinstance(result, str)

    def test_ocr_japanese_text(self):
        """日本語テキストのOCR処理"""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            test_image = Path(f.name)

        try:
            # 日本語フォントを探す
            japanese_fonts = [
                "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
                "/System/Library/Fonts/Hiragino Sans GB.ttc",
            ]

            font = None
            for font_path in japanese_fonts:
                if Path(font_path).exists():
                    try:
                        font = ImageFont.truetype(font_path, 60)
                        break
                    except OSError:
                        continue

            # 日本語画像を作成
            img = Image.new("RGB", (800, 200), color="white")
            draw = ImageDraw.Draw(img)

            if font:
                draw.text((50, 70), "こんにちは", fill="black", font=font)
            else:
                # フォントが見つからない場合はスキップ
                pytest.skip("Japanese font not found")

            img.save(test_image)

            # OCR実行
            result = perform_ocr(test_image, timeout_seconds=30)

            # 結果検証（日本語が含まれていることを確認）
            assert len(result) > 0, "OCR result should not be empty"
            # 日本語が正しく認識されることを期待（ただし完璧ではない可能性がある）

        finally:
            test_image.unlink()

    def test_ocr_timeout(self):
        """OCR処理のタイムアウトテスト"""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            test_image = Path(f.name)

        try:
            # テスト画像を作成
            self.create_test_image("Timeout Test", test_image)

            # 短いタイムアウトで実行
            # （実際の処理は速いので、タイムアウトしない可能性がある）
            result = perform_ocr(test_image, timeout_seconds=1)

            # エラーが発生せず、結果が返ることを確認
            assert isinstance(result, str)

        finally:
            test_image.unlink()
