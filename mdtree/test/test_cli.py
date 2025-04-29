# mdtree/test/test_cli.py

from click.testing import CliRunner

from mdtree.__main__ import main


def test_cli_minimal(tmp_path):
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file.txt").touch()

    runner = CliRunner()
    result = runner.invoke(
        main, ["--path", str(tmp_path), "--no-clipboard", "--savepath", ""]
    )  # 保存・コピーなし
    print(result.output)
    assert result.exit_code == 0
    assert "dir1" in result.output
    assert "file.txt" in result.output


def test_cli_ignore_list(tmp_path):
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "junk.js").touch()
    (tmp_path / "main.py").touch()

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--path",
            str(tmp_path),
            "--ignore-list",
            "node_modules",
            "--no-clipboard",
            "--savepath",
            "",
        ],
    )
    print(result.output)
    assert "node_modules" not in result.output
    assert "main.py" in result.output


def test_cli_savepath(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").touch()

    md_out = tmp_path / "output.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--path", str(tmp_path), "--savepath", str(md_out), "--no-clipboard"],
    )
    assert result.exit_code == 0
    assert md_out.exists()
    content = md_out.read_text()
    assert "structure_tree" in content
    assert "src" in content
