#!/usr/bin/env python3
"""校验术语审核阶段的 PDF、来源与术语数据边界。"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "furuyoni_comprehensive_rule.pdf"
COVERAGE = ROOT / "data" / "source" / "pdf-coverage.json"
SOURCES = ROOT / "data" / "glossary" / "sources.json"
TERMS = ROOT / "data" / "glossary" / "terms.json"
SCHEMA = ROOT / "data" / "glossary" / "schema.json"
DECISION = ROOT / "data" / "glossary" / "decision-record.json"
REVIEW = ROOT / "docs" / "research" / "terminology-review.md"
EVIDENCE = ROOT / "docs" / "research" / "source-evidence.md"
CONTEXT = ROOT / "CONTEXT.md"
SIGNATURES = ROOT / "data" / "rules" / "source-numeric-signatures.json"

EXPECTED_HASH = "b96c743b343d7522db61af03952db73189283816868b8e8747f289a71801ab98"
ID_RE = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
ALLOWED_CATEGORIES = {
    "project_concept",
    "region_resource",
    "card_type",
    "effect_class",
    "phase_action",
    "rule_keyword",
    "goddess",
    "goddess_mechanism",
}
ALLOWED_PARTS = {"core", "additional", "appendix-1", "appendix-2"}
REQUIRED_TERM_IDS = {
    "zone.distance",
    "zone.life",
    "zone.aura",
    "zone.flare",
    "zone.dust",
    "zone.draw-pile",
    "zone.discard",
    "zone.covered",
    "zone.enchantment",
    "zone.hand",
    "zone.trump",
    "zone.extra",
    "zone.sealed",
    "zone.in-use",
    "zone.attack-in-progress",
    "zone.out-of-game",
    "effect.rule-based",
    "effect.constant",
    "effect.on-use",
    "effect.after-attack",
    "effect.on-deploy",
    "effect.while-deployed",
    "effect.on-discard",
    "effect.while-used",
    "state.unused",
    "state.in-use",
    "state.used",
    "state.flinched",
    "rule.impatience",
    "rule.situation-based",
    "rule.full-power-augmentation",
    "action.standard",
    "action.full-power",
}
EXPECTED_PRIMARY_ANCHORS = {
    "object.sakura-crystal": (12, "6-3"),
    "zone.dust": (15, "7-1-5"),
    "zone.in-use": (18, "7-1-14"),
    "zone.attack-in-progress": (18, "7-1-15"),
    "zone.out-of-game": (18, "7-1-16"),
    "card.deck": (6, "5-3"),
    "card.cost": (11, "6-2-1-12"),
    "card.capacity": (11, "6-2-1-11"),
    "attack.proper-range": (13, "6-4-1-3"),
    "effect.constant": (21, "9-1-1-2"),
    "phase.ending": (20, "8-3"),
    "state.unused": (12, "6-2-2-3"),
    "state.in-use": (12, "6-2-2-3"),
    "state.used": (12, "6-2-2-3"),
    "rule.owner": (6, "5-4"),
    "rule.situation-based": (6, "5-5"),
    "keyword.gap": (31, "10-6"),
    "keyword.terminal": (24, "9-2"),
    "keyword.unrespondable": (34, "10-22"),
    "keyword.unavoidable": (27, "9-4"),
    "keyword.recover": (31, "10-7"),
    "keyword.immediate-recover": (31, "10-8"),
    "keyword.arrow": (29, "10-1"),
    "keyword.range-expand-near": (30, "10-4-1"),
    "keyword.range-expand-far": (30, "10-4-2"),
    "keyword.range-shrink-near": (30, "10-4-3"),
    "keyword.range-shrink-far": (31, "10-4-4"),
    "resolution.cancel": (27, "9-4"),
    "action.seal": (31, "10-9"),
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for path in (PDF, COVERAGE, SOURCES, TERMS, SCHEMA, DECISION, CONTEXT, SIGNATURES):
        check(path.exists(), f"缺少必需文件：{path.relative_to(ROOT)}", errors)
    if errors:
        print("\n".join(f"ERROR {item}" for item in errors))
        return 1

    pdf_hash = hashlib.sha256(PDF.read_bytes()).hexdigest()
    check(pdf_hash == EXPECTED_HASH, f"PDF SHA-256 不匹配：{pdf_hash}", errors)

    coverage = load(COVERAGE)
    check(coverage.get("validation", {}).get("status") == "passed", "PDF 覆盖清单未通过", errors)
    check(coverage.get("metadata", {}).get("pages") == 86, "PDF 覆盖页数不是 86", errors)
    check(len(coverage.get("pages", [])) == 86, "PDF 覆盖记录不是 86 条", errors)
    check(
        coverage.get("metadata", {}).get("sha256") == EXPECTED_HASH,
        "PDF 覆盖清单哈希不匹配",
        errors,
    )
    coverage_pages = {item["pdf_page"]: item for item in coverage.get("pages", [])}
    signature_doc = load(SIGNATURES)
    check(signature_doc.get("source_sha256") == EXPECTED_HASH, "数值签名底本哈希不匹配", errors)
    check(len(signature_doc.get("pages", {})) == 86, "数值签名记录不是 86 页", errors)

    source_doc = load(SOURCES)
    source_items = source_doc.get("sources", [])
    source_ids = [item.get("id") for item in source_items]
    check(len(source_ids) == len(set(source_ids)), "来源 ID 重复", errors)
    check(source_doc.get("accessed_at") == "2026-08-04", "来源总访问日期不正确", errors)
    for item in source_items:
        prefix = f"来源 {item.get('id', '<missing>')}"
        for key in ("id", "title", "url", "accessed_at", "accessibility", "evidence_summary", "limitations"):
            check(bool(item.get(key)), f"{prefix} 缺少 {key}", errors)
        check(str(item.get("url", "")).startswith("https://"), f"{prefix} URL 不是 HTTPS", errors)
        check(item.get("accessed_at") == "2026-08-04", f"{prefix} 访问日期不正确", errors)
        check(item.get("evidence_level") in {0, 1, 2, 3, 4}, f"{prefix} 证据等级非法", errors)

    schema_doc = load(SCHEMA)
    status_enum = (
        schema_doc.get("properties", {})
        .get("terms", {})
        .get("items", {})
        .get("properties", {})
        .get("review_status", {})
        .get("enum", [])
    )
    check("locked" in status_enum, "术语数据模式未允许 locked 状态", errors)

    decision_record = load(DECISION)
    check(decision_record.get("schema_version") == 1, "术语确认记录版本不正确", errors)
    check(
        decision_record.get("decision_id") == "terminology-freeze-2026-08-04",
        "术语确认记录 ID 不正确",
        errors,
    )
    check(decision_record.get("confirmed_at") == "2026-08-04", "术语确认日期不正确", errors)
    check(
        decision_record.get("user_statement")
        == "接受审核文档全部 171 条推荐方案，包括 21 条 provisional 的当前推荐名。",
        "术语确认记录未保留用户原话",
        errors,
    )
    check(decision_record.get("baseline_commit") == "7738d71", "术语确认基线提交不正确", errors)
    check(decision_record.get("term_count") == 171, "术语确认记录总数不是 171", errors)
    check(
        decision_record.get("pre_lock_status_counts") == {"review": 150, "provisional": 21},
        "冻结前状态计数不是 review 150／provisional 21",
        errors,
    )
    check(decision_record.get("locked_count") == 171, "术语确认记录锁定数不是 171", errors)
    provisional_ids = set(decision_record.get("provisional_term_ids", []))
    check(len(provisional_ids) == 21, "术语确认记录中的原 provisional ID 不是 21 个", errors)

    term_doc = load(TERMS)
    check(term_doc.get("source_pdf_sha256") == EXPECTED_HASH, "术语数据 PDF 哈希不匹配", errors)
    term_items = term_doc.get("terms", [])
    check(len(term_items) == 171, f"术语条目不是 171：{len(term_items)}", errors)
    ids = [item.get("id") for item in term_items]
    check(len(ids) == len(set(ids)), "术语稳定 ID 重复", errors)
    missing_required = sorted(REQUIRED_TERM_IDS - set(ids))
    check(not missing_required, "缺少核心术语：" + "、".join(missing_required), errors)
    required_fields = {
        "id",
        "category",
        "recommended_zh",
        "ja",
        "aliases",
        "strict_definition",
        "plain_explanation",
        "anchors",
        "evidence",
        "confidence",
        "review_status",
        "impact",
        "conflict_note",
    }
    for item in term_items:
        term_id = item.get("id", "<missing>")
        prefix = f"术语 {term_id}"
        check(set(item) == required_fields, f"{prefix} 字段集合不完整或含未知字段", errors)
        check(bool(ID_RE.fullmatch(str(term_id))), f"{prefix} 稳定 ID 格式非法", errors)
        check(item.get("category") in ALLOWED_CATEGORIES, f"{prefix} 分类非法", errors)
        check(bool(item.get("recommended_zh")), f"{prefix} 缺少推荐简中", errors)
        check(bool(item.get("ja")), f"{prefix} 缺少日文原词", errors)
        check(isinstance(item.get("aliases"), list), f"{prefix} 别名不是数组", errors)
        check(bool(item.get("strict_definition")), f"{prefix} 缺少严格定义", errors)
        check(bool(item.get("plain_explanation")), f"{prefix} 缺少白话说明", errors)
        check(item.get("confidence") in {"high", "medium", "low"}, f"{prefix} 置信度非法", errors)
        check(item.get("review_status") == "locked", f"{prefix} 未按用户确认锁定", errors)
        check(item.get("impact") in {"high", "medium", "low"}, f"{prefix} 影响等级非法", errors)

        anchors = item.get("anchors", [])
        check(bool(anchors), f"{prefix} 没有规则锚点", errors)
        for location in anchors:
            check(location.get("part") in ALLOWED_PARTS, f"{prefix} 锚点部分非法", errors)
            page = location.get("pdf_page")
            check(isinstance(page, int) and 1 <= page <= 86, f"{prefix} PDF 页码非法", errors)
            check(bool(location.get("rule")), f"{prefix} 锚点缺少规则编号", errors)
            if isinstance(page, int) and page in coverage_pages:
                check(
                    coverage_pages[page].get("part") == location.get("part"),
                    f"{prefix} 锚点分部与 PDF 第 {page} 页不一致",
                    errors,
                )
                rule_match = re.match(r"^(\d+(?:-\d+)+)", str(location.get("rule", "")))
                if rule_match:
                    rule_number = rule_match.group(1)
                    page_rule_tokens = coverage_pages[page].get("rule_tokens", [])
                    check(
                        rule_number in page_rule_tokens
                        or any(token.startswith(rule_number + "-") for token in page_rule_tokens),
                        f"{prefix} 锚点 {rule_number} 未在 PDF 第 {page} 页检出",
                        errors,
                    )

        evidence = item.get("evidence", [])
        evidence_ids = [entry.get("source_id") for entry in evidence]
        check(bool(evidence_ids), f"{prefix} 没有来源证据", errors)
        check("pdf-1.14.1" in evidence_ids, f"{prefix} 未引用规则底本", errors)
        check(len(evidence_ids) == len(set(evidence_ids)), f"{prefix} 重复引用同一来源", errors)
        for source_id in evidence_ids:
            check(source_id in source_ids, f"{prefix} 引用未知来源 {source_id}", errors)

    term_map = {item["id"]: item for item in term_items}
    for term_id, (expected_page, expected_rule) in EXPECTED_PRIMARY_ANCHORS.items():
        if term_id not in term_map:
            continue
        actual = [
            (item["pdf_page"], str(item["rule"]).split("（", 1)[0].split(" ", 1)[0])
            for item in term_map[term_id]["anchors"]
        ]
        check(
            (expected_page, expected_rule) in actual,
            f"术语 {term_id} 的主锚点应为 PDF {expected_page} / {expected_rule}，实际为 {actual}",
            errors,
        )

    counts = Counter(item.get("category") for item in term_items)
    check(set(counts) == ALLOWED_CATEGORIES, "术语分类覆盖不完整", errors)
    check(counts["goddess"] == 30, f"女神条目应为 30，实际 {counts['goddess']}", errors)
    check(counts["goddess_mechanism"] >= 50, "女神机制条目不足 50", errors)
    status_counts = Counter(item.get("review_status") for item in term_items)
    check(status_counts == {"locked": 171}, f"术语锁定计数不正确：{dict(status_counts)}", errors)
    accepted_ids = decision_record.get("accepted_term_ids", [])
    check(len(accepted_ids) == 171, "确认记录的 accepted_term_ids 不是 171 条", errors)
    check(len(accepted_ids) == len(set(accepted_ids)), "确认记录的 accepted_term_ids 有重复", errors)
    check(set(accepted_ids) == set(ids), "确认记录与当前术语 ID 集合不一致", errors)
    check(provisional_ids <= set(ids), "确认记录含未知的原 provisional ID", errors)

    conflicted_ids = {
        item["id"] for item in term_items if item.get("conflict_note") or item["id"] in provisional_ids
    }
    decision_ids = {
        item["id"]
        for item in term_items
        if item.get("impact") == "high"
        and (item.get("conflict_note") or item["id"] in provisional_ids)
    }
    for path, label in ((REVIEW, "术语审核文档"), (EVIDENCE, "来源证据文档")):
        check(path.exists(), f"缺少{label}：{path.relative_to(ROOT)}", errors)
    if REVIEW.exists():
        review_text = REVIEW.read_text(encoding="utf-8")
        missing_all = sorted(term_id for term_id in ids if f"`{term_id}`" not in review_text)
        check(not missing_all, f"术语审核文档遗漏词条 ID：{', '.join(missing_all)}", errors)
        missing = sorted(term_id for term_id in conflicted_ids if f"`{term_id}`" not in review_text)
        check(not missing, f"术语审核文档遗漏冲突／暂定 ID：{', '.join(missing)}", errors)
        check(
            "接受审核文档全部 171 条推荐方案，包括 21 条 provisional 的当前推荐名。"
            in review_text,
            "术语审核文档未记录用户确认原话",
            errors,
        )
        decision_section = review_text.split("## 已确认的高影响裁决项", 1)[-1].split("## 重点建议摘要", 1)[0]
        missing_decisions = sorted(
            term_id for term_id in decision_ids if f"`{term_id}`" not in decision_section
        )
        check(
            not missing_decisions,
            f"高影响裁决表遗漏 ID：{', '.join(missing_decisions)}",
            errors,
        )
        check("`locked`：171" in review_text, "术语审核文档未写明 171 条 locked", errors)
    if EVIDENCE.exists():
        evidence_text = EVIDENCE.read_text(encoding="utf-8")
        for source_id in source_ids:
            check(f"`{source_id}`" in evidence_text, f"来源证据文档遗漏 {source_id}", errors)

    if CONTEXT.exists():
        context_text = CONTEXT.read_text(encoding="utf-8")
        context_term_count = len(re.findall(r"^\*\*.+\*\*（日文：.+）$", context_text, re.MULTILINE))
        check(context_term_count == 171, f"CONTEXT.md 术语块不是 171：{context_term_count}", errors)
        for category_label in (
            "项目与对局概念",
            "区域与资源",
            "卡牌分类与数值",
            "效果分类",
            "阶段与动作",
            "通用规则关键字与状态",
            "女神名",
            "女神专属机制",
        ):
            check(f"## {category_label}" in context_text, f"CONTEXT.md 遗漏分类：{category_label}", errors)
        missing_context_terms = [
            item["id"]
            for item in term_items
            if f"**{item['recommended_zh']}**（日文：{item['ja']}）" not in context_text
        ]
        check(
            not missing_context_terms,
            "CONTEXT.md 遗漏冻结术语：" + "、".join(missing_context_terms),
            errors,
        )

    duplicate_zh = [name for name, count in Counter(item["recommended_zh"] for item in term_items).items() if count > 1]
    if duplicate_zh:
        warnings.append("推荐简中重复（可能为有意复用）：" + "、".join(sorted(duplicate_zh)))

    result = {
        "status": "passed" if not errors else "failed",
        "pdf_pages": 86,
        "term_count": len(term_items),
        "category_counts": dict(sorted(counts.items())),
        "review_status_counts": dict(sorted(status_counts.items())),
        "source_count": len(source_items),
        "decision_record": "terminology-freeze-2026-08-04",
        "confirmed_provisional_count": len(provisional_ids),
        "high_impact_decision_count": len(decision_ids),
        "conflict_or_provisional_count": len(conflicted_ids),
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
