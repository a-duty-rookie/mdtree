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
    out = []
    for raw in gi.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
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
        if max_depth is not None and depth >= max_depth:
            continue
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
        for is_neg, spec, _pat in rules:
            core = _pat[1:] if _pat.startswith("!") else _pat

            # ---- 末尾 `/` を特別扱い ----
            if core.endswith("/"):
                dir_pat = core.rstrip("/")
                if not is_neg:
                    # 非否定: ディレクトリ本体 と その配下すべて を除外
                    if rel == dir_pat or rel.startswith(dir_pat + "/"):
                        state_ignore = True
                        hits.append((_pat, rel, "EXCLUDE (dir and descendants)"))
                else:
                    # 否定: ディレクトリ本体だけを再許可（中身は別途 ! で）
                    if p.is_dir() and rel == dir_pat:
                        state_ignore = False
                        hits.append((_pat, rel, "INCLUDE (unignore dir)"))
                # 末尾 `/` ルールはここで完結（spec は使わない）
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
