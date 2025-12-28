# Copilot向け指示書

リポジトリ情報: `koboriakira/screen-times`

## 開発ルール

- [AGENTS.md](../AGENTS.md)が存在すれば、これを参照すること
- PRのタイトルはConversional Commitの形式に従うこと
- mainブランチ上で開発することは避け、かならずmainブランチからfeatureブランチを切って作業すること
  - `<type>/<issue-number>-<short-description>` の形式でブランチ名をつけること
  - `<type>`もConversional Commitの形式に従うこと

## Pythonの開発について

- 仮想環境(`.venv`)を使うこと。なお`pipenv`で管理することを前提としている。
