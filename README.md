# 《散樱乱武 新幕》综合规则简中站

这是《新幕 桜降る代に決闘を》综合规则 1.14.1 的非营利、非官方简中民间翻译与纯静态规则站。

- 在线站点：<https://witchsand.github.io/furuyoni-rules/>
- 公开仓库：<https://github.com/WitchSand/furuyoni-rules>
- 官方底本：86 页，SHA-256 `b96c743b343d7522db61af03952db73189283816868b8e8747f289a71801ab98`
- 官方来源：[BakaFire Party 综合规则 PDF](https://main-bakafire.ssl-lolipop.jp/furuyoni/sp/na/dl/furuyoni_comprehensive_rule.pdf)

本站不附带原 PDF、卡图、立绘、官方标志或其他官方素材。规则含义以日文官方底本为最高权威；发现差异时，请以底本页码和规则编号提出纠错。

## 功能

- 完整覆盖底本 86/86 页：卷首、10 个核心规则章节、24 个追加规则章节与 2 个附则；
- 保留规则编号、PDF 页码、卡号、交叉引用、表格及红／绿修订信息；
- 171 条已冻结术语的独立页面、日文与社区别名检索；
- 支持稳定深链、键盘操作、窄屏、200% 重排与禁用 JavaScript 后的正文阅读；
- 无服务器逻辑、数据库、CDN 字体、统计脚本或运行时外部依赖。

## 目录

| 路径 | 内容 |
| --- | --- |
| `content/rules/zh-Hans/` | 规范简中正文 |
| `data/` | 术语、翻译清单、来源与底本覆盖证据 |
| `src/` | Astro 静态站源码 |
| `scripts/` | 内容、构建、公开源码与部署审计 |
| `tests/` | 单元测试与 Playwright 端到端测试 |
| `docs/release/` | 翻译状态、术语来源与部署说明 |
| `docs/research/` | 来源、PDF 覆盖、术语审核与最终 QA 证据 |

## 本地开发

需要 Node.js `>=22.12.0` 与 npm `>=9.6.5`。

```sh
npm ci
npm run dev
```

完整公开发布门禁：

```sh
npm run verify:public
```

该命令依次执行公开源码卫生审计、生产依赖高危审计、17 项单元测试、Astro/TypeScript 检查、根路径构建、GitHub Pages 子路径构建和 8 项端到端测试。默认使用本机 Chrome；若要使用 Playwright 自带 Chromium：

```sh
npx playwright install chromium
PLAYWRIGHT_CHANNEL=chromium npm run verify:public
```

## 底本复现校验

原 PDF 不在仓库中。需要复现 PDF 覆盖和数值签名时，请自行从上方官方链接取得文件，确认文件名为 `furuyoni_comprehensive_rule.pdf`，再安装研究依赖：

```sh
python3 -m pip install -r requirements-research.txt
python3 scripts/extract_pdf_inventory.py
python3 scripts/validate_terminology_stage.py
python3 scripts/validate_translation_stage.py
python3 scripts/normalize_translation_page_order.py
python3 scripts/build_translation_signatures.py
```

任何哈希或页数不匹配都应停止校验，不得用其他版本静默覆盖 1.14.1 的证据。

## 部署与维护

`npm run build:pages` 以 `/furuyoni-rules/` 为固定基址生成 `dist-pages/`。`main` 的 GitHub Actions 在全部质量门禁通过后才上传并部署该目录。部署、回滚和线上冒烟命令见 [`docs/release/deployment.md`](docs/release/deployment.md)。

提交规则纠错或站点缺陷前请阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)；安全问题见 [`SECURITY.md`](SECURITY.md)。

## 权利声明

原创程序代码依 [`LICENSE`](LICENSE) 采用 MIT License。规范译文、术语、证据数据及原作相关内容不纳入 MIT，具体边界见 [`NOTICE.md`](NOTICE.md)。《新幕 桜降る代に決闘を》及相关权利归原作者与 BakaFire Party 所有。本项目与 BakaFire Party 无隶属或认可关系。
