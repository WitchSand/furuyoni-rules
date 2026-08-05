#!/usr/bin/env python3
"""从唯一 PDF 底本生成逐页数值与符号词素签名。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "furuyoni_comprehensive_rule.pdf"
OUTPUT = ROOT / "data/rules/source-numeric-signatures.json"
TERMS = ROOT / "data/glossary/terms.json"
MANIFEST = ROOT / "data/rules/translation-manifest.json"
EXPECTED_SHA256 = "b96c743b343d7522db61af03952db73189283816868b8e8747f289a71801ab98"
CARD_NUMBER_RE = re.compile(r"NA-\d{2}(?:/\d{2})?(?:-{1,2}[A-Za-z0-9/]+){2,}")
TRANSFORM_NUMBER_RE = re.compile(r"TransForm\s+Card\s+(?:A1-)?\d{2}")
TRANSFORM_NUMBER_COMPACT_RE = re.compile(r"TransFormCard(?:A1-)?\d{2}")


def repair_text_layer(page_number: int, text: str) -> str:
    """修复已人工对照 PDF 版面确认的文本层断行。

    第 15 页的“10 个樱花结晶”在文本层被拆成行末“１”与下一行“０个”。
    仅修复这一处已知字面，且强制要求恰好命中一次，避免吞掉表格行界。
    """

    if page_number != 15:
        return text
    repaired, replacements = re.subn(r"１[ \t]*\n[ \t]*０個", "１０個", text, count=1)
    if replacements != 1:
        raise RuntimeError("第 15 页预期的“10 个樱花结晶”文本层断行未唯一命中")
    return repaired


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def without_printed_page(text: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        if line.strip().isdigit():
            del lines[index]
        break
    return "\n".join(lines)


def numeric_lexemes(text: str) -> Counter[str]:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = re.sub(r"(?<=\d)[ \t]+(?=\d)", "", normalized)
    return Counter(re.findall(r"\d+", normalized))


def symbolic_lexemes(text: str) -> Counter[str]:
    normalized = unicodedata.normalize("NFKC", text)
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


def card_lexemes(text: str) -> Counter[str]:
    """提取卡号及变形卡编号并保留同页重复次数。"""

    compact = re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))
    cards = Counter(CARD_NUMBER_RE.findall(compact))
    cards.update(TRANSFORM_NUMBER_COMPACT_RE.findall(compact))
    return cards


def ordered(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: (len(item[0]), item[0])))


def build() -> dict[str, object]:
    actual_hash = sha256_file(PDF)
    if actual_hash != EXPECTED_SHA256:
        raise RuntimeError(f"底本 SHA-256 不一致：{actual_hash}")
    reader = PdfReader(str(PDF))
    if len(reader.pages) != 86:
        raise RuntimeError(f"底本页数不为 86：{len(reader.pages)}")
    pages: dict[str, object] = {}
    source_texts: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        source_texts.append(raw_text)
        text = repair_text_layer(page_number, without_printed_page(raw_text))
        pages[str(page_number)] = {
            "numeric": ordered(numeric_lexemes(text)),
            "symbolic": ordered(symbolic_lexemes(text)),
            "cards": ordered(card_lexemes(text)),
        }

    terms = json.loads(TERMS.read_text(encoding="utf-8"))["terms"]
    term_by_id = {term["id"]: term for term in terms}
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    excluded_ids = manifest.get("terms_not_in_normative_source", [])
    complete_source_text = "\n".join(source_texts)
    verified_absent_terms: dict[str, str] = {}
    for term_id in excluded_ids:
        term = term_by_id.get(term_id)
        if term is None:
            raise RuntimeError(f"翻译清单中的底本未出现术语 ID 不存在：{term_id}")
        japanese = term["ja"]
        if japanese in complete_source_text:
            raise RuntimeError(f"声明为底本未出现的术语实际存在：{term_id} / {japanese}")
        verified_absent_terms[term_id] = japanese

    return {
        "schema_version": 1,
        "source_sha256": actual_hash,
        "source_pages": 86,
        "extraction": "pypdf text layer; leading printed-page numeral removed; Unicode NFKC",
        "text_layer_repairs": {"15": "１\\n０個 -> １０個；已与 PDF 版面人工对照"},
        "verified_absent_locked_terms": verified_absent_terms,
        "pages": pages,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="写入生成结果；默认仅检查现有文件")
    args = parser.parse_args()
    payload = build()
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(rendered, encoding="utf-8")
        print(f"已写入 {OUTPUT.relative_to(ROOT)}：86 页")
        return 0
    if not OUTPUT.is_file():
        print(f"缺少 {OUTPUT.relative_to(ROOT)}；请先使用 --write 生成", file=sys.stderr)
        return 1
    if OUTPUT.read_text(encoding="utf-8") != rendered:
        print("数值与符号词素签名已过期", file=sys.stderr)
        return 1
    print("数值与符号词素签名与底本一致：86 页")
    return 0


if __name__ == "__main__":
    sys.exit(main())
