# import os
from pathlib import Path
from typing import Union

# import click


def validate_and_convert_path(s: Union[str, Path]):
    if not isinstance(s, (str, Path)):
        raise ValueError(f"Invalid input type: {type(s)}. Expected str or Path.")
    p = Path(s) if isinstance(s, str) else s
    if not p.exists():
        raise ValueError("input path does not exist.")
    return p


def build_structure_tree(root_path, max_depth=None):

    ends = ["├── ", "└── "]
    extentions = ["|    ", "    "]
    res_list = [str(root_path)]

    def search_directories(path: Path, prefix="", depth=0):
        depth = depth + 1
        if max_depth is not None and depth > max_depth:
            return
        children = sorted(list(path.glob("*")))
        for i, child in enumerate(children):
            # その階層の探索終了フラグ
            is_last = i + 1 == len(children)
            # その階層の探索が終了したらtreeを閉じる
            end = ends[int(is_last)]
            # その階層の探索が終了したら次からパイプを描かない
            extention = extentions[int(is_last)]
            res_list.append(prefix + end + child.name)
            if child.is_dir():
                search_directories(child, prefix + extention, depth)

    search_directories(root_path)
    return "\n".join(res_list)


if __name__ == "__main__":
    s = "."
    p = validate_and_convert_path(s)

    import pathspec

    gitignore_path = p / ".gitignore"
    ignore_list = gitignore_path.read_text().splitlines()
    spec = pathspec.PathSpec.from_lines("gitwildmatch", ignore_list)
    for path in p.glob("*"):
        if not spec.match_file(path):
            print(str(path))
    # ignore_text =
    # spec =PathSpec().from_lines()

    # res = build_structure_tree(p, max_depth=2)
    # print(res)
