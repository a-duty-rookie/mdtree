from pathlib import Path

import click
import pyperclip  # type: ignore

from mdtree.treebuilder import build_structure_tree, validate_and_convert_path


@click.command()
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    help="対象ディレクトリ。規定値は今の階層。",
)
@click.option("--max-depth", type=int, default=None, help="深掘りする最大階層を指定")
@click.option(
    "--ignore-list",
    type=str,
    multiple=True,
    default=None,
    help="除外したいパターン（gitignoreと同じ記法,複数指定OK）",
)
@click.option(
    "--apply-gitignore/--no-apply-gitignore",
    default=True,
    help="gitignoreと同じ除外を適用。既定で適用。",
)
@click.option(
    "--exclude-git/--no-exclude-git",
    default=True,
    help=".gitフォルダを除外。既定で適用。",
)
@click.option(
    "--clipboard/--no-clipboard",
    default=True,
    help="clipboardへコピー。既定で適用",
)
@click.option(
    "--savepath",
    type=click.Path(exists=False, dir_okay=False),
    default=None,
    help="textで書き出し",
)
def main(
    path,
    max_depth,
    ignore_list,
    apply_gitignore,
    exclude_git,
    clipboard,
    savepath,
):
    p = validate_and_convert_path(path)
    res = build_structure_tree(
        root_path=p,
        max_depth=max_depth,
        ignore_list=list(ignore_list),
        apply_gitignore=apply_gitignore,
        exclude_git=exclude_git,
    )
    print(res)
    if clipboard:
        pyperclip.copy(res)
    if savepath:
        sp = Path(savepath)
        sp.parent.mkdir(exist_ok=True, parents=True)
        sp.touch()
        text = "# structure_tree\n\n" + "``` plaintext\n" + res + "\n```\n"
        sp.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
