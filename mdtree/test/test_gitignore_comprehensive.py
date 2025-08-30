# mdtree/test/test_gitignore_comprehensive.py
from __future__ import annotations

from pathlib import Path

import pytest

from mdtree import build_structure_tree, validate_and_convert_path


def write_gitignore(root: Path, text: str) -> None:
    root.joinpath(".gitignore").write_text(
        "\n".join([ln.rstrip() for ln in text.strip().splitlines()]) + "\n",
        encoding="utf-8",
    )


def _lines(tree: str) -> list[str]:
    return tree.splitlines()


def _appears_as_entry(tree: str, name: str) -> bool:
    # 行頭/枝記号つきの“エントリ表示”として出ているかを判定
    for ln in _lines(tree):
        s = ln.strip()
        if s == name:
            return True  # ルート名など
        if s.endswith(f"├── {name}") or s.endswith(f"└── {name}"):
            return True
    return False


def _appears_as_root_entry(tree: str, name: str) -> bool:
    for ln in _lines(tree):
        # ルート直下の行は接頭の枝がなく、"├── " / "└── " で始まる
        if ln.startswith(f"├── {name}") or ln.startswith(f"└── {name}"):
            return True
    return False


def present_root(tree: str, *names: str) -> None:
    for n in names:
        assert _appears_as_root_entry(tree, n), (
            f"expected to see root entry {n!r} in\n{tree}"
        )


def absent_root(tree: str, *names: str) -> None:
    for n in names:
        assert not _appears_as_root_entry(tree, n), (
            f"expected NOT to see root entry {n!r} in\n{tree}"
        )


def present(tree: str, *names: str) -> None:
    for n in names:
        assert _appears_as_entry(tree, n), f"expected to see entry {n!r} in\n{tree}"


def absent(tree: str, *names: str) -> None:
    for n in names:
        assert not _appears_as_entry(tree, n), (
            f"expected NOT to see entry {n!r} in\n{tree}"
        )


@pytest.fixture
def base(tmp_path: Path) -> Path:
    # 共通で使う最低限のディレクトリ構造
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('ok')")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "train.csv").write_text("id\n1\n")
    (tmp_path / "README.md").write_text("readme")
    return tmp_path


def test_apply_gitignore_false_ignores_nothing(base: Path):
    write_gitignore(base, "*.egg-info/")
    (base / "pkg.egg-info").mkdir()
    (base / "pkg.egg-info" / "PKG-INFO").write_text("x")
    p = validate_and_convert_path(base)
    out = build_structure_tree(p, apply_gitignore=False)
    present(out, "pkg.egg-info", "PKG-INFO")


def test_exclude_git_true_hides_git_even_without_gitignore(base: Path):
    (base / ".git").mkdir()
    (base / ".git" / "config").write_text("")
    p = validate_and_convert_path(base)
    out = build_structure_tree(p, exclude_git=True)
    absent(out, ".git", "config")


def test_exclude_git_false_keeps_git_dir(base: Path):
    (base / ".git").mkdir()
    (base / ".git" / "config").write_text("")
    p = validate_and_convert_path(base)
    out = build_structure_tree(p, exclude_git=False)
    present(out, ".git", "config")


def test_glob_directory_pattern_excludes_descendants(base: Path):
    (base / "foo.egg-info").mkdir()
    (base / "foo.egg-info" / "PKG-INFO").write_text("")
    write_gitignore(base, "*.egg-info/")
    out = build_structure_tree(base, apply_gitignore=True)
    absent(out, "foo.egg-info", "PKG-INFO")
    present(out, "src", "data", "README.md")


def test_trailing_slash_non_negation_excludes_dir_and_descendants(base: Path):
    (base / "build").mkdir()
    (base / "build" / "artifact.bin").write_text("")
    write_gitignore(base, "build/")
    out = build_structure_tree(base)
    absent(out, "build", "artifact.bin")


def test_negated_trailing_slash_only_unignores_dir_itself(base: Path):
    (base / "private").mkdir()
    (base / "private" / "visible.txt").write_text("yes")
    (base / "private" / "hidden.txt").write_text("no")
    write_gitignore(
        base,
        """
        private/**
        !private/
        !private/visible.txt
        """,
    )
    out = build_structure_tree(base)
    # ディレクトリは枝として見える
    present(out, "private")
    # 明示的に復活したファイルだけ見える
    present(out, "visible.txt")
    # 他は非表示
    absent(out, "hidden.txt")


def test_double_star_any_depth_then_unignore_specific_file(base: Path):
    (base / "logs").mkdir()
    (base / "logs" / "2025" / "07").mkdir(parents=True)
    (base / "logs" / "2025" / "07" / "x.log").write_text("x")
    (base / "logs" / "2025" / "07" / "keep.log").write_text("k")
    write_gitignore(
        base,
        """
        logs/**
        !logs/2025/07/keep.log
        """,
    )
    out = build_structure_tree(base)
    present(out, "logs")  # 枝復活（親ディレクトリ自体は復活しうる）
    present(out, "2025", "07", "keep.log")
    absent(out, "x.log")


def test_last_rule_wins_with_re_exclude(base: Path):
    (base / "toggle.txt").write_text("")
    write_gitignore(
        base,
        """
        toggle.txt
        !toggle.txt
        toggle.txt
        """,
    )
    out = build_structure_tree(base)
    absent(out, "toggle.txt")


def test_character_class_and_qmark_globs(base: Path):
    (base / "cacheA").mkdir()
    (base / "cacheB").mkdir()
    (base / "cacheA" / "a.tmp").write_text("x")
    (base / "cacheB" / "b.tmp").write_text("x")
    (base / "cacheC").mkdir()
    (base / "cacheC" / "c.tmp").write_text("x")
    write_gitignore(
        base,
        """
        cache[AB]/      # 末尾スラ: A,Bディレクトリ全除外
        *.tmp           # ルート配下の tmp ファイル
        ?EADME.md       # 'README.md' は該当しないはず
        """,
    )
    out = build_structure_tree(base)
    # ディレクトリ A,B 丸ごと消える
    absent(out, "cacheA", "cacheB", "a.tmp", "b.tmp")
    # cacheC は残るが .tmp は消える
    present(out, "cacheC")
    absent(out, "c.tmp")
    # '?' は1文字ワイルドカード → '?EADME.md' は 'README.md' にマッチして除外される
    absent(out, "README.md")


def test_leading_slash_root_anchored_pattern(base: Path):
    # ルート直下の dist/ は除外されるが、src/dist は除外しない（root-anchored を想定）
    (base / "dist").mkdir()
    (base / "dist" / "bundle.js").write_text("")
    (base / "src" / "dist").mkdir()
    (base / "src" / "dist" / "keep.js").write_text("")
    write_gitignore(
        base,
        """
        /dist/
        """,
    )
    out = build_structure_tree(base)
    # ルート直下 dist/ は消える
    absent_root(out, "dist")
    # ネストした src/dist は残す
    present(out, "src", "dist", "keep.js")


def test_ignore_list_is_merged_with_gitignore(base: Path):
    (base / "downloads").mkdir()
    (base / "downloads" / "a.bin").write_text("")
    (base / "eggs").mkdir()
    (base / "eggs" / "e.whl").write_text("")
    write_gitignore(base, "downloads/")
    out = build_structure_tree(base, ignore_list=["eggs/"])
    absent(out, "downloads", "a.bin", "eggs", "e.whl")


def test_parent_shown_when_child_unignored(base: Path):
    (base / ".obsidian" / "plugins" / "ok").mkdir(parents=True)
    (base / ".obsidian" / "plugins" / "ok" / "data.json").write_text("{}")
    (base / ".obsidian" / "plugins" / "ok" / "other.txt").write_text("x")
    write_gitignore(
        base,
        """
        .obsidian/**
        !.obsidian/
        !.obsidian/plugins/
        !.obsidian/plugins/ok/
        !.obsidian/plugins/ok/data.json
        """,
    )
    out = build_structure_tree(base)
    # 枝は辿れる
    present(out, ".obsidian", "plugins", "ok")
    # 明示復活のみ見える
    present(out, "data.json")
    absent(out, "other.txt")


def test_max_depth_respected_even_with_ignored_parents(base: Path):
    (base / ".mypy_cache").mkdir()
    (base / ".mypy_cache" / "cachefile").write_text("x")
    write_gitignore(base, ".mypy_cache/")
    out = build_structure_tree(base, max_depth=1)
    # depth=1 でも .mypy_cache が除外されていること（= そもそも出ない）
    absent(out, ".mypy_cache", "cachefile")
    # 既存のトップ階層は見える
    present(out, base.name.split("/")[-1])


def test_union_of_rules_handles_many_patterns(base: Path):
    # パッケージング系の典型パターンをまとめて
    for d in [
        ".Python",
        "build",
        "dist",
        "downloads",
        "eggs",
        ".eggs",
        "lib",
        "lib64",
        "sdist",
        "wheels",
        "share/python-wheels",
    ]:
        (base / d).mkdir(parents=True)
        (base / d / "marker").write_text("x")
    for f in ["MANIFEST", ".installed.cfg"]:
        (base / f).write_text("x")
    (base / "proj.egg-info").mkdir()
    (base / "proj.egg-info" / "PKG-INFO").write_text("x")

    write_gitignore(
        base,
        """
        .Python
        build/
        dist/
        downloads/
        eggs/
        .eggs/
        lib/
        lib64/
        sdist/
        wheels/
        share/python-wheels/
        *.egg-info/
        .installed.cfg
        *.egg
        MANIFEST
        """,
    )
    out = build_structure_tree(base)

    # 典型ビルド成果物が見えないこと
    absent(
        out,
        ".Python",
        "build",
        "dist",
        "downloads",
        "eggs",
        ".eggs",
        "lib",
        "lib64",
        "sdist",
        "wheels",
        "share",
        "python-wheels",
        "proj.egg-info",
        "PKG-INFO",
        ".installed.cfg",
        "MANIFEST",
    )
    # 既存のソース類は残る
    present(out, "src", "data", "README.md")
