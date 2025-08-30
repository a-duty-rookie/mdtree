# 先頭付近に追加
import os
from pathlib import Path
from typing import Optional, Set, Union

import pathspec


def validate_and_convert_path(s: Union[str, Path]) -> Path:
    if not isinstance(s, (str, Path)):
        raise ValueError(f"Invalid input type: {type(s)}. Expected str or Path.")
    p = Path(s) if isinstance(s, str) else s
    if not p.exists():
        raise ValueError("input path does not exist.")
    return p.resolve()


def _read_gitignore_lines(root: Path) -> list[str]:
    gi = root / ".gitignore"
    if not gi.exists():
        return []
    out: list[str] = []
    for raw in gi.read_text(encoding="utf-8").splitlines():
        # 1) 両端の空白を除去（← これが超重要。行頭インデントを殺す）
        line = raw.strip()
        # 2) 空行 / 先頭コメントはスキップ
        if not line or line.startswith("#"):
            continue
        # 3) インラインコメントを除去:
        #    「半角スペースに続く #」以降はコメントとみなす（'foo#bar' は壊さない）
        idx = line.find(" #")
        if idx != -1:
            line = line[:idx].rstrip()
            if not line:
                continue
        out.append(line)
    return out


def _compile_gitignore_rules(patterns: list[str]):
    """
    .gitignore の行順を保持したまま、各行を個別の PathSpec (gitwildmatch) にする。
    返り値: [(is_negation, spec, original_pattern), ...]
    """
    rules = []
    for pat in patterns:
        is_neg = pat.startswith("!")
        core = pat[1:] if is_neg else pat
        # 空はスキップ
        if not core:
            continue
        spec = pathspec.PathSpec.from_lines("gitwildmatch", [core])
        rules.append((is_neg, spec, pat))
    return rules


def _rel_for_match(root: Path, p: Path) -> list[str]:
    """
    ルート相対 POSIX パス。ディレクトリの場合は
    - 'dir' と 'dir/' の両方を返し、'foo/' パターンにも確実に届くようにする。
    """
    rel = p.relative_to(root).as_posix()
    if p.is_dir():
        return [rel, (rel + "/") if rel and not rel.endswith("/") else rel]
    return [rel]


def build_structure_tree(
    root_path: Path,
    max_depth: Optional[int] = None,
    ignore_list: Optional[list[str]] = None,
    apply_gitignore: bool = True,
    exclude_git: bool = True,
):
    root_path = root_path.resolve()

    # 1) ルール列の構築（順序が命）
    patterns: list[str] = []
    if apply_gitignore:
        patterns.extend(_read_gitignore_lines(root_path))
    if ignore_list:
        patterns.extend(ignore_list)
    if exclude_git:
        patterns.append(".git/")  # ディレクトリ専用パターン

    # 2) 行ごとに gitwildmatch としてコンパイル（順序保持）
    rules = _compile_gitignore_rules(patterns)

    # 3) 全探索（親が ignore でも子が ! で復活し得るため、ここでは枝刈りしない）
    all_paths: list[Path] = [root_path]
    stack: list[tuple[Path, int]] = [(root_path, 0)]
    while stack:
        cur, depth = stack.pop()
        for ch in sorted(cur.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            all_paths.append(ch)
            if ch.is_dir():
                stack.append((ch, depth + 1))

    # 4) 最終判定：行順に評価し、最後にマッチした状態を採用
    DEBUG = os.environ.get("MDTREE_DEBUG") == "1"

    def is_ignored(p: Path) -> bool:
        # デフォルトは「含める」
        state_ignore = False
        hits = []
        rel = p.relative_to(root_path).as_posix()
        # 祖先ディレクトリ（自身がdirなら自身も含む）の相対POSIXパス一覧
        ancestors = []
        cur = p if p.is_dir() else p.parent
        while cur and cur != root_path:
            ancestors.append(cur.relative_to(root_path).as_posix())
            cur = cur.parent
        for is_neg, spec, _pat in rules:
            core = _pat[1:] if _pat.startswith("!") else _pat

            # ---- 末尾 `/` を特別扱い ----
            if core.endswith("/"):
                # 非否定: パターンにマッチする任意の祖先ディレクトリ（自身がdirならそれ自身も）があれば
                # その配下すべてを除外とする。ワイルドカードを含むので spec を使って照合。
                if not is_neg:
                    matched_dir = False
                    # 自身がdirなら自身も候補に入れる
                    dir_candidates = ([rel] if p.is_dir() else []) + ancestors
                    for d in dir_candidates:
                        # 'xxx/' で照合（gitwildmatchは末尾スラ付きディレクトリを期待する）
                        if d and spec.match_file(d.rstrip("/") + "/"):
                            matched_dir = True
                            break
                    if matched_dir:
                        state_ignore = True
                        hits.append((_pat, rel, "EXCLUDE (dir pattern & descendants)"))
                else:
                    # 否定: ディレクトリ本体のみ再許可（配下は別途 ! 指定）
                    if p.is_dir() and spec.match_file(rel.rstrip("/") + "/"):
                        state_ignore = False
                        hits.append((_pat, rel, "INCLUDE (unignore dir)"))
                continue

            # ---- それ以外は pathspec の判定に任せる ----
            if spec.match_file(rel):
                state_ignore = not is_neg  # True=除外, False=含める
                hits.append(
                    (_pat, rel, "EXCLUDE" if not is_neg else "INCLUDE (unignore)")
                )
        if DEBUG:
            kind = "DIR " if p.is_dir() else "FILE"
            print(f"[{kind}] {p.relative_to(root_path).as_posix() or '.'}")
            if hits:
                for pat, rel, eff in hits:
                    print(f"   -> match: {pat!r} on {rel!r} => {eff}")
                print(f"   => FINAL: {'IGNORED' if state_ignore else 'INCLUDED'}")
            else:
                print("   -> no match")
        return state_ignore

    included: Set[Path] = set()
    for p in all_paths:
        if p == root_path:
            included.add(p)
            continue
        if not is_ignored(p):
            included.add(p)

    # 5) 含められたノードの親は強制復活（枝の連結）
    for p in list(included):
        cur = p
        while cur != root_path:
            cur = cur.parent
            included.add(cur)

    # 5.5) “空”ディレクトリ枝落とし（最終版）
    # 子孫に included が1つでもあれば残す。無い場合は「直下に実ファイルがあれば残す」。
    # 直下に“除外されたディレクトリ”しか無いときだけ落とす。
    children_by_parent: dict[Path, list[Path]] = {}
    for p in all_paths:
        if p == root_path:
            continue
        children_by_parent.setdefault(p.parent, []).append(p)

    def has_included_descendant(dir_path: Path) -> bool:
        for q in included:
            if q == dir_path:
                continue
            try:
                q.relative_to(dir_path)
                return True
            except Exception:
                pass
        return False

    pruned = set()
    for p in included:
        if p == root_path or not p.is_dir():
            pruned.add(p)
            continue
        if has_included_descendant(p):
            pruned.add(p)
            continue
        # included 子孫が無い → 直下に実ファイルがあるなら残す
        has_real_file_child = any(ch.is_file() for ch in children_by_parent.get(p, []))
        if has_real_file_child:
            pruned.add(p)
            continue
        # 直下に実ファイルが無く、直下に除外されたディレクトリがある（or 何も無い）→ 落とす
        # （直下のディレクトリが included に居ない = 除外されている とみなす）
        # 直下に何も無い（本当に空）場合も落とす
        pruned = pruned  # no-op; p は追加しない（= 落とす）
    included = pruned

    # 6) ツリー描画
    def list_children(path: Path) -> list[Path]:
        return [
            c
            for c in sorted(
                path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())
            )
            if c in included
        ]

    lines = [root_path.name]
    ends = ["├── ", "└── "]
    extents = ["│    ", "     "]

    def rec(path: Path, prefix: str = "", depth: int = 0):
        if max_depth is not None and depth >= max_depth:
            return
        kids = list_children(path)
        for i, ch in enumerate(kids):
            is_last = i == len(kids) - 1
            lines.append(prefix + ends[int(is_last)] + ch.name)
            if ch.is_dir():
                rec(ch, prefix + extents[int(is_last)], depth + 1)

    rec(root_path)
    return "\n".join(lines)


if __name__ == "__main__":
    p = validate_and_convert_path(".")
    print(build_structure_tree(p))
