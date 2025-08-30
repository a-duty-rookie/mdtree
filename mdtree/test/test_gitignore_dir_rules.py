# mdtree/test/test_gitignore_dir_rules.py
from pathlib import Path

import pytest

from mdtree import build_structure_tree, validate_and_convert_path


def _lines(s: str) -> str:
    return "\n".join(s.strip().splitlines())


@pytest.fixture
def tmpbase(tmp_path: Path) -> Path:
    # 共通：見やすくするための通常ファイル
    (tmp_path / "root.txt").write_text("ok")
    return tmp_path


def test_dir_trailing_slash_excludes_descendants(tmpbase: Path):
    """
    非否定の 'dir/' は「ディレクトリ本体 + その配下すべて」を除外する。
    """
    (tmpbase / ".cache").mkdir()
    (tmpbase / ".cache" / "a.txt").write_text("x")
    (tmpbase / ".cache" / "sub").mkdir()
    (tmpbase / ".cache" / "sub" / "b.txt").write_text("y")

    (tmpbase / ".gitignore").write_text(
        _lines("""
        .cache/
    """)
    )

    path = validate_and_convert_path(tmpbase)
    tree = build_structure_tree(path, apply_gitignore=True)

    assert ".cache" not in tree
    assert "a.txt" not in tree
    assert "sub" not in tree
    assert "b.txt" not in tree
    assert "root.txt" in tree


def test_unignore_dir_only_then_unignore_specific_file(tmpbase: Path):
    """
    否定の '!dir/' は「ディレクトリ本体だけ」を再許可。
    配下は別途 '!file' で明示的に再許可しない限り非表示のまま。
    """
    (tmpbase / ".secret").mkdir()
    (tmpbase / ".secret" / "keep.txt").write_text("keep")
    (tmpbase / ".secret" / "hide.txt").write_text("hide")

    (tmpbase / ".gitignore").write_text(
        _lines("""
        .secret/**
        !.secret/
        !.secret/keep.txt
    """)
    )

    path = validate_and_convert_path(tmpbase)
    tree = build_structure_tree(path, apply_gitignore=True)

    # 枝として .secret は見える
    assert ".secret" in tree
    # 明示的に復活させたファイルは見える
    assert "keep.txt" in tree
    # 復活指定していないファイルは非表示
    assert "hide.txt" not in tree
    # ルートの通常ファイルは見える
    assert "root.txt" in tree


def test_last_rule_wins_with_negation_and_re_exclude(tmpbase: Path):
    """
    .gitignore の原則: 最後にマッチしたルールが勝つ。
    ここでは一旦除外 → 再許可 → もう一度除外 を確認。
    """
    (tmpbase / "target.txt").write_text("t")

    (tmpbase / ".gitignore").write_text(
        _lines("""
        target.txt
        !target.txt
        target.txt
    """)
    )

    path = validate_and_convert_path(tmpbase)
    tree = build_structure_tree(path, apply_gitignore=True)

    # 最終行が除外なので、target.txt は出ない
    assert "target.txt" not in tree
    # 代わりに root.txt は出る（比較用）
    assert "root.txt" in tree
