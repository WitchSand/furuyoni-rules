# GitHub Pages 部署说明

最后更新：2026-08-05

## 公开地址

- 仓库：<https://github.com/WitchSand/furuyoni-rules>
- 站点：<https://witchsand.github.io/furuyoni-rules/>
- 默认分支：`main`
- Pages 发布源：GitHub Actions

站点不使用自定义域名、统计分析、评论、广告、账户、后端或运行时外部脚本。

## 构建环境与命令

- Node.js：`>=22.12.0`；
- npm：`>=9.6.5`；
- 依赖安装：`npm ci`；
- 根路径构建：`npm run build`，输出 `dist/`；
- Pages 构建：`npm run build:pages`，固定 base=`/furuyoni-rules/`，输出 `dist-pages/`；
- 完整门禁：`npm run verify:public`。

根路径和 Pages 构建必须串行执行。构建期间不得同时运行预览服务或让其他进程写入输出目录。每次复制、归档或上传前，都必须紧邻执行：

```sh
npm run audit:pages
```

审计必须显示 214 个 HTML 页面、171 个术语页、453 个文件、236 个 Pagefind 文件、4 个筛选、9 张语义表格，且外部运行时依赖、受限素材和冲突副本均为 0。

## GitHub Actions

`.github/workflows/pages.yml` 在 Pull Request、`main` 推送和手动运行时触发：

1. 使用 Node.js 22 执行 `npm ci`；
2. 安装 Playwright Chromium；
3. 执行公开源码与 Git 历史卫生审计、生产依赖高危审计、单元测试和类型检查；
4. 串行生成根路径与 Pages 子路径构建；
5. 执行完整端到端测试与最终静态产物审计；
6. 只有 `main` 的全部质量门禁通过后才上传 Pages Artifact；
7. 独立 `deploy` 作业以 `pages: write` 和 `id-token: write` 权限部署完整产物。

第三方 Actions 固定到完整提交 SHA，Dependabot 每周检查 npm 与 Actions 更新。

## 部署后冒烟

自动 HTTP 冒烟：

```sh
npm run smoke:deployment -- --url https://witchsand.github.io/furuyoni-rules/
```

还必须使用真实浏览器检查：

- 首页、规则目录、卷首、10 个核心章节、24 个追加章节和 2 个附则；
- `/furuyoni-rules/rules/core/05/#rule-5-8-3` 直接打开与刷新；
- 简中、日文、社区别名、女神名和卡号搜索；
- 171 个术语路由及其子路径前缀；
- CSS、JavaScript 与 Pagefind 都从 `/furuyoni-rules/` 加载；
- 未知路径返回自定义 404，不改写为首页；
- 来源页和 404 显示版本、86 页、固定哈希与非官方声明；
- HTTPS、canonical、禁用 JavaScript、320px、200% 重排、键盘焦点、无横向溢出、无障碍扫描和控制台。

## 仓库治理

`main` 规则集禁止删除与强推、要求线性历史、要求通过 Pull Request 更新，并要求唯一命名的 `quality` 状态检查。管理员旁路只用于紧急回滚。仓库默认工作流权限为只读；Issues 开启，Wiki、Projects 与 Discussions 关闭；依赖图、安全提醒、自动安全修复、私密漏洞报告及可用的秘密扫描能力开启。

## Release 与回滚

首发标签为 `v1.0.0`，与综合规则 1.14.1 对应。Release 不附带官方 PDF 或其他受限素材。

若线上冒烟失败，立即停止 Pages 发布并保留失败工作流和日志。修复通过 Pull Request 与全部门禁进入 `main`，不得强推、改写历史或混合新旧构建文件。后续版本可从已验证旧标签重新运行 Pages 工作流；内容错误使用 revert 或后续修正提交处理。
