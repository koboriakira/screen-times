#!/usr/bin/env python3
"""
Electron分類モジュールのテスト
"""

import pytest

from screen_times.electron_classifier import (
    classify_electron_app,
    is_electron_app,
    ELECTRON_APP_PATTERNS,
)


class TestIsElectronApp:
    """is_electron_app関数のテスト"""

    def test_electron_in_owner_name(self):
        """オーナー名にElectronが含まれる場合"""
        assert is_electron_app(owner_name="Electron") is True
        assert is_electron_app(owner_name="electron") is True
        assert is_electron_app(owner_name="Electron Helper") is True

    def test_electron_in_app_name(self):
        """アプリ名にElectronが含まれる場合"""
        assert is_electron_app(app_name="Electron") is True
        assert is_electron_app(app_name="electron") is True

    def test_non_electron_app(self):
        """Electron以外のアプリ"""
        assert is_electron_app(owner_name="Safari") is False
        assert is_electron_app(app_name="Finder") is False
        assert is_electron_app(owner_name="Code", app_name="Code") is False

    def test_none_values(self):
        """値がNoneの場合"""
        assert is_electron_app(owner_name=None, app_name=None) is False


class TestClassifyElectronApp:
    """classify_electron_app関数のテスト"""

    def test_vscode_by_owner_name(self):
        """VSCodeをオーナー名で判定"""
        assert classify_electron_app(owner_name="Code") == "VSCode"
        assert classify_electron_app(owner_name="Code - Insiders") == "VSCode"

    def test_vscode_by_title(self):
        """VSCodeをウィンドウタイトルで判定"""
        assert classify_electron_app(window_title="app.py - myproject - Visual Studio Code") == "VSCode"
        assert classify_electron_app(window_title="Visual Studio Code") == "VSCode"

    def test_cursor_by_owner_name(self):
        """Cursorをオーナー名で判定"""
        assert classify_electron_app(owner_name="Cursor") == "Cursor"

    def test_cursor_by_title(self):
        """Cursorをウィンドウタイトルで判定"""
        assert classify_electron_app(window_title="main.py - project - Cursor") == "Cursor"

    def test_slack_by_owner_name(self):
        """Slackをオーナー名で判定"""
        assert classify_electron_app(owner_name="Slack") == "Slack"

    def test_slack_by_title(self):
        """Slackをウィンドウタイトルで判定"""
        assert classify_electron_app(window_title="Slack | general | MyWorkspace") == "Slack"

    def test_discord_by_owner_name(self):
        """Discordをオーナー名で判定"""
        assert classify_electron_app(owner_name="Discord") == "Discord"

    def test_discord_by_title(self):
        """Discordをウィンドウタイトルで判定"""
        assert classify_electron_app(window_title="#general - Discord") == "Discord"

    def test_notion_by_owner_name(self):
        """Notionをオーナー名で判定"""
        assert classify_electron_app(owner_name="Notion") == "Notion"

    def test_notion_by_title(self):
        """Notionをウィンドウタイトルで判定"""
        assert classify_electron_app(window_title="My Notes - Notion") == "Notion"

    def test_obsidian_by_owner_name(self):
        """Obsidianをオーナー名で判定"""
        assert classify_electron_app(owner_name="Obsidian") == "Obsidian"

    def test_figma_by_owner_name(self):
        """Figmaをオーナー名で判定"""
        assert classify_electron_app(owner_name="Figma") == "Figma"

    def test_teams_by_owner_name(self):
        """Microsoft Teamsをオーナー名で判定"""
        assert classify_electron_app(owner_name="Microsoft Teams") == "Microsoft Teams"

    def test_postman_by_owner_name(self):
        """Postmanをオーナー名で判定"""
        assert classify_electron_app(owner_name="Postman") == "Postman"

    def test_1password_by_owner_name(self):
        """1Passwordをオーナー名で判定"""
        assert classify_electron_app(owner_name="1Password") == "1Password"

    def test_github_desktop_by_owner_name(self):
        """GitHub Desktopをオーナー名で判定"""
        assert classify_electron_app(owner_name="GitHub Desktop") == "GitHub Desktop"

    def test_default_to_vscode(self):
        """判定できない場合はVSCodeにフォールバック"""
        assert classify_electron_app(owner_name="Electron") == "VSCode"
        assert classify_electron_app(owner_name="Unknown Electron App") == "VSCode"
        assert classify_electron_app() == "VSCode"

    def test_case_insensitive_owner_name(self):
        """オーナー名の大文字小文字を無視"""
        assert classify_electron_app(owner_name="SLACK") == "Slack"
        assert classify_electron_app(owner_name="discord") == "Discord"

    def test_priority_owner_over_title(self):
        """オーナー名がタイトルより優先される"""
        # Slackのオーナー名で、Discordっぽいタイトルでも、Slackと判定
        assert classify_electron_app(
            owner_name="Slack",
            window_title="#general - Discord"
        ) == "Slack"


class TestElectronAppPatterns:
    """パターン定義のテスト"""

    def test_patterns_have_required_fields(self):
        """全パターンが必須フィールドを持つ"""
        for pattern in ELECTRON_APP_PATTERNS:
            assert pattern.name, "name is required"
            assert isinstance(pattern.title_patterns, list), "title_patterns must be a list"
            assert isinstance(pattern.owner_names, list), "owner_names must be a list"
            assert len(pattern.owner_names) > 0, "owner_names must not be empty"

    def test_owner_names_are_lowercase(self):
        """オーナー名は小文字で定義されている"""
        for pattern in ELECTRON_APP_PATTERNS:
            for owner_name in pattern.owner_names:
                assert owner_name == owner_name.lower(), \
                    f"Owner name '{owner_name}' should be lowercase"
