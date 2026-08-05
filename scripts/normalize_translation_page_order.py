#!/usr/bin/env python3
"""按 source-page 数字顺序检查或整理规范正文页块。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/rules/translation-manifest.json"
PAGE_BLOCK_RE = re.compile(
    r"(?P<block><!-- source-page: (?P<page>\d+); printed-page: (?:null|\d+); "
    r"part: [a-z0-9-]+ -->.*?<!-- /source-page -->\n?)",
    re.DOTALL,
)


def normalize(path: Path) -> tuple[str, bool]:
    text = path.read_text(encoding="utf-8")
    matches = list(PAGE_BLOCK_RE.finditer(text))
    if not matches:
        raise RuntimeError(f"{path.relative_to(ROOT)} 中没有 source-page 页块")
    prefix = text[: matches[0].start()]
    suffix = text[matches[-1].end() :]
    between = "".join(text[left.end() : right.start()] for left, right in zip(matches, matches[1:]))
    if between.strip():
        raise RuntimeError(f"{path.relative_to(ROOT)} 的页块之间存在未归属内容")
    numbered = [(int(match.group("page")), match.group("block").rstrip() + "\n") for match in matches]
    if len({page for page, _ in numbered}) != len(numbered):
        raise RuntimeError(f"{path.relative_to(ROOT)} 存在重复 source-page")
    ordered = sorted(numbered)
    rendered = prefix.rstrip() + "\n\n" + "\n".join(block.rstrip() for _, block in ordered) + "\n"
    if suffix.strip():
        rendered += "\n" + suffix.lstrip()
    return rendered, rendered != text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="写回排序结果；默认仅检查")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    changed: list[Path] = []
    for spec in manifest["content_files"]:
        path = ROOT / spec["path"]
        rendered, differs = normalize(path)
        if not differs:
            continue
        changed.append(path)
        if args.write:
            path.write_text(rendered, encoding="utf-8")
    if changed and not args.write:
        for path in changed:
            print(f"页块顺序待整理：{path.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if changed:
        print("已整理页块顺序：" + "、".join(str(path.relative_to(ROOT)) for path in changed))
    else:
        print("正文页块顺序正确")
    return 0


if __name__ == "__main__":
    sys.exit(main())
