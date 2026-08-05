import { describe, expect, it } from "vitest";

import { loadSiteContent } from "../../src/lib/content-model";

describe("规范内容模型", () => {
  it("从唯一入口载入并验证完整规则站内容", () => {
    const model = loadSiteContent();

    expect({
      sourcePages: model.source.pages,
      sourceSha256: model.source.sha256,
      documents: model.documents.length,
      coveredPages: model.sourcePages.length,
      coreChapters: model.chapters.core.length,
      additionalChapters: model.chapters.additional.length,
      glossaryEntries: model.glossary.length,
      glossarySources: model.glossarySources.length,
      lockedEntries: model.glossary.filter((entry) => entry.review_status === "locked").length,
      ruleHeadings: model.metrics.ruleHeadings,
      cardOccurrences: model.metrics.normativeCardOccurrences,
      semanticTables: model.metrics.semanticTables,
      redRevisions: model.metrics.revisions["2025-04-25-update"],
      greenRevisions: model.metrics.revisions["2025-06-02-tweak"],
      sourceAnomalies: model.metrics.sourceAnomalies,
    }).toEqual({
      sourcePages: 86,
      sourceSha256: "b96c743b343d7522db61af03952db73189283816868b8e8747f289a71801ab98",
      documents: 5,
      coveredPages: 86,
      coreChapters: 10,
      additionalChapters: 24,
      glossaryEntries: 171,
      glossarySources: 8,
      lockedEntries: 171,
      ruleHeadings: 392,
      cardOccurrences: 490,
      semanticTables: 9,
      redRevisions: 69,
      greenRevisions: 23,
      sourceAnomalies: 8,
    });
  });
});
