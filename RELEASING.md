# Release Process

## Pre-release Checklist

リリース前に以下を確認：

- [ ] すべてのテストがパス（Ubuntu CI + macOS Build）
- [ ] `CHANGELOG.md` が更新されている
- [ ] `pyproject.toml` のバージョン番号が更新されている
- [ ] `README.md` が最新の状態
- [ ] TestPyPIでの動作確認済み

## Release Steps

### 1. バージョン番号の更新

```toml
# pyproject.toml
version = "0.1.0"  # 適切なバージョンに更新
```

### 2. CHANGELOGの更新

```bash
# CHANGELOG.mdに変更内容を記載
## [0.1.0] - 2025-12-28
### Added
- 新機能の説明
### Changed
- 変更内容の説明
### Fixed
- 修正内容の説明
```

### 3. コミット・プッシュ

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.1.0"
git push origin main
```

### 4. GitHubでリリース作成

1. https://github.com/koboriakira/screen-times/releases/new にアクセス
2. 「Choose a tag」で新しいタグを作成（例: `v0.1.0`）
3. リリースタイトル: `v0.1.0`
4. リリースノート: CHANGELOGの内容をコピー
5. 「Publish release」をクリック

### 5. 自動公開の確認

GitHub Releaseを作成すると、`.github/workflows/publish.yml` が自動的にトリガーされ、PyPIに公開されます。

- Actions タブで実行状況を確認
- PyPIページで公開を確認: https://pypi.org/project/screen-times/

## Post-release

リリース後の確認：

### 1. インストールテスト

```bash
# 仮想環境を作成
python -m venv test-env
source test-env/bin/activate  # macOS/Linux
# または
test-env\Scripts\activate  # Windows

# PyPIからインストール
pip install screen-times

# 動作確認
screenocr --help
screenocr status
```

### 2. ドキュメント確認

- PyPIページの表示確認: https://pypi.org/project/screen-times/
- READMEが正しく表示されているか
- メタデータ（author, license, classifiersなど）が正しいか

### 3. 次のバージョンへ

開発を再開する場合は、次のバージョンに更新：

```toml
# pyproject.toml
version = "0.1.1.dev0"  # 開発版として明示
```

## Manual Release (Alternative)

GitHub Releaseを使わず、手動でPyPIに公開する場合：

```bash
# 1. ビルド
python -m build

# 2. パッケージチェック
twine check dist/*

# 3. TestPyPIで確認（オプション）
twine upload --repository testpypi dist/*

# 4. 本番PyPIに公開
twine upload dist/*
```

## Troubleshooting

### ビルドエラー

```bash
# キャッシュをクリア
rm -rf dist/ build/ src/*.egg-info/
python -m build
```

### アップロードエラー

- APIトークンが正しく設定されているか確認
- 同じバージョンが既に存在していないか確認
- ネットワーク接続を確認

### バージョン重複エラー

PyPI（TestPyPI含む）では同じバージョンは1度しかアップロードできません：

```bash
# バージョンを上げてリトライ
# pyproject.toml の version を更新
python -m build
twine upload dist/*
```

## Security

- PyPI APIトークンは GitHub Secrets で管理
- トークンはプロジェクト単位で発行（全プロジェクトアクセス可能なトークンは使用しない）
- `.gitignore` に `dist/`, `build/`, `*.egg-info/` を追加済み
