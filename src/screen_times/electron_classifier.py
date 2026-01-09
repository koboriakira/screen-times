#!/usr/bin/env python3
"""
Electronアプリ分類モジュール

Electronアプリを検出した際に、ウィンドウタイトルや
その他の情報から具体的なアプリの種類を判定する
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ElectronAppPattern:
    """Electronアプリのマッチングパターン"""

    name: str  # 表示名（例: "VSCode"）
    title_patterns: list[str]  # ウィンドウタイトルにマッチする正規表現パターン
    owner_names: list[str]  # kCGWindowOwnerNameにマッチする名前（小文字）


# 既知のElectronアプリのパターン定義
ELECTRON_APP_PATTERNS: list[ElectronAppPattern] = [
    ElectronAppPattern(
        name="VSCode",
        title_patterns=[
            r"Visual Studio Code",
            r"\.vscode",
            r" - .+ - Visual Studio Code$",
            r"^\[.*\] .*\.(py|ts|js|tsx|jsx|md|json|yaml|yml|go|rs|java|cpp|c|h)",
        ],
        owner_names=["code", "code - insiders"],
    ),
    ElectronAppPattern(
        name="Cursor",
        title_patterns=[
            r"Cursor",
            r" - Cursor$",
        ],
        owner_names=["cursor"],
    ),
    ElectronAppPattern(
        name="Slack",
        title_patterns=[
            r"Slack \|",
            r"^\| .+ \| Slack$",
            r"^Slack$",
        ],
        owner_names=["slack"],
    ),
    ElectronAppPattern(
        name="Discord",
        title_patterns=[
            r"Discord",
            r"^#.+ - Discord$",
        ],
        owner_names=["discord"],
    ),
    ElectronAppPattern(
        name="Notion",
        title_patterns=[
            r"Notion",
            r" - Notion$",
        ],
        owner_names=["notion"],
    ),
    ElectronAppPattern(
        name="Obsidian",
        title_patterns=[
            r"Obsidian",
            r" - Obsidian$",
        ],
        owner_names=["obsidian"],
    ),
    ElectronAppPattern(
        name="Figma",
        title_patterns=[
            r"Figma",
            r" – Figma$",
        ],
        owner_names=["figma"],
    ),
    ElectronAppPattern(
        name="Microsoft Teams",
        title_patterns=[
            r"Microsoft Teams",
            r"Teams",
        ],
        owner_names=["microsoft teams", "teams"],
    ),
    ElectronAppPattern(
        name="Postman",
        title_patterns=[
            r"Postman",
        ],
        owner_names=["postman"],
    ),
    ElectronAppPattern(
        name="1Password",
        title_patterns=[
            r"1Password",
        ],
        owner_names=["1password"],
    ),
    ElectronAppPattern(
        name="GitHub Desktop",
        title_patterns=[
            r"GitHub Desktop",
        ],
        owner_names=["github desktop"],
    ),
    ElectronAppPattern(
        name="Insomnia",
        title_patterns=[
            r"Insomnia",
        ],
        owner_names=["insomnia"],
    ),
    ElectronAppPattern(
        name="Linear",
        title_patterns=[
            r"Linear",
        ],
        owner_names=["linear"],
    ),
    ElectronAppPattern(
        name="Todoist",
        title_patterns=[
            r"Todoist",
        ],
        owner_names=["todoist"],
    ),
    ElectronAppPattern(
        name="Bitwarden",
        title_patterns=[
            r"Bitwarden",
        ],
        owner_names=["bitwarden"],
    ),
]


def classify_electron_app(
    window_title: Optional[str] = None,
    owner_name: Optional[str] = None,
    app_name: Optional[str] = None,
) -> str:
    """
    Electronアプリを分類する

    ウィンドウタイトル、ウィンドウオーナー名、アプリ名から
    具体的なElectronアプリの種類を判定する。

    Args:
        window_title: ウィンドウタイトル（kCGWindowName）
        owner_name: ウィンドウオーナー名（kCGWindowOwnerName）
        app_name: AppleScriptで取得したアプリ名

    Returns:
        判定されたアプリ名。判定できない場合は "VSCode" をデフォルトとして返す。
    """
    # オーナー名での判定（高精度）
    if owner_name:
        normalized_owner = owner_name.lower().strip()
        for pattern in ELECTRON_APP_PATTERNS:
            if normalized_owner in pattern.owner_names:
                return pattern.name

    # アプリ名での判定
    if app_name:
        normalized_app = app_name.lower().strip()
        for pattern in ELECTRON_APP_PATTERNS:
            if normalized_app in pattern.owner_names:
                return pattern.name

    # ウィンドウタイトルでの判定
    if window_title:
        for pattern in ELECTRON_APP_PATTERNS:
            for title_pattern in pattern.title_patterns:
                if re.search(title_pattern, window_title, re.IGNORECASE):
                    return pattern.name

    # デフォルトはVSCode（ユーザーの指示に基づく）
    return "VSCode"


def is_electron_app(owner_name: Optional[str] = None, app_name: Optional[str] = None) -> bool:
    """
    Electronアプリかどうかを判定する

    Args:
        owner_name: ウィンドウオーナー名（kCGWindowOwnerName）
        app_name: AppleScriptで取得したアプリ名

    Returns:
        Electronアプリの場合はTrue
    """
    electron_indicators = ["electron", "helper"]

    if owner_name:
        normalized = owner_name.lower()
        if "electron" in normalized:
            return True

    if app_name:
        normalized = app_name.lower()
        if "electron" in normalized:
            return True

    return False
