#!/usr/bin/env python3
"""由全部冻结的术语数据生成仓库根目录 CONTEXT.md。"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TERMS_PATH = ROOT / "data" / "glossary" / "terms.json"
DECISION_PATH = ROOT / "data" / "glossary" / "decision-record.json"
OUTPUT = ROOT / "CONTEXT.md"

CATEGORY_LABELS = {
    "project_concept": "项目与对局概念",
    "region_resource": "区域与资源",
    "card_type": "卡牌分类与数值",
    "effect_class": "效果分类",
    "phase_action": "阶段与动作",
    "rule_keyword": "通用规则关键字与状态",
    "goddess": "女神名",
    "goddess_mechanism": "女神专属机制",
}


def main() -> None:
    document = json.loads(TERMS_PATH.read_text(encoding="utf-8"))
    decision_record = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
    expected_decisions = [
        "terminology-freeze-2026-08-04",
        "terminology-revision-2026-08-29",
    ]
    if document.get("applied_decision_ids") != expected_decisions:
        raise ValueError("术语数据未按顺序应用初始冻结与 2026-08-29 修订")
    if decision_record.get("applied_decision_ids") != expected_decisions:
        raise ValueError("术语决定记录与当前术语数据不一致")
    terms = document.get("terms", [])
    if len(terms) != 171:
        raise ValueError(f"CONTEXT.md 只允许从完整的 171 条术语生成，实际为 {len(terms)}")
    unlocked = [item["id"] for item in terms if item.get("review_status") != "locked"]
    if unlocked:
        raise ValueError("存在未冻结术语：" + "、".join(unlocked))

    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in terms:
        category = item.get("category")
        if category not in CATEGORY_LABELS:
            raise ValueError(f"未知术语分类：{category}")
        grouped[category].append(item)

    lines = [
        "# 《散樱乱武 新幕》综合规则简中语境",
        "",
        "本文件定义本项目唯一规范领域语言。全部 171 条术语于 2026-08-04 经用户确认并初始冻结，其中 6 条于 2026-08-29 根据用户填写意见明确修订；粗体为现行推荐名。规则正文只使用现行推荐名，日文原词用于对照，别名仅用于检索和释义。未经用户新的明确决定，不得改名、解锁或把别名混入规范正文。",
        "",
    ]

    for category, label in CATEGORY_LABELS.items():
        lines.extend([f"## {label}", ""])
        for item in grouped[category]:
            name = str(item["recommended_zh"])
            japanese = str(item["ja"])
            aliases = [str(alias) for alias in item.get("aliases", [])]
            if len(aliases) != len(set(aliases)):
                raise ValueError(f"{item['id']} 的别名存在重复")
            if name in aliases:
                raise ValueError(f"{item['id']} 的推荐名与别名重复")
            lines.extend(
                [
                    f"**{name}**（日文：{japanese}）",
                    "",
                    str(item["strict_definition"]),
                ]
            )
            if aliases:
                lines.extend(["", f"_避免混用_：{'、'.join(aliases)}。"])
            lines.append("")

    OUTPUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"generated {len(terms)} locked terms -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
