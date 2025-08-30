# test_gitignore_behavior.py
import textwrap
from pathlib import Path

import pytest

from mdtree import build_structure_tree, validate_and_convert_path


@pytest.fixture
def tmp_repo(tmp_path: Path):
    """
    疑似リポジトリを作るfixture:
    .obsidian配下はignore、ただし特定ファイルは再許可
    """
    # .gitignore 内容
    gi = textwrap.dedent(
        """
        .obsidian/**
        !.obsidian/
        !.obsidian/plugins/
        !.obsidian/plugins/obsidian-linter/
        !.obsidian/plugins/obsidian-linter/data.json
        """
    ).strip()
    (tmp_path / ".gitignore").write_text(gi)

    # ディレクトリとファイルを作る
    (tmp_path / "normal.txt").write_text("ok")
    (tmp_path / ".obsidian" / "plugins" / "obsidian-linter").mkdir(parents=True)
    (tmp_path / ".obsidian" / "plugins" / "obsidian-linter" / "data.json").write_text(
        "{}"
    )
    (tmp_path / ".obsidian" / "plugins" / "obsidian-linter" / "other.txt").write_text(
        "ignored"
    )
    (tmp_path / ".obsidian" / "something.txt").write_text("ignored")

    return tmp_path


def test_gitignore_unignore(tmp_repo: Path):
    path = validate_and_convert_path(tmp_repo)
    tree = build_structure_tree(path)

    # 出力を見やすくデバッグ
    print("\n--- TREE ---\n" + tree + "\n-------------")

    # 普通のファイルは見える
    assert "normal.txt" in tree

    # .obsidian/自体は枝として表示される（!解除されてる）
    assert ".obsidian" in tree

    # data.json は再許可されて見える
    assert "data.json" in tree

    # 他のignore対象は見えない
    assert "something.txt" not in tree
    assert "other.txt" not in tree
