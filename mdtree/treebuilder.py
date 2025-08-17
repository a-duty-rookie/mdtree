from pathlib import Path
from typing import Optional, Union

import pathspec


def validate_and_convert_path(s: Union[str, Path]):
    if not isinstance(s, (str, Path)):
        raise ValueError(f"Invalid input type: {type(s)}. Expected str or Path.")
    p = Path(s) if isinstance(s, str) else s
    if not p.exists():
        raise ValueError("input path does not exist.")
    return p


def check_ignore_child(child: Path, spec: pathspec.pathspec.PathSpec):
    # 除外対象のspecに対して判定->除外対象ならTrueを返す
    str_child = str(child) + "/" if child.is_dir() else str(child)
    return spec.match_file(str_child)


def build_structure_tree(
    root_path: Path,
    max_depth: Optional[int] = None,
    ignore_list: Optional[list] = None,
    apply_gitignore: bool = True,
    exclude_git: bool = True,
):
    # tree表示のための記号準備
    ends = ["├── ", "└── "]
    extentions = ["│    ", "    "]
    # rootディレクトリを格納した結果収集リスト
    res_list = [root_path.resolve().name]
    # ignoreリスト定義
    if ignore_list is None:
        ignore_list = list()
    # ignore_listにgitignoreを反映
    if apply_gitignore:
        gitignore_path = root_path / ".gitignore"
        if gitignore_path.exists():
            for target in gitignore_path.read_text().splitlines():
                ignore_list.append(target)
    # gitファイル除外
    if exclude_git:
        ignore_list.append(".git")
    # pathspecインスタンス作成
    ignore_spec = pathspec.PathSpec.from_lines("gitwildmatch", ignore_list)

    def search_directories(path: Path, prefix="", depth=0):
        # 再帰的な内部関数
        # 探索深さを進める。depthはroot(0)スタートなので、最初にまず1歩深みへ進む。
        depth = depth + 1
        # 設定した最深を超えたら再帰関数を終了する
        if max_depth is not None and depth > max_depth:
            return
        # 今いる深さにいる子パスを抽出
        children = sorted(list(path.glob("*")))
        # ignore判定のものを除外する
        children = [
            child for child in children if not check_ignore_child(child, ignore_spec)
        ]
        for i, child in enumerate(children):
            # その階層の探索終了フラグを設定
            is_last = i + 1 == len(children)
            # 今のchildでその階層の探索が終了する場合はtreeを閉じる記号
            end = ends[int(is_last)]
            # 今のchildの行をlistに追加
            res_list.append(prefix + end + child.name)
            # 今のchildでその階層の探索が終了するかどうかで、さらに深掘りするときに|を描くか決める
            extention = extentions[int(is_last)]
            if child.is_dir():
                # 子パスがディレクトリの場合はさらに深く潜る
                search_directories(child, prefix + extention, depth)

    # 再帰関数をrootから実行する
    search_directories(root_path)
    # 改行区切りで出力
    return "\n".join(res_list)


if __name__ == "__main__":
    s = "."
    p = validate_and_convert_path(s)

    res = build_structure_tree(p)
    print(res)
