# mdtree

**See below for the English version.**

[Source code available on GitHub! 👥](https://github.com/a-duty-rookie/mdtree)

---

## 🔄 これは何？

`mdtree` は、指定したディレクトリ構造を、テキストベースのMarkdownファイルとして出力するCLIツールです。

「作ったディレクトリ構造をサクッと分かりやすく紹介したい」「プロジェクトの構成を手間なく見せたい」そんな時に使えます。

---

## 🔍 使い方

### インストール

```bash
pip install mdtree-py
```

### コマンド例

現在のディレクトリを観測：

```bash
mdtree
```

他のオプション例：

```bash
mdtree --path ./your_project --max-depth 2 --ignore-list ./mypy_cache --ignore-list .venv --no-clipboard --savepath structure.md
```

### 主なオプション

- `--path [PATH]` : 構造を取りたいディレクトリパス指定（default: `.`）
- `--max-depth [N]` : 探索する最大階層を指定
- `--ignore-list [PATTERN]` : 除外したいパターンを複数指定（gitignore形式）
- `--apply-gitignore / --no-apply-gitignore` : `.gitignore`設定に基づく除外を適用/適用しない（default: 適用する）
- `--exclude-git / --no-exclude-git` : `.git`ディレクトリを除外する/しない（default: 除外する）
- `--clipboard / --no-clipboard` : 出力をクリップボードにコピーする/しない（default: コピーする）
- `--savepath [FILE]` : Markdownファイルに書き出すパスを指定（encoding: utf-8, default: `None` 保存しない）
- `--help` : 使い方ヘルプを表示

---

## ✨ 便利機能

- `.gitignore`に基づいた除外も自動適用可能
- `.git`ディレクトリもデフォルトで除外
- クリップボードへ結果を即コピペ可能
- Markdownファイルへキレイに書き出し

---

## 🎉 実施例

例えばこのリポジトリのルートで以下のように実行すると・・・

``` bash
mdtree --savepath 好きなパス.md
```

こんな感じのコードブロックを持ったmdファイル`好きなパス.md`が生成されます。
また、コードブロック内のテキストがクリップボードに追加されます。

``` plaintext
mdtree
├── .gitignore
├── LICENSE
├── README.md
├── mdtree
│    ├── __init__.py
│    ├── __main__.py
│    ├── test
│    │    ├── test_cli.py
│    │    └── test_structure.py
│    └── treebuilder.py
├── mdtree_output.md
├── pyproject.toml
└── requirements.txt
```

---

## 💛 ライセンス

This project is licensed under the terms of the MIT license.

---

[Source code available on GitHub! 👥](https://github.com/a-duty-rookie/mdtree)

---

## 🔄 What is this?

`mdtree` is a CLI tool that outputs the structure of a specified directory as a text-based Markdown file.

It's perfect for situations where you want to quickly show your directory structure or easily explain the layout of your project.

---

## 🔍 How to use

### Installation

```bash
pip install mdtree-py
```

### Example command

Check the current directory structure:

```bash
mdtree
```

Other options:

```bash
mdtree --path ./your_project --max-depth 2 --ignore-list .mypy_cache --ignore-list .venv --no-clipboard --savepath structure.md
```

### Main options

- `--path [PATH]` : Specify the directory path to inspect (default: `.`)
- `--max-depth [N]` : Set the maximum depth for traversal
- `--ignore-list [PATTERN]` : Specify patterns to ignore (multiple allowed, gitignore format)
- `--apply-gitignore / --no-apply-gitignore` : Apply or ignore `.gitignore` settings (default: apply)
- `--exclude-git / --no-exclude-git` : Exclude or include the `.git` directory (default: exclude)
- `--clipboard / --no-clipboard` : Copy output to clipboard or not (default: copy)
- `--savepath [FILE]` : Path to save output as a Markdown file (encoding: utf-8, default: `None`)
- `--help` : Display help

---

## ✨ Features

- Automatically apply `.gitignore`-based exclusions
- Exclude `.git` directory by default
- Instantly copy results to clipboard
- Cleanly export results as a Markdown file

---

## 🎉 Example

For example, running the following command at the root of this repository:

```bash
mdtree --savepath path-you-like.md
```

Generates a Markdown file `path-you-like.md` containing a code block like this, and also copies the block to your clipboard:

```plaintext
mdtree
├── .gitignore
├── LICENSE
├── README.md
├── mdtree
|    ├── __init__.py
|    ├── __main__.py
|    ├── test
|    |    ├── test_cli.py
|    |    └── test_structure.py
|    └── treebuilder.py
├── mdtree_output.md
├── pyproject.toml
└── requirements.txt
```

---

## 💛 License

This project is licensed under the terms of the MIT license.
