# 规范简中翻译状态

最后更新：2026-08-05

## 结论

《新幕 桜降る代に決闘を》综合规则 1.14.1 的规范简中翻译已完整覆盖底本 86/86 页，并已完成规则语义与冻结术语／规范措辞两轮逐页校对。发布前独立复跑内容门禁后仍为通过状态，没有改动规范译文、术语冻结数据、翻译清单或 PDF 覆盖证据。

## 底本

- 文件：`furuyoni_comprehensive_rule.pdf`
- 版本：综合规则 1.14.1
- 页数：86
- SHA-256：`b96c743b343d7522db61af03952db73189283816868b8e8747f289a71801ab98`
- 红色修订：`2025-04-25 更新`
- 绿色修订：`2025-06-02 微調整`

## 规范正文覆盖

| 文件 | 分部 | PDF 页 |
| --- | --- | ---: |
| `content/rules/zh-Hans/00-front-matter.md` | 封面与说明 | 1 |
| `content/rules/zh-Hans/01-core-rules.md` | 核心规则 | 2–38 |
| `content/rules/zh-Hans/02-additional-rules.md` | 追加规则 | 39–74 |
| `content/rules/zh-Hans/03-appendix-goddess-list.md` | 附则 1 | 75–84 |
| `content/rules/zh-Hans/04-appendix-errata.md` | 附则 2 | 85–86 |

## 校验结果

| 项目 | 结果 |
| --- | ---: |
| PDF 页覆盖 | 86/86 |
| 顶层章节 | 34 |
| 规则标题 | 392 |
| 编号／范围词元 | 439 |
| 显式交叉引用 | 8 |
| 卡号总出现／全局唯一卡号 | 490／301 |
| 底本中出现并标记的冻结术语 | 165 |
| 经重新提取确认未在底本出现的冻结术语 | 6 |
| 表格 | 9 |
| 红色／绿色修订段 | 69／23 |
| 源文异常 | 8 个稳定 ID，均保留原状与处理边界 |
| 数值与专用符号逐页签名 | 86/86 一致 |
| 页序规范化 | 通过，无改写 |
| 第一轮规则语义校对 | 86/86，`passed` |
| 第二轮术语与规范措辞校对 | 86/86，`passed` |

## 特殊边界

- `translation-manifest.json` 记录的 8 个源文异常没有被静默修正；译文保留可追溯注记与底本字面信息。
- 第 45 页官方图示没有进入公开产物；站点只使用原创 CSS 色块和“攻击／行动／付与／对应／全力”文字标签。
- 内部日文逐页稿只用于校对，不属于公开构建。
- 白话说明与规范正文保持独立边界，不能作为规则裁定依据。

## 第一轮规则语义校对

86/86 页逐页核对规则含义、编号、数值、范围、卡号、交叉引用、表格结构和红／绿修订标记，结果全部为 `passed`。

## 第二轮冻结术语与规范措辞校对

86/86 页逐页核对 171 条冻结术语及规范表达；165 个底本实际出现的术语 ID 均已标记，其余 6 个有可重复的底本未出现证据，结果全部为 `passed`。

## 证据入口

- 完整发布验收：[`docs/research/final-qa-report.md`](../research/final-qa-report.md)
- 翻译结构与异常清单：`data/rules/translation-manifest.json`
- 数值签名：`data/rules/source-numeric-signatures.json`
- PDF 覆盖：`data/source/pdf-coverage.json`
- 冻结术语来源：[`docs/release/terminology-sources.md`](terminology-sources.md)
