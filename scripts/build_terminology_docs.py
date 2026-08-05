#!/usr/bin/env python3
"""由术语与来源 JSON 生成完整审核文档。"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TERMS_PATH = ROOT / "data" / "glossary" / "terms.json"
SOURCES_PATH = ROOT / "data" / "glossary" / "sources.json"
DECISION_PATH = ROOT / "data" / "glossary" / "decision-record.json"
REVIEW_PATH = ROOT / "docs" / "research" / "terminology-review.md"
EVIDENCE_PATH = ROOT / "docs" / "research" / "source-evidence.md"

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

FREQUENT_CORE_CATEGORIES = {
    "project_concept",
    "region_resource",
    "card_type",
    "effect_class",
    "phase_action",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def evidence_reason(term: dict, source_map: dict[str, dict], was_provisional: bool) -> str:
    ids = [item["source_id"] for item in term["evidence"]]
    levels = [source_map[source_id]["evidence_level"] for source_id in ids]
    has_bilibili = any(source_id.startswith("bilibili-") for source_id in ids)
    has_fandom = any(source_id.startswith("fandom-") for source_id in ids)
    if "steam-radiant-duels-zh-hans" in ids:
        return "受认证与监修项目已采用；规则含义再由日文底本限定。"
    if has_bilibili and has_fandom:
        return "两个独立社区体系可交叉印证，且与日文规则定义相容。"
    if was_provisional:
        return "冻结前的简中证据不足；用户已知悉其直译、音译或单一社区工作名属性，并确认采用当前推荐名。"
    if 3 in levels:
        return "可确认社区实际用法，但证据尚未达到受监修层级。"
    if 4 in levels:
        return "旧译仅用于发现差异；推荐方案主要依据日文定义和简中消歧。"
    return "日文底本可确定规则含义；简中形式按透明、可检索原则提出。"


def build_source_doc(source_doc: dict) -> str:
    lines = [
        "# 术语来源证据记录",
        "",
        "访问日期：2026-08-04",
        "",
        "本文件只记录 `PLAN.md` 允许的证据体系。日文 PDF 决定规则语义；网络来源只用于判断简中推荐名、社区别名和冲突。任何单一旧民译均不作为权威。",
        "",
        "## 证据等级",
        "",
        "| 等级 | 使用边界 |",
        "| ---: | --- |",
    ]
    for level, description in source_doc["evidence_policy"].items():
        lines.append(f"| {escape(level)} | {escape(description)} |")
    lines.extend(["", "## 已核验来源", ""])
    for source in source_doc["sources"]:
        lines.extend(
            [
                f"### `{source['id']}` — {source['title']}",
                "",
                f"- 证据等级：{source['evidence_level']}",
                f"- URL：<{source['url']}>",
                f"- 访问日期：{source['accessed_at']}",
                f"- 可访问性：`{source['accessibility']}`",
                f"- 简短证据：{source['evidence_summary']}",
                f"- 使用限制：{source['limitations']}",
            ]
        )
        if source.get("related_urls"):
            lines.append("- 同组核验页：")
            lines.extend(f"  - <{url}>" for url in source["related_urls"])
        lines.append("")
    lines.extend(
        [
            "## 访问异常与处置",
            "",
            "- 半官方模拟器的索引快照可访问，但本次直接请求本地化资源超时；因此没有把未能复核的界面字符串写入术语依据。",
            "- Fandom FAQ 直接访问偶发错误，搜索索引快照可读取；记录为间歇可访问，并由 Bilibili 独立社区材料交叉核对通用词。",
            "- 女神 Wiki 只完整覆盖较早角色；第 19 至 26 柱女神名不得由该站外推。证据不足的名称在冻结前标为 `provisional`，现已按用户明确确认锁定当前推荐名。",
            "- 旧民译作者自述含机器翻译与个人理解；它只负责暴露差异，不负责裁决。",
            "",
        ]
    )
    return "\n".join(lines)


def build_review_doc(term_doc: dict, source_doc: dict, decision_record: dict) -> str:
    terms = term_doc["terms"]
    source_map = {item["id"]: item for item in source_doc["sources"]}
    provisional_ids = set(decision_record["provisional_term_ids"])
    status_counts = Counter(item["review_status"] for item in terms)
    confidence_counts = Counter(item["confidence"] for item in terms)
    category_counts = Counter(item["category"] for item in terms)
    decision_terms = [
        item
        for item in terms
        if item["impact"] == "high" and (item["conflict_note"] or item["id"] in provisional_ids)
    ]
    all_attention = [
        item for item in terms if item["conflict_note"] or item["id"] in provisional_ids
    ]
    frequent_core_terms = [
        item for item in terms if item["category"] in FREQUENT_CORE_CATEGORIES
    ]

    lines = [
        "# 《散樱乱武 新幕》综合规则 1.14.1 术语审核与冻结记录",
        "",
        "审核日期：2026-08-04",
        "",
        "## 关卡结论",
        "",
        "术语审核关卡已经通过。用户明确表示：“接受审核文档全部 171 条推荐方案，包括 21 条 provisional 的当前推荐名。”因此全部推荐简中已转为 `locked`，根目录 `CONTEXT.md` 已成为规范领域语言入口。原冲突、置信度和冻结前状态继续保留，便于追溯，不表示仍待裁决。",
        "",
        f"- 术语总数：{len(terms)}",
        f"- `locked`：{status_counts['locked']}",
        f"- 冻结前 `review`／`provisional`：{decision_record['pre_lock_status_counts']['review']}／{decision_record['pre_lock_status_counts']['provisional']}",
        f"- 高／中／低置信度：{confidence_counts['high']}／{confidence_counts['medium']}／{confidence_counts['low']}",
        f"- 高影响且有冲突或暂定：{len(decision_terms)}",
        "- 女神覆盖：26 个可选女神 + 4 个不可选但会作为使用者出现的女神",
        "- 专属机制覆盖：54 项",
        "",
        f"## 高频核心词总览（{len(frequent_core_terms)} 项）",
        "",
        "下列词会跨章节反复出现在规则正文、导航、检索或交互标签中。全部推荐名均已确认；冲突提示只保留冻结时的考据背景。",
        "",
        "| 稳定 ID | 推荐简中 | 日文原词 | 主要别名 | 影响／置信度 | 冲突或状态提示 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in frequent_core_terms:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{escape(item['id'])}`",
                    escape(item["recommended_zh"]),
                    escape(item["ja"]),
                    escape("、".join(item["aliases"]) or "—"),
                    f"{item['impact']} / {item['confidence']}",
                    escape(
                        "已确认采用推荐名；原冲突：" + item["conflict_note"]
                        if item["conflict_note"]
                        else (
                            "已确认采用当前推荐名；冻结前为 provisional。"
                            if item["id"] in provisional_ids
                            else "已确认；无已知冲突。"
                        )
                    ),
                ]
            )
            + " |"
        )

    lines.extend(
        [
        "",
        "## 已确认的高影响裁决项",
        "",
        "下表记录冻结前需要裁决的高影响项。用户已经批量接受全部推荐方案，替代名与风险仅作审计留痕。",
        "",
        "| 稳定 ID | 推荐简中 | 日文原词 | 主要别名／方案 | 推荐理由 | 冲突与风险 | 状态 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in decision_terms:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{escape(item['id'])}`",
                    escape(item["recommended_zh"]),
                    escape(item["ja"]),
                    escape("、".join(item["aliases"]) or "—"),
                    escape(evidence_reason(item, source_map, item["id"] in provisional_ids)),
                    escape(item["conflict_note"] or "冻结前证据等级不足；当前推荐名已获确认。"),
                    f"`{item['review_status']}` / {item['confidence']}",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## 重点建议摘要",
            "",
            "- 已确认采用受监修项目稳定使用的“散樱乱武、双掌缭乱、眼前构筑、樱花决斗、樱花结晶、距离、王牌”。",
            "- 已确认五个核心资源使用“距离／命／装／气／虚”；“距”等短标签及其他别名仅用于检索，不在规范正文混写。",
            "- 已确认采用“牌组”而非“卡组”；“卡组”保留为别名，以记录 Steam 页面存在的两种写法。",
            "- 已确认采用“通常牌／王牌”，日文“通常札／切札”仍可通过词条检索。",
            "- 已确认采用“开始阶段”，将社区常用“准备阶段”保留为别名。",
            "- 已确认采用“达人距离”，保留“达人距／达人间合／近身距离”为别名。",
            "- 已确认采用“攻击距离”对应 `適正距離`，把“适正距离／适当距离”保留为检索别名。",
            "- 已确认采用“纳”“装附”“重铸牌库”，其替代写法只保留为考据记录或检索别名。",
            "- 已确认 `状況起因` 为“状态触发处理”，`保有者` 为“所有者”。",
            "- 已确认第 19 至 26 柱当前推荐名，包括冻结前仅有暂定音译证据的卡姆伊、西斯伊、伊尼尔。",
            "",
            "## 已确认的原冲突与暂定项",
            "",
            "下表完整保留冻结前存在冲突说明或处于 `provisional` 的条目。全部当前推荐名均已确认，不再处于待审状态。",
            "",
            "| 稳定 ID | 推荐简中 | 日文 | 冲突说明 | 规则锚点 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in all_attention:
        anchors = "；".join(
            f"{location['part']} PDF {location['pdf_page']} / {location['rule']}"
            for location in item["anchors"]
        )
        lines.append(
            f"| `{escape(item['id'])}` | {escape(item['recommended_zh'])} | {escape(item['ja'])} | "
            f"{escape(item['conflict_note'] or '冻结前证据不足；当前推荐名已确认。')} | {escape(anchors)} |"
        )

    lines.extend(["", "## 完整术语审核表", ""])
    grouped: dict[str, list[dict]] = defaultdict(list)
    for term in terms:
        grouped[term["category"]].append(term)
    for category, label in CATEGORY_LABELS.items():
        lines.extend(
            [
                f"### {label}（{category_counts[category]} 项）",
                "",
                "| ID | 推荐简中／日文 | 社区别名 | 严格定义 | 白话说明 | 锚点 | 证据 | 影响／置信度／状态 |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for item in grouped[category]:
            anchors = "；".join(
                f"PDF {location['pdf_page']} {location['rule']}" for location in item["anchors"]
            )
            evidence = "、".join(f"`{entry['source_id']}`" for entry in item["evidence"])
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{escape(item['id'])}`",
                        f"{escape(item['recommended_zh'])}<br>{escape(item['ja'])}",
                        escape("、".join(item["aliases"]) or "—"),
                        escape(item["strict_definition"]),
                        escape(item["plain_explanation"]),
                        escape(anchors),
                        evidence,
                        f"{item['impact']} / {item['confidence']} / `{item['review_status']}`",
                    ]
                )
                + " |"
            )
        lines.append("")

    lines.extend(
        [
            "## 术语冻结后的明确入口",
            "",
            "1. `issues/05-lock-terms-and-context.md` 已完成，确认原文另存于 `data/glossary/decision-record.json`。",
            "2. 规范领域语言已生成到根目录 `CONTEXT.md`；全文翻译必须使用其中的冻结名称。",
            "3. 下一阶段从 `issues/06-full-rule-translation.md` 开始，完成 86 页全文翻译与双轮校对。",
            "4. 在全文翻译完成前，`issues/07-static-site-build.md` 仍不得开始。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    term_doc = load(TERMS_PATH)
    source_doc = load(SOURCES_PATH)
    decision_record = load(DECISION_PATH)
    REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(build_source_doc(source_doc), encoding="utf-8")
    REVIEW_PATH.write_text(
        build_review_doc(term_doc, source_doc, decision_record), encoding="utf-8"
    )
    print(f"generated {EVIDENCE_PATH.relative_to(ROOT)}")
    print(f"generated {REVIEW_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
