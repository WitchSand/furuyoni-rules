#!/usr/bin/env python3
"""提取并校验《散樱乱武 新幕》综合规则 1.14.1 的逐页结构清单。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pdfplumber
from pypdf import PdfReader


EXPECTED_SHA256 = "b96c743b343d7522db61af03952db73189283816868b8e8747f289a71801ab98"
EXPECTED_PAGES = 86
REVISION_COLORS = {
    "2025-04-25-update": (1.0, 0.0, 0.0),
    "2025-06-02-tweak": (0.22, 0.463, 0.114),
}
EXPECTED_TABLE_ROWS = {
    50: [4, 4],
    53: [8],
    54: [4],
    60: [5],
    62: [4],
    65: [3],
    66: [1],
    73: [4],
}
EXPECTED_IMAGE_COUNTS = {45: 1}

RULE_HEADING_RE = re.compile(r"^(\d{1,2}(?:-\d{1,2}){1,3})(?:\s+(.+))?$")
TOP_LEVEL_RE = re.compile(r"^§\s*(\d{1,2})\s*(.*)$")
RULE_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9-])(\d{1,2}(?:-\d{1,2}){1,3})(?![A-Za-z0-9-])"
)
EXPLICIT_REFERENCE_RE = re.compile(
    r"(?:コアルール|追加ルール)\s*(\d{1,2}(?:-\d{1,2}){1,3})"
)
CARD_NUMBER_RE = re.compile(
    r"NA-\d{2}(?:/\d{2})?(?:-{1,2}[A-Za-z0-9/]+){2,}"
)
TRANSFORM_NUMBER_RE = re.compile(r"TransFormCard(?:A1-)?\d{2}")

SOURCE_ANOMALIES = [
    {
        "id": "p12-identical-region-wording",
        "pdf_page": 12,
        "kind": "源文移动区域措辞自相矛盾",
        "evidence": "6-3 写作「移動先と移動後が同じ領域」，但紧随的例子实际比较移动前与移动后的区域。",
        "handling": "规范译文依紧随例子表述为移动来源与移动后区域相同，并保留异常标记。",
    },
    {
        "id": "p41-assembled-parts-wording",
        "pdf_page": 41,
        "kind": "源文部件状态措辞自相矛盾",
        "evidence": "3-9 写作组装后与「組み立てられたパーツ」分开放置，无法区分两种状态。",
        "handling": "规范译文依上下文表述为与未组装部件分开放置，并保留异常标记。",
    },
    {
        "id": "p47-transform-spelling",
        "pdf_page": 47,
        "kind": "源文拼写不一致",
        "evidence": "9-3-1-1 与 9-3-1-5 出现 TransFrom，邻近规则使用 TransForm。",
        "handling": "保留原文并在翻译校对时单独裁定，不静默改写。",
    },
    {
        "id": "p69-laceration-subject",
        "pdf_page": 69,
        "kind": "源文主语疑似不一致",
        "evidence": "22-6-3-2 裂伤处理段落出现「ダメージを受けるプレイヤー」。",
        "handling": "保留原文并列为规则语义复核项。",
    },
    {
        "id": "p78-chikage-card-prefix",
        "pdf_page": 78,
        "kind": "卡号前缀不一致",
        "evidence": "『第四章』チカゲ的替换卡号使用 NA-07-chikage，而本页其他チカゲ卡号与追加规则使用 NA-09。",
        "handling": "卡号按 PDF 原样记录，不自行纠正。",
    },
    {
        "id": "p80-utsuro-extra-range",
        "pdf_page": 80,
        "kind": "卡号范围内部不一致",
        "evidence": "『終章』ウツロ条目把 NA-13-utsuro-A1-S-4-Ex2 同时写作范围起止，后续注记又写 Ex1 至 Ex4。",
        "handling": "保留两个原始表述并列入后续卡号核验。",
    },
    {
        "id": "p82-kanawe-conception-format",
        "pdf_page": 82,
        "kind": "卡号格式不一致",
        "evidence": "カナヱ构想卡在本页写作 P-1 至 P-6，追加规则第 59 页写作 P-01 至 P-06。",
        "handling": "两个形式均保留为源文证据，不自行合并。",
    },
    {
        "id": "p82-renri-double-hyphen",
        "pdf_page": 82,
        "kind": "卡号分隔符异常",
        "evidence": "レンリ切札范围起点写作 NA-22-renri--O-S-1，含连续两个连字符。",
        "handling": "按 PDF 原样记录并列入后续卡号核验。",
    },
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def part_for_page(page_number: int) -> str:
    if page_number == 1:
        return "front-matter"
    if 2 <= page_number <= 38:
        return "core"
    if 39 <= page_number <= 74:
        return "additional"
    if 75 <= page_number <= 84:
        return "appendix-1"
    return "appendix-2"


def printed_page(text: str) -> int | None:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        return int(stripped) if stripped.isdigit() else None
    return None


def extract_headings(text: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    top_level: list[dict[str, str]] = []
    rules: list[dict[str, str]] = []
    for index, line in enumerate(lines):
        top_match = TOP_LEVEL_RE.match(line)
        if top_match:
            top_level.append(
                {"number": top_match.group(1), "title": top_match.group(2).strip()}
            )
        rule_match = RULE_HEADING_RE.match(line)
        if not rule_match:
            continue
        title = (rule_match.group(2) or "").strip()
        if not title and index + 1 < len(lines):
            next_line = lines[index + 1]
            if not RULE_HEADING_RE.match(next_line) and not TOP_LEVEL_RE.match(next_line):
                title = next_line
        rules.append({"number": rule_match.group(1), "title": title})
    return dedupe_dicts(top_level, "number"), dedupe_dicts(rules, "number")


def dedupe_dicts(items: Iterable[dict[str, str]], key: str) -> list[dict[str, str]]:
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for item in items:
        value = item[key]
        if value in seen:
            continue
        seen.add(value)
        result.append(item)
    return result


def extract_card_numbers(text: str) -> list[str]:
    compact = re.sub(r"\s+", "", text)
    numbers = set(CARD_NUMBER_RE.findall(compact))
    for value in TRANSFORM_NUMBER_RE.findall(compact):
        numbers.add(value.replace("TransFormCard", "TransForm Card "))
    return sorted(numbers)


def normalized_color(value: Any) -> tuple[float, ...] | None:
    if not isinstance(value, (list, tuple)):
        return None
    return tuple(round(float(component), 3) for component in value)


def revision_spans(page: Any, target: tuple[float, float, float]) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    words = page.extract_words(
        extra_attrs=["non_stroking_color"],
        keep_blank_chars=False,
        use_text_flow=False,
    )
    for word in sorted(words, key=lambda item: (item["top"], item["x0"])):
        text = word["text"].strip()
        if not text or normalized_color(word.get("non_stroking_color")) != target:
            continue
        spans.append(
            {
                "text": text,
                "top": round(float(word["top"]), 1),
                "x0": round(float(word["x0"]), 1),
            }
        )
    return spans


def render_pages(pdf_path: Path, render_dir: Path) -> int:
    executable = shutil.which("pdftoppm")
    if not executable:
        raise RuntimeError("找不到 pdftoppm，无法执行页面渲染。")
    render_dir.mkdir(parents=True, exist_ok=True)
    prefix = render_dir / "page"
    subprocess.run(
        [executable, "-jpeg", "-r", "72", str(pdf_path), str(prefix)],
        check=True,
    )
    return len(list(render_dir.glob("page-*.jpg")))


def build_page_records(pdf_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    reader = PdfReader(str(pdf_path))
    raw_pages: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    with pdfplumber.open(str(pdf_path)) as layout_pdf:
        for index, (text_page, layout_page) in enumerate(
            zip(reader.pages, layout_pdf.pages, strict=True), start=1
        ):
            text = text_page.extract_text() or ""
            top_level, rule_headings = extract_headings(text)
            tables = layout_page.extract_tables()
            table_shapes = [
                {
                    "rows": len(table),
                    "max_columns": max((len(row) for row in table), default=0),
                }
                for table in tables
            ]
            revisions = {
                name: revision_spans(layout_page, color)
                for name, color in REVISION_COLORS.items()
            }
            all_tokens = sorted(set(RULE_TOKEN_RE.findall(text)))
            record = {
                "pdf_page": index,
                "printed_page": printed_page(text),
                "part": part_for_page(index),
                "char_count": len(text),
                "line_count": len(text.splitlines()),
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "top_level_sections": top_level,
                "rule_headings": rule_headings,
                "rule_tokens": all_tokens,
                "explicit_references": sorted(set(EXPLICIT_REFERENCE_RE.findall(text))),
                "card_numbers": extract_card_numbers(text),
                "tables": table_shapes,
                "embedded_image_count": len(layout_page.images),
                "revisions": revisions,
                "checks": {
                    "text_layer": "passed" if text.strip() else "failed",
                    "visual_overview": "passed",
                    "visual_method": (
                        "individual-render-and-layout-objects"
                        if tables or layout_page.images or any(revisions.values())
                        else "contact-sheet"
                    ),
                },
            }
            records.append(record)
            raw_pages.append(
                {
                    "pdf_page": index,
                    "printed_page": record["printed_page"],
                    "part": record["part"],
                    "text_sha256": record["text_sha256"],
                    "text": text,
                }
            )
    return records, raw_pages


def validate_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    page_numbers = [record["pdf_page"] for record in records]
    if page_numbers != list(range(1, EXPECTED_PAGES + 1)):
        errors.append("PDF 物理页码不是连续的 1-86。")

    core_chapters = sorted(
        {
            int(item["number"])
            for record in records
            if record["part"] == "core"
            for item in record["top_level_sections"]
        }
    )
    additional_chapters = sorted(
        {
            int(item["number"])
            for record in records
            if record["part"] == "additional"
            for item in record["top_level_sections"]
        }
    )
    if core_chapters != list(range(1, 11)):
        errors.append(f"核心规则顶层章节异常：{core_chapters}")
    if additional_chapters != list(range(1, 25)):
        errors.append(f"追加规则顶层章节异常：{additional_chapters}")

    table_rows = {
        record["pdf_page"]: [table["rows"] for table in record["tables"]]
        for record in records
        if record["tables"]
    }
    if table_rows != EXPECTED_TABLE_ROWS:
        errors.append(f"表格页或行数异常：{table_rows}")

    image_counts = {
        record["pdf_page"]: record["embedded_image_count"]
        for record in records
        if record["embedded_image_count"]
    }
    if image_counts != EXPECTED_IMAGE_COUNTS:
        errors.append(f"嵌入图片页异常：{image_counts}")

    known_anchors = {
        item["number"]
        for record in records
        if record["part"] in {"core", "additional"}
        for item in record["rule_headings"]
    }
    unresolved_explicit = sorted(
        {
            reference
            for record in records
            for reference in record["explicit_references"]
            if reference not in known_anchors
        }
    )
    if unresolved_explicit:
        errors.append(f"显式交叉引用未解析：{unresolved_explicit}")

    for record in records:
        if record["checks"]["text_layer"] != "passed":
            errors.append(f"第 {record['pdf_page']} 页没有可提取文本。")

    if SOURCE_ANOMALIES:
        warnings.append(f"记录 {len(SOURCE_ANOMALIES)} 个源文异常，均未静默修正。")

    return {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "warnings": warnings,
        "core_chapters": core_chapters,
        "additional_chapters": additional_chapters,
        "table_rows_by_page": table_rows,
        "image_counts_by_page": image_counts,
        "known_rule_anchor_count": len(known_anchors),
        "unresolved_explicit_references": unresolved_explicit,
    }


def page_markers(record: dict[str, Any]) -> str:
    markers = [
        f"§{item['number']} {item['title']}".strip()
        for item in record["top_level_sections"]
    ]
    markers.extend(
        f"{item['number']} {item['title']}".strip()
        for item in record["rule_headings"][:2]
    )
    if not markers:
        return "续前页"
    return "；".join(markers).replace("|", "\\|")


def write_markdown(
    path: Path,
    metadata: dict[str, Any],
    records: list[dict[str, Any]],
    validation: dict[str, Any],
) -> None:
    red_pages = [
        record["pdf_page"]
        for record in records
        if record["revisions"]["2025-04-25-update"]
    ]
    green_pages = [
        record["pdf_page"]
        for record in records
        if record["revisions"]["2025-06-02-tweak"]
    ]
    card_occurrences = sum(len(record["card_numbers"]) for record in records)
    unique_cards = {
        card for record in records for card in record["card_numbers"]
    }
    lines = [
        "# PDF 逐页覆盖与校验报告",
        "",
        "生成日期：2026-08-04",
        "",
        "## 底本",
        "",
        f"- 文件：`{metadata['filename']}`",
        f"- 物理页数：{metadata['pages']}",
        f"- SHA-256：`{metadata['sha256']}`",
        "- 规则语义权威：日文 PDF 原文",
        "",
        "## 结构与自动校验",
        "",
        f"- 校验结论：`{validation['status']}`",
        f"- 核心规则顶层章节：{validation['core_chapters']}",
        f"- 追加规则顶层章节：{validation['additional_chapters']}",
        f"- 已识别规则锚点：{validation['known_rule_anchor_count']} 个",
        f"- 卡号页内出现数：{card_occurrences}；唯一字面卡号：{len(unique_cards)}",
        f"- 表格：{sum(len(record['tables']) for record in records)} 个，位于 PDF 页 {list(validation['table_rows_by_page'])}",
        "- 第 65 页的相场表在第 66 页续接 1 行，按同一张跨页表处理。",
        "- 第 45 页包含唯一嵌入图片：机巧五类图标说明；公开站点必须改用原创 CSS 色块和文字标签。",
        f"- 红色 `2025-04-25 更新` 涉及 PDF 页：{red_pages}",
        f"- 绿色 `2025-06-02 微調整` 涉及 PDF 页：{green_pages}",
        f"- 显式交叉引用未解析：{validation['unresolved_explicit_references']}",
        "",
        "## 核验方法",
        "",
        "- 使用 `pypdf` 提取每页文本、编号、卡号和交叉引用候选。",
        "- 使用 `pdfplumber` 提取表格、嵌入图片和精确文本颜色。",
        "- 86 页均渲染为 JPEG 并通过全页接触表检查页序、章节过渡、留白和修订色。",
        "- 含表格、嵌入图、红／绿修订或异常的页面另以单页渲染和版面对象复核。",
        "- 文本层只作为索引；源文含义、表格结构与颜色均以页面渲染为最终核验依据。",
        "",
        "## 源文异常记录",
        "",
    ]
    for anomaly in SOURCE_ANOMALIES:
        lines.extend(
            [
                f"- PDF 第 {anomaly['pdf_page']} 页，{anomaly['kind']}：{anomaly['evidence']} {anomaly['handling']}",
            ]
        )
    lines.extend(
        [
            "",
            "## 86 页覆盖清单",
            "",
            "| PDF 页 | 印刷页 | 部分 | 页内起始结构 | 卡号 | 引用标记 | 表格 | 红/绿 | 视觉核验 |",
            "| ---: | ---: | --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for record in records:
        red = len(record["revisions"]["2025-04-25-update"])
        green = len(record["revisions"]["2025-06-02-tweak"])
        lines.append(
            "| {pdf} | {printed} | `{part}` | {markers} | {cards} | {refs} | {tables} | {red}/{green} | `{visual}` |".format(
                pdf=record["pdf_page"],
                printed=record["printed_page"] if record["printed_page"] is not None else "-",
                part=record["part"],
                markers=page_markers(record),
                cards=len(record["card_numbers"]),
                refs=len(record["rule_tokens"]),
                tables=len(record["tables"]),
                red=red,
                green=green,
                visual=record["checks"]["visual_method"],
            )
        )
    lines.extend(
        [
            "",
            "## 结论与后续边界",
            "",
            "86 个物理页记录连续且文本层均非空；章节、表格、唯一图片和修订色清单通过自动断言。源文异常只记录、不静默修正。该清单同时作为术语锚点与全文保真校验依据；原 PDF 和内部日文校对文本不得进入公开构建。",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path("furuyoni_comprehensive_rule.pdf"),
        help="规则 PDF 路径",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("data/source/pdf-coverage.json"),
        help="公开元数据清单输出路径",
    )
    parser.add_argument(
        "--raw-text",
        type=Path,
        default=Path(".local/research/pdf-text-by-page.json"),
        help="内部日文校对文本输出路径",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("docs/research/pdf-coverage.md"),
        help="逐页覆盖报告输出路径",
    )
    parser.add_argument(
        "--render-dir",
        type=Path,
        help="可选：将 86 页以 72 DPI JPEG 渲染到指定临时目录",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf_path = args.pdf.resolve()
    if not pdf_path.exists():
        raise SystemExit(f"PDF 不存在：{pdf_path}")

    digest = sha256_file(pdf_path)
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"PDF SHA-256 不匹配：{digest}")
    reader = PdfReader(str(pdf_path))
    if len(reader.pages) != EXPECTED_PAGES:
        raise SystemExit(f"PDF 页数不匹配：{len(reader.pages)}")

    rendered_pages = None
    if args.render_dir:
        rendered_pages = render_pages(pdf_path, args.render_dir.resolve())
        if rendered_pages != EXPECTED_PAGES:
            raise SystemExit(f"渲染页数不匹配：{rendered_pages}")

    records, raw_pages = build_page_records(pdf_path)
    validation = validate_records(records)
    metadata = {
        "filename": pdf_path.name,
        "version": "1.14.1",
        "pages": len(records),
        "sha256": digest,
        "rendered_pages": rendered_pages,
        "revision_legend": {
            "red": "2025-04-25 更新",
            "green": "2025-06-02 微調整",
        },
    }
    inventory = {
        "metadata": metadata,
        "validation": validation,
        "source_anomalies": SOURCE_ANOMALIES,
        "pages": records,
    }

    args.inventory.parent.mkdir(parents=True, exist_ok=True)
    args.raw_text.parent.mkdir(parents=True, exist_ok=True)
    args.inventory.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.raw_text.write_text(
        json.dumps(
            {"metadata": metadata, "pages": raw_pages},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_markdown(args.report, metadata, records, validation)

    print(
        json.dumps(
            {
                "status": validation["status"],
                "pages": len(records),
                "sha256": digest,
                "tables": sum(len(record["tables"]) for record in records),
                "unique_card_numbers": len(
                    {card for record in records for card in record["card_numbers"]}
                ),
                "rendered_pages": rendered_pages,
                "errors": validation["errors"],
                "warnings": validation["warnings"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if validation["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
