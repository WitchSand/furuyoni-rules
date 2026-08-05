#!/usr/bin/env python3
"""校验 86 页简中正文、两轮校对记录和底本保真信息。"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "furuyoni_comprehensive_rule.pdf"
COVERAGE = ROOT / "data/source/pdf-coverage.json"
TERMS = ROOT / "data/glossary/terms.json"
MANIFEST = ROOT / "data/rules/translation-manifest.json"
EXPECTED_SHA256 = "b96c743b343d7522db61af03952db73189283816868b8e8747f289a71801ab98"
EXPECTED_PAGES = 86

PAGE_START_RE = re.compile(
    r"<!-- source-page: (?P<page>\d+); printed-page: (?P<printed>null|\d+); "
    r"part: (?P<part>[a-z0-9-]+) -->"
)
PAGE_END = "<!-- /source-page -->"
RULE_HEADING_RE = re.compile(r"^#{2,6}\s+(\d{1,2}(?:-\d{1,2}){1,3})(?:\s+|$)", re.MULTILINE)
TOP_LEVEL_HEADING_RE = re.compile(r"^#{2,6}\s+§(\d{1,2})(?:\s+|$)", re.MULTILINE)
RULE_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9-])(\d{1,2}(?:-\d{1,2}){1,3})(?![A-Za-z0-9-])"
)
CARD_NUMBER_RE = re.compile(r"NA-\d{2}(?:/\d{2})?(?:-{1,2}[A-Za-z0-9/]+){2,}")
TRANSFORM_NUMBER_RE = re.compile(r"TransForm\s+Card\s+(?:A1-)?\d{2}")
TRANSFORM_NUMBER_COMPACT_RE = re.compile(r"TransFormCard(?:A1-)?\d{2}")
TERM_MARKER_RE = re.compile(r"\[\[([^\]|]+)\|([a-z0-9._-]+)\]\]")
JAPANESE_SCRIPT_RE = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff]")
REVISION_RE = re.compile(r'data-revision="(2025-04-25-update|2025-06-02-tweak)"')
TABLE_DECL_RE = re.compile(r"<!-- table: rows=(\d+); columns=(\d+); id=([a-z0-9-]+) -->")
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
HTML_TAG_RE = re.compile(r"<[^>]+>")
REVISION_NOTE_RE = re.compile(r"[（(]2025-(?:04-25 更新|06-02 微調整)[）)]")
REVISION_SCOPE_LABEL_RE = re.compile(r"【2025-(?:04-25 更新|06-02 微調整)：[^】]+】")
REVISION_SPAN_RE = re.compile(
    r'<span data-revision="(?P<revision>2025-04-25-update|2025-06-02-tweak)">'
    r'(?P<body>.*?)</span>',
    re.DOTALL,
)
PLACEHOLDER_RE = re.compile(r"TODO|TBD|FIXME|待翻译|待译|未译|待确认|译者注", re.IGNORECASE)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_page_count(path: Path) -> int | None:
    try:
        result = subprocess.run(
            ["pdfinfo", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.MULTILINE)
    return int(match.group(1)) if match else None


def strip_markup(text: str) -> str:
    text = TERM_MARKER_RE.sub(lambda match: match.group(1), text)
    text = COMMENT_RE.sub("", text)
    text = HTML_TAG_RE.sub("", text)
    text = REVISION_NOTE_RE.sub("", text)
    text = REVISION_SCOPE_LABEL_RE.sub("", text)
    return text


def normalized_numeric_lexemes(text: str) -> Counter[str]:
    """提取正文中的全部阿拉伯数字词素，作为数值保真辅助校验。"""

    normalized = unicodedata.normalize("NFKC", strip_markup(text))
    normalized = re.sub(r"(?<=\d)[ \t]+(?=\d)", "", normalized)
    return Counter(re.findall(r"\d+", normalized))


def normalized_symbolic_lexemes(text: str) -> Counter[str]:
    """提取带符号数值、分数式伤害、范围和规则专用符号。"""

    normalized = unicodedata.normalize("NFKC", strip_markup(text))
    normalized = CARD_NUMBER_RE.sub("", normalized)
    normalized = TRANSFORM_NUMBER_RE.sub("", normalized)
    expressions: list[str] = []
    expressions.extend(re.findall(r"(?<![A-Za-z0-9])(?:[+-]?(?:\d+|[XY]))/(?:[+-]?(?:\d+|[XY]))", normalized))
    expressions.extend(re.findall(r"(?<![A-Za-z0-9])(?:[+-](?:\d+|[XY]))(?![A-Za-z0-9])", normalized))
    expressions.extend(re.findall(r"(?:\d+|[XY])~(?:\d+|[XY])", normalized))
    expressions.extend(re.findall(r"\{(?:\d+|[XY])/(?:\d+|[XY])\}", normalized))
    expressions.extend(re.findall(r"⇔", normalized))
    expressions.extend("quoted-hyphen" for _ in re.finditer(r"[“\"「]-[”\"」]", normalized))
    return Counter(expressions)


def normalized_card_lexemes(text: str) -> Counter[str]:
    """提取卡号及变形卡编号，并校验同页重复次数。"""

    compact = re.sub(r"\s+", "", unicodedata.normalize("NFKC", strip_markup(text)))
    cards = Counter(CARD_NUMBER_RE.findall(compact))
    cards.update(TRANSFORM_NUMBER_COMPACT_RE.findall(compact))
    return cards


def split_pages(path: Path, errors: list[str]) -> dict[int, dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    pages: dict[int, dict[str, Any]] = {}
    cursor = 0
    while True:
        start = PAGE_START_RE.search(text, cursor)
        if not start:
            break
        end = text.find(PAGE_END, start.end())
        if end < 0:
            errors.append(f"{path.relative_to(ROOT)}：第 {start.group('page')} 页缺少结束标记")
            break
        page = int(start.group("page"))
        if page in pages:
            errors.append(f"{path.relative_to(ROOT)}：第 {page} 页标记重复")
        pages[page] = {
            "printed_page": None if start.group("printed") == "null" else int(start.group("printed")),
            "part": start.group("part"),
            "body": text[start.end() : end].strip(),
            "path": path,
        }
        cursor = end + len(PAGE_END)
    return pages


def semantic_tables(body: str) -> list[tuple[int, int, str]]:
    """返回每个声明后紧随的 Markdown／HTML 表格的（行数、列数、ID）。"""

    tables: list[tuple[int, int, str]] = []
    lines = body.splitlines()
    for index, line in enumerate(lines):
        declaration = TABLE_DECL_RE.fullmatch(line.strip())
        if not declaration:
            continue
        following = lines[index + 1 :]
        first_index = next((offset for offset, value in enumerate(following) if value.strip()), None)
        if first_index is None:
            tables.append((0, 0, declaration.group(3)))
            continue
        if following[first_index].strip().startswith("<table"):
            html_lines: list[str] = []
            for candidate in following[first_index:]:
                html_lines.append(candidate)
                if "</table>" in candidate:
                    break
            html = "\n".join(html_lines)
            rows = re.findall(r"<tr(?:\s[^>]*)?>(.*?)</tr>", html, re.DOTALL)
            column_counts = [len(re.findall(r"<t[hd](?:\s[^>]*)?>", row)) for row in rows]
            tables.append((len(rows), max(column_counts, default=0), declaration.group(3)))
            continue

        table_lines: list[str] = []
        for candidate in following:
            stripped = candidate.strip()
            if not stripped:
                if table_lines:
                    break
                continue
            if not stripped.startswith("|"):
                break
            table_lines.append(stripped)
        semantic_lines = [
            candidate
            for candidate in table_lines
            if not re.fullmatch(r"\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?", candidate)
        ]
        columns = 0
        if semantic_lines:
            columns = len([cell for cell in semantic_lines[0].strip("|").split("|")])
        tables.append((len(semantic_lines), columns, declaration.group(3)))
    return tables


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    signature_card_occurrences = 0

    for path in (PDF, COVERAGE, TERMS, MANIFEST):
        if not path.exists():
            errors.append(f"缺少文件：{path.relative_to(ROOT)}")
    if errors:
        print("翻译阶段校验失败：")
        for error in errors:
            print(f"- {error}")
        return 1

    if sha256_file(PDF) != EXPECTED_SHA256:
        errors.append("底本 SHA-256 与任务锁定值不一致")
    page_count = pdf_page_count(PDF)
    if page_count is None:
        warnings.append("当前环境没有可用的 pdfinfo；已继续使用覆盖清单页数校验")
    elif page_count != EXPECTED_PAGES:
        errors.append(f"底本页数应为 {EXPECTED_PAGES}，实际为 {page_count}")

    coverage = load_json(COVERAGE)
    terms_data = load_json(TERMS)
    manifest = load_json(MANIFEST)
    if coverage.get("metadata", {}).get("sha256") != EXPECTED_SHA256:
        errors.append("覆盖清单中的底本哈希不一致")
    if coverage.get("metadata", {}).get("pages") != EXPECTED_PAGES:
        errors.append("覆盖清单中的页数不为 86")

    term_by_id = {term["id"]: term for term in terms_data.get("terms", [])}
    if len(term_by_id) != 171 or any(term.get("review_status") != "locked" for term in term_by_id.values()):
        errors.append("术语源必须恰有 171 条且全部为 locked")

    content_specs = manifest.get("content_files", [])
    if not content_specs:
        errors.append("翻译清单没有 content_files")
    pages: dict[int, dict[str, Any]] = {}
    for spec in content_specs:
        path = ROOT / spec.get("path", "")
        if not path.is_file():
            errors.append(f"缺少正文文件：{spec.get('path')}")
            continue
        source_text = path.read_text(encoding="utf-8")
        required_frontmatter = (
            "content_kind: normative-rule",
            "language: zh-Hans",
            'source_version: "1.14.1"',
            f"part: {spec.get('part')}",
        )
        for frontmatter_line in required_frontmatter:
            if frontmatter_line not in source_text[:500]:
                errors.append(f"{spec.get('path')}：规范正文 frontmatter 缺少 {frontmatter_line}")
        file_pages = split_pages(path, errors)
        page_range = spec.get("pdf_pages", [])
        if (
            not isinstance(page_range, list)
            or len(page_range) != 2
            or not all(isinstance(value, int) for value in page_range)
        ):
            errors.append(f"{spec.get('path')}：pdf_pages 必须是起止页码")
            expected_file_pages: list[int] = []
        else:
            expected_file_pages = list(range(page_range[0], page_range[1] + 1))
        if list(file_pages) != expected_file_pages:
            errors.append(
                f"{spec.get('path')}：页块顺序／范围应为 {expected_file_pages}，"
                f"实际为 {list(file_pages)}"
            )
        for page, record in file_pages.items():
            if page in pages:
                errors.append(f"第 {page} 页同时出现在多个正文文件")
            pages[page] = record

    expected_pages = set(range(1, EXPECTED_PAGES + 1))
    actual_pages = set(pages)
    missing_pages = sorted(expected_pages - actual_pages)
    extra_pages = sorted(actual_pages - expected_pages)
    if missing_pages:
        errors.append(f"正文缺少 PDF 页：{missing_pages}")
    if extra_pages:
        errors.append(f"正文出现范围外页：{extra_pages}")

    coverage_by_page = {record["pdf_page"]: record for record in coverage.get("pages", [])}
    all_term_ids: set[str] = set()
    actual_revision_pages: dict[str, set[int]] = {
        "2025-04-25-update": set(),
        "2025-06-02-tweak": set(),
    }
    actual_revision_segments: dict[str, Counter[int]] = {
        "2025-04-25-update": Counter(),
        "2025-06-02-tweak": Counter(),
    }
    table_ids: set[str] = set()

    for page in sorted(actual_pages & expected_pages):
        record = pages[page]
        source = coverage_by_page.get(page)
        if source is None:
            errors.append(f"覆盖清单缺少第 {page} 页")
            continue
        body = record["body"]
        if record["printed_page"] != source.get("printed_page"):
            errors.append(f"第 {page} 页印刷页码不一致")
        if record["part"] != source.get("part"):
            errors.append(f"第 {page} 页所属部分不一致")
        if len(strip_markup(body).strip()) < 40:
            errors.append(f"第 {page} 页正文过短，疑似未翻译完整")
        if JAPANESE_SCRIPT_RE.search(strip_markup(body)):
            errors.append(f"第 {page} 页公开中文正文含平假名或片假名")
        if PLACEHOLDER_RE.search(strip_markup(body)):
            errors.append(f"第 {page} 页公开中文正文含占位符或未决译注")
        if "<img" in body.lower() or re.search(r"!\[[^\]]*\]\(", body):
            errors.append(f"第 {page} 页规范正文不得直接嵌入图片")

        expected_headings = [item["number"] for item in source.get("rule_headings", [])]
        actual_headings = RULE_HEADING_RE.findall(body)
        if len(actual_headings) != len(set(actual_headings)):
            errors.append(f"第 {page} 页规则标题编号有重复：{actual_headings}")
        if sorted(actual_headings) != sorted(expected_headings):
            errors.append(
                f"第 {page} 页规则标题编号不一致：应为 {expected_headings}，实际为 {actual_headings}"
            )

        expected_top_level = [item["number"] for item in source.get("top_level_sections", [])]
        actual_top_level = TOP_LEVEL_HEADING_RE.findall(body)
        if actual_top_level != expected_top_level:
            errors.append(
                f"第 {page} 页顶层章节编号不一致：应为 {expected_top_level}，实际为 {actual_top_level}"
            )

        cardless = CARD_NUMBER_RE.sub("", body)
        cardless = TRANSFORM_NUMBER_RE.sub("", cardless)
        actual_tokens = sorted(set(RULE_TOKEN_RE.findall(cardless)))
        expected_tokens = sorted(source.get("rule_tokens", []))
        if actual_tokens != expected_tokens:
            errors.append(f"第 {page} 页编号／范围词元不一致：应为 {expected_tokens}，实际为 {actual_tokens}")

        actual_cards = sorted(set(CARD_NUMBER_RE.findall(body) + TRANSFORM_NUMBER_RE.findall(body)))
        expected_cards = sorted(source.get("card_numbers", []))
        if actual_cards != expected_cards:
            errors.append(f"第 {page} 页卡号不一致：应为 {expected_cards}，实际为 {actual_cards}")

        for reference in source.get("explicit_references", []):
            reference_re = re.compile(
                rf"(?:核心规则|追加规则)\s*[“”\"《〈]?\s*{re.escape(reference)}(?!\d)"
            )
            if not reference_re.search(strip_markup(body)):
                errors.append(f"第 {page} 页缺少显式交叉引用 {reference}")

        table_overrides = manifest.get("table_shape_overrides", {}).get(str(page))
        expected_tables = (
            [tuple(item) for item in table_overrides]
            if table_overrides is not None
            else [(item["rows"], item["max_columns"]) for item in source.get("tables", [])]
        )
        parsed_tables = semantic_tables(body)
        actual_tables = [(rows, columns) for rows, columns, _ in parsed_tables]
        if actual_tables != expected_tables:
            errors.append(f"第 {page} 页表格形状不一致：应为 {expected_tables}，实际为 {actual_tables}")
        for _, _, table_id in parsed_tables:
            if table_id in table_ids:
                errors.append(f"第 {page} 页表格 ID 重复：{table_id}")
            table_ids.add(table_id)
        for html_table in re.findall(r"<table(?:\s[^>]*)?>.*?</table>", body, re.DOTALL):
            if "<caption>" not in html_table:
                errors.append(f"第 {page} 页 HTML 表格缺少语义标题 caption")
            if re.search(r"<tr>\s*<td", html_table):
                errors.append(f"第 {page} 页 HTML 表格首列未使用行标题 th")

        source_revisions = source.get("revisions", {})
        for revision in actual_revision_pages:
            count = len(re.findall(rf'data-revision="{re.escape(revision)}"', body))
            if count:
                actual_revision_pages[revision].add(page)
                actual_revision_segments[revision][page] = count
            if bool(source_revisions.get(revision)) != bool(count):
                errors.append(f"第 {page} 页修订类别 {revision} 的有无与底本不一致")

        revision_openings = len(REVISION_RE.findall(body))
        revision_spans = list(REVISION_SPAN_RE.finditer(body))
        if revision_openings != len(revision_spans):
            errors.append(f"第 {page} 页修订标记存在未闭合或非 span 结构")
        for revision_span in revision_spans:
            revision = revision_span.group("revision")
            visible_body = revision_span.group("body")
            expected_label = "2025-04-25 更新" if revision == "2025-04-25-update" else "2025-06-02 微調整"
            if expected_label not in visible_body:
                errors.append(f"第 {page} 页修订标记 {revision} 缺少可见文字标签")

        for display, term_id in TERM_MARKER_RE.findall(body):
            term = term_by_id.get(term_id)
            if term is None:
                errors.append(f"第 {page} 页出现未知术语 ID：{term_id}")
                continue
            if term.get("review_status") != "locked":
                errors.append(f"第 {page} 页引用未锁定术语：{term_id}")
            if display != term.get("recommended_zh"):
                errors.append(
                    f"第 {page} 页术语 {term_id} 显示为“{display}”，应为“{term.get('recommended_zh')}”"
                )
            all_term_ids.add(term_id)

    term_policy = manifest.get("required_term_policy")
    terms_not_in_source = set(manifest.get("terms_not_in_normative_source", []))
    if term_policy == "all-locked-except-not-in-source":
        required_term_ids = set(term_by_id) - terms_not_in_source
    else:
        required_term_ids = set(manifest.get("required_term_ids", []))
    unknown_exclusions = sorted(terms_not_in_source - set(term_by_id))
    unknown_required = sorted(required_term_ids - set(term_by_id))
    missing_required = sorted(required_term_ids - all_term_ids)
    if unknown_exclusions:
        errors.append(f"清单中的底本未出现术语 ID 不存在：{unknown_exclusions}")
    if unknown_required:
        errors.append(f"清单中的必需术语 ID 不存在：{unknown_required}")
    if missing_required:
        errors.append(f"正文未标注底本中出现的规范术语：{missing_required}")

    full_normative_text = "\n".join(record["body"] for record in pages.values())
    for alias in manifest.get("forbidden_normative_aliases", []):
        if alias in strip_markup(full_normative_text):
            errors.append(f"规范正文出现冻结名以外的禁用别名：{alias}")

    expected_revision_segments = manifest.get("revision_segments", {})
    for revision, page_counts in expected_revision_segments.items():
        expected_counter = Counter({int(page): int(count) for page, count in page_counts.items()})
        if actual_revision_segments.get(revision, Counter()) != expected_counter:
            errors.append(
                f"{revision} 语义修订段计数不一致：应为 {dict(expected_counter)}，"
                f"实际为 {dict(actual_revision_segments.get(revision, Counter()))}"
            )

    coverage_anomalies = {
        anomaly.get("id"): anomaly.get("pdf_page")
        for anomaly in coverage.get("source_anomalies", [])
    }
    manifest_anomalies = {
        anomaly.get("id"): anomaly.get("pdf_page")
        for anomaly in manifest.get("source_anomalies", [])
    }
    if coverage_anomalies != manifest_anomalies:
        errors.append("PDF 覆盖清单与翻译清单的源文异常 ID／页码不一致")

    for anomaly in manifest.get("source_anomalies", []):
        page = int(anomaly["pdf_page"])
        body = pages.get(page, {}).get("body", "")
        marker = f"source-anomaly: {anomaly['id']}"
        if marker not in body:
            errors.append(f"第 {page} 页缺少源文异常标记 {anomaly['id']}")
        for literal in anomaly.get("required_literals", []):
            if literal not in body:
                errors.append(f"第 {page} 页源文异常 {anomaly['id']} 缺少原样字面量：{literal}")

    graphic = manifest.get("official_graphic_replacement", {})
    graphic_page = int(graphic.get("pdf_page", 0))
    graphic_body = pages.get(graphic_page, {}).get("body", "")
    if graphic and "original-graphic-replaced:" not in graphic_body:
        errors.append(f"第 {graphic_page} 页缺少官方图片的原创语义替代标记")
    for label in graphic.get("required_labels", []):
        if label not in graphic_body:
            errors.append(f"第 {graphic_page} 页原创图示缺少文字标签：{label}")

    signature_path = ROOT / manifest.get("source_signature_file", "")
    if not signature_path.is_file():
        errors.append("缺少底本数值与符号词素签名")
    else:
        signatures = load_json(signature_path)
        if signatures.get("source_sha256") != EXPECTED_SHA256:
            errors.append("底本数值与符号词素签名的哈希来源不一致")
        expected_absent_terms = {
            term_id: term_by_id[term_id]["ja"]
            for term_id in terms_not_in_source
            if term_id in term_by_id
        }
        if signatures.get("verified_absent_locked_terms") != expected_absent_terms:
            errors.append("底本未出现术语的可重复核验证据与翻译清单不一致")
        signature_pages = signatures.get("pages", {})
        signature_card_occurrences = sum(
            sum(int(count) for count in page_signature.get("cards", {}).values())
            for page_signature in signature_pages.values()
        )
        if set(map(int, signature_pages)) != expected_pages:
            errors.append("底本数值与符号词素签名必须覆盖 1 至 86 页")
        for page_text, expected in signature_pages.items():
            page = int(page_text)
            actual_numeric = normalized_numeric_lexemes(pages[page]["body"])
            expected_numeric = Counter(
                {str(token): int(count) for token, count in expected.get("numeric", {}).items()}
            )
            if actual_numeric != expected_numeric:
                errors.append(
                    f"第 {page} 页数值词素不一致：应为 {dict(expected_numeric)}，实际为 {dict(actual_numeric)}"
                )
            actual_symbolic = normalized_symbolic_lexemes(pages[page]["body"])
            expected_symbolic = Counter(
                {str(token): int(count) for token, count in expected.get("symbolic", {}).items()}
            )
            if actual_symbolic != expected_symbolic:
                errors.append(
                    f"第 {page} 页符号词素不一致：应为 {dict(expected_symbolic)}，实际为 {dict(actual_symbolic)}"
                )
            actual_card_lexemes = normalized_card_lexemes(pages[page]["body"])
            expected_card_lexemes = Counter(
                {str(token): int(count) for token, count in expected.get("cards", {}).items()}
            )
            if actual_card_lexemes != expected_card_lexemes:
                errors.append(
                    f"第 {page} 页卡号出现次数不一致：应为 {dict(expected_card_lexemes)}，"
                    f"实际为 {dict(actual_card_lexemes)}"
                )

    review_passes = {item.get("id"): item for item in manifest.get("review_passes", [])}
    for pass_id in ("semantic", "terminology-style"):
        review = review_passes.get(pass_id, {})
        if review.get("status") != "passed":
            errors.append(f"校对轮次 {pass_id} 尚未标记 passed")
        if review.get("reviewed_pages") != list(range(1, EXPECTED_PAGES + 1)):
            errors.append(f"校对轮次 {pass_id} 未逐页记录 1 至 86 页")

    explanation_readme = ROOT / manifest.get("nonnormative_explanation_boundary", "")
    if not explanation_readme.is_file():
        errors.append("缺少非规范性白话说明边界文档")
    else:
        explanation_text = explanation_readme.read_text(encoding="utf-8")
        if "非规范性" not in explanation_text or "不得作为裁定依据" not in explanation_text:
            errors.append("白话说明边界文档未明确非规范性及裁定边界")

    print("翻译阶段校验结果")
    print(f"- 底本 SHA-256：{sha256_file(PDF)}")
    print(f"- 底本页数：{page_count if page_count is not None else coverage['metadata']['pages']}")
    print(f"- 中文正文覆盖：{len(actual_pages & expected_pages)}/86 页")
    print(
        "- 顶层章节："
        f"{sum(len(page.get('top_level_sections', [])) for page in coverage.get('pages', []))} "
        "（核心规则 10，追加规则 24）"
    )
    print(f"- 已解析规则标题：{sum(len(page.get('rule_headings', [])) for page in coverage.get('pages', []))}")
    print(
        "- 卡号："
        f"{signature_card_occurrences} 次总出现，"
        f"{sum(len(page.get('card_numbers', [])) for page in coverage.get('pages', []))} 个页内不重复字面，"
        f"{len({card for page in coverage.get('pages', []) for card in page.get('card_numbers', [])})} 个全局唯一字面"
    )
    print(
        "- 显式交叉引用："
        f"{sum(len(page.get('explicit_references', [])) for page in coverage.get('pages', []))} 个"
    )
    print(f"- 已解析冻结术语标记：{len(all_term_ids)} 个不同 ID")
    print(
        "- 语义表格："
        f"{len(table_ids)} 个；PDF 页 "
        f"{sorted(page for page in actual_pages if coverage_by_page[page].get('tables'))}"
    )
    print(
        "- 修订：红 "
        f"{sum(actual_revision_segments['2025-04-25-update'].values())} 段／"
        f"{sorted(actual_revision_pages['2025-04-25-update'])}；绿 "
        f"{sum(actual_revision_segments['2025-06-02-tweak'].values())} 段／"
        f"{sorted(actual_revision_pages['2025-06-02-tweak'])}"
    )
    for warning in warnings:
        print(f"- 警告：{warning}")
    if errors:
        print(f"- 错误：{len(errors)}")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("- 状态：passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
