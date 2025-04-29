import pytest

from mdtree import build_structure_tree, validate_and_convert_path


@pytest.fixture
def sample_dir(tmp_path):
    (tmp_path / "folder").mkdir()
    (tmp_path / "folder" / "file.txt").touch()
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").touch()
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "lib").touch()
    (tmp_path / "file_root.txt").touch()
    (tmp_path / ".mypy_cache").mkdir()
    (tmp_path / ".mypy_cache" / "cachefile").touch()
    (tmp_path / ".gitignore").write_text(".mypy_cache/\n.venv\n")
    return tmp_path


def test_tree_output():
    # カレントディレクトリを指定
    path = validate_and_convert_path(".")
    result = build_structure_tree(path, max_depth=1)
    assert isinstance(result, str)
    assert result.startswith(path.name)


def test_basic_output(sample_dir):
    path = validate_and_convert_path(sample_dir)
    result = build_structure_tree(path)
    assert isinstance(result, str)
    assert path.name in result
    assert "folder" in result
    assert "file_root.txt" in result
    assert not any(
        line.strip().endswith("/.git")
        or line.strip().endswith("├── .git")
        or line.strip().endswith("└── .git")
        for line in result.splitlines()
    )
    assert ".mypy_cache" not in result  # 追加


def test_max_depth_zero(sample_dir):
    path = validate_and_convert_path(sample_dir)
    result = build_structure_tree(path, max_depth=0)
    # ルートだけ出るか
    assert result.strip() == path.name


def test_max_depth_one(sample_dir):
    path = validate_and_convert_path(sample_dir)
    result = build_structure_tree(path, max_depth=1)
    assert "folder" in result
    assert "file.txt" not in result  # folder直下のfile.txtはdepth=2だから出ない
    assert not any(
        line.strip().endswith("/.git")
        or line.strip().endswith("├── .git")
        or line.strip().endswith("└── .git")
        for line in result.splitlines()
    )


def test_ignore_nonexistent_pattern(sample_dir):
    path = validate_and_convert_path(sample_dir)
    result = build_structure_tree(path, ignore_list=["nonexistentpattern"])
    assert "folder" in result
    assert "file_root.txt" in result
    assert not any(
        line.strip().endswith("/.git")
        or line.strip().endswith("├── .git")
        or line.strip().endswith("└── .git")
        for line in result.splitlines()
    )


def test_ignore_wildcard_pattern(sample_dir):
    path = validate_and_convert_path(sample_dir)
    result = build_structure_tree(path, ignore_list=["*.txt"])
    assert "file_root.txt" not in result
    assert "file.txt" not in result


def test_apply_gitignore(sample_dir):
    path = validate_and_convert_path(sample_dir)
    result = build_structure_tree(path, apply_gitignore=True)
    assert ".mypy_cache" not in result


def test_exclude_git(sample_dir):
    path = validate_and_convert_path(sample_dir)
    result = build_structure_tree(path, exclude_git=True)
    assert not any(
        line.strip().endswith("/.git")
        or line.strip().endswith("├── .git")
        or line.strip().endswith("└── .git")
        for line in result.splitlines()
    )


def test_invalid_path():
    with pytest.raises(ValueError):
        validate_and_convert_path("/this/path/does/not/exist")
