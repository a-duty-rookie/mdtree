# mdtree/test/test_gitignore_glob_dir.py
from pathlib import Path

from mdtree import build_structure_tree, validate_and_convert_path


def test_glob_dir_pattern_excludes_descendants(tmp_path: Path):
    (tmp_path / "pkg.egg-info").mkdir()
    (tmp_path / "pkg.egg-info" / "PKG-INFO").touch()
    (tmp_path / "normal.txt").touch()
    (tmp_path / ".gitignore").write_text("*.egg-info/\n")

    path = validate_and_convert_path(tmp_path)
    out = build_structure_tree(path, apply_gitignore=True)

    assert "pkg.egg-info" not in out
    assert "PKG-INFO" not in out
    assert "normal.txt" in out
