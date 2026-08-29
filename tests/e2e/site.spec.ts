import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function expectNoHorizontalOverflow(page: Page): Promise<void> {
  const dimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.viewport + 1);
}

async function search(page: Page, query: string): Promise<void> {
  await page.getByRole("searchbox").fill(query);
  await page.getByRole("button", { name: "搜索", exact: true }).click();
  await expect(page.locator(".search-status")).toContainText(/找到 \d+ 条结果/);
  await expect(page.locator(".search-result").first()).toBeVisible();
}

test("数字稳定深链接、章节目录和 404 均可直接刷新", async ({ page }) => {
  const response = await page.goto("/rules/core/05/#rule-5-8-3");
  expect(response?.status()).toBe(200);
  await expect(page.locator("#rule-5-8-3")).toBeVisible();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("樱花决斗的基本定义与原则");
  await expect(page.locator(".site-nav a[href^='/rules/core/']")).toHaveCount(10);
  await expect(page.locator(".site-nav a[href^='/rules/additional/']")).toHaveCount(24);

  const missing = await page.goto("/rules/core/99/");
  expect(missing?.status()).toBe(404);
  await expect(page.getByRole("heading", { name: "没有找到这个页面" })).toBeVisible();
});

test("桌面术语工作区支持四窗、键盘、拖动、缩放、最小化、置顶、关闭和跨页恢复", async ({ page }) => {
  await page.goto("/rules/core/04/");
  await expect(page.locator("term-workspace")).toHaveClass(/is-ready/);

  const previewTerm = page.locator('term-reference[data-term-id="zone.distance"] a').first();
  await previewTerm.hover();
  await expect(page.locator(".term-preview")).toBeVisible();
  await expect(page.locator(".term-preview")).toContainText("距离");
  await page.mouse.move(0, 0);
  await expect(page.locator(".term-preview")).toBeHidden();

  for (const termId of ["zone.distance", "object.sakura-crystal"]) {
    await page.locator(`term-reference[data-term-id="${termId}"] a`).first().click();
  }
  const enterTerm = page.locator('term-reference[data-term-id="zone.aura"] a').first();
  await enterTerm.focus();
  await enterTerm.press("Enter");
  await expect(page.locator(".term-window")).toHaveCount(3);

  const keyboardTerm = page.locator('term-reference[data-term-id="zone.hand"] a').first();
  await keyboardTerm.focus();
  await keyboardTerm.press("Space");
  await expect(page.locator(".term-window")).toHaveCount(4);

  const firstWindow = page.locator('.term-window[data-term-id="zone.distance"]');
  const header = firstWindow.locator(".term-window-header");
  const beforeKeyboardMove = await firstWindow.boundingBox();
  await header.focus();
  await header.press("ArrowRight");
  const afterKeyboardMove = await firstWindow.boundingBox();
  expect(afterKeyboardMove!.x).toBeGreaterThan(beforeKeyboardMove!.x);
  await header.press("Shift+ArrowDown");
  const afterKeyboardResize = await firstWindow.boundingBox();
  expect(afterKeyboardResize!.height).toBeGreaterThan(afterKeyboardMove!.height);

  const beforeDrag = await firstWindow.boundingBox();
  const headerBox = await header.boundingBox();
  expect(beforeDrag && headerBox).toBeTruthy();
  await page.mouse.move(headerBox!.x + 30, headerBox!.y + 20);
  await page.mouse.down();
  await page.mouse.move(headerBox!.x + 125, headerBox!.y + 85, { steps: 5 });
  await page.mouse.up();
  const afterDrag = await firstWindow.boundingBox();
  expect(afterDrag!.x).not.toBe(beforeDrag!.x);

  const beforeResize = await firstWindow.boundingBox();
  await page.mouse.move(beforeResize!.x + beforeResize!.width - 3, beforeResize!.y + beforeResize!.height - 3);
  await page.mouse.down();
  await page.mouse.move(beforeResize!.x + beforeResize!.width + 45, beforeResize!.y + beforeResize!.height + 35, { steps: 5 });
  await page.mouse.up();
  const afterResize = await firstWindow.boundingBox();
  expect(afterResize!.width).toBeGreaterThan(beforeResize!.width);

  await firstWindow.getByRole("button", { name: "最小化" }).click();
  await expect(firstWindow).toHaveClass(/is-minimized/);
  await firstWindow.getByRole("button", { name: "置顶" }).click();

  await page.goto("/rules/core/05/");
  await expect(page.locator("term-workspace")).toHaveClass(/is-ready/);
  await expect(page.locator(".term-window")).toHaveCount(4);
  await expect(page.locator('.term-window[data-term-id="zone.distance"]')).toHaveClass(/is-minimized/);

  const viewport = page.viewportSize()!;
  for (const windowElement of await page.locator(".term-window").all()) {
    const box = await windowElement.boundingBox();
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.y).toBeGreaterThanOrEqual(0);
    expect(box!.x + box!.width).toBeLessThanOrEqual(viewport.width + 1);
    expect(box!.y + box!.height).toBeLessThanOrEqual(viewport.height + 1);
  }

  const keyboardClose = page.locator('.term-window[data-term-id="zone.hand"]').getByRole("button", { name: "关闭" });
  await keyboardClose.focus();
  await keyboardClose.press("Enter");
  await expect(page.locator(".term-window")).toHaveCount(3);
});

test("搜索覆盖简中、日文、社区别名、女神名、卡号与组合筛选", async ({ page }) => {
  await page.goto("/search/");
  await expect(page.locator("search-app")).toHaveClass(/is-ready/);

  await search(page, "樱花结晶");
  await expect(page.locator('.search-result a[href*="/glossary/object.sakura-crystal/"]').first()).toBeVisible();
  await search(page, "オーラ");
  await expect(page.locator('.search-result a[href*="/glossary/zone.aura/"]').first()).toBeVisible();
  await search(page, "护盾");
  await expect(page.locator('.search-result a[href*="/glossary/zone.aura/"]').first()).toBeVisible();
  await search(page, "枢");
  await expect(page.locator(".search-results")).toContainText("枢");
  await search(page, "NA-10-kururu-A1-S-3-Ex1");
  await expect(page.locator('.search-result a[href*="/rules/"]').first()).toBeVisible();

  const revisedAliases = [
    ["攻击中区", "/glossary/zone.attack-in-progress/", "攻击中"],
    ["卡姆伊", "/glossary/goddess.21/", "神居"],
    ["西斯伊", "/glossary/goddess.24/", "志水"],
    ["科达玛", "/glossary/goddess.nonselectable.kodama/", "菰珠"],
    ["赞卡", "/glossary/goddess.nonselectable.zanka/", "斩华"],
    ["沃卡", "/glossary/goddess.nonselectable.wouka/", "奥华"],
  ] as const;
  for (const [previousName, route, currentName] of revisedAliases) {
    await test.step(`旧译“${previousName}”可检索到“${currentName}”`, async () => {
      await search(page, previousName);
      const result = page.locator(`.search-result a[href*="${route}"]`).first();
      await expect(result).toBeVisible();
      await expect(result).toContainText(currentName);
    });
  }

  await page.getByLabel("内容类型").selectOption("术语");
  await page.getByLabel("术语类别").selectOption("goddess_mechanism");
  await page.locator('select[data-filter="goddess"]').selectOption("枢");
  await search(page, "机巧");
  await expect(page.locator('.search-result a[href*="/glossary/mechanic.kururu.contraption/"]').first()).toBeVisible();

  await page.getByLabel("内容类型").selectOption("规则");
  await page.getByLabel("术语类别").selectOption("");
  await page.locator('select[data-filter="goddess"]').selectOption("伊尼尔");
  await search(page, "命运牌");
  await expect(page.locator('.search-result a[href*="/rules/additional/24/"]').first()).toBeVisible();
});

test("搜索面板在桌面端只绘制一个完整边框盒", async ({ page }) => {
  await page.goto("/search/");
  const searchPanel = page.locator("search-app.search-panel");
  await expect(searchPanel).toHaveClass(/is-ready/);

  const fragments = await searchPanel.evaluate((element) =>
    Array.from(element.getClientRects(), ({ width, height }) => ({ width, height })),
  );
  expect(fragments).toHaveLength(1);
  expect(fragments[0].width).toBeGreaterThan(600);
  expect(fragments[0].height).toBeGreaterThan(0);
});

test("320px 窄屏使用章节抽屉与术语堆叠抽屉且无横向溢出", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 720 });
  await page.goto("/rules/core/04/");
  await expectNoHorizontalOverflow(page);

  const navigationButton = page.getByRole("button", { name: "章节导航", exact: true });
  await expect(navigationButton).toBeVisible();
  await navigationButton.click();
  await expect(page.locator("site-navigation")).toHaveClass(/is-open/);
  await page.keyboard.press("Escape");
  await expect(page.locator("site-navigation")).not.toHaveClass(/is-open/);
  await expect(navigationButton).toBeFocused();

  await expect(page.locator("term-workspace")).toHaveClass(/is-ready/);
  await page.locator('term-reference[data-term-id="zone.distance"] a').first().click();
  await expect(page.locator("term-workspace")).toHaveClass(/mobile-open/);
  await expect(page.locator(".term-window")).toHaveCount(1);
  await expect(page.locator(".term-window")).toHaveCSS("position", "static");
  await expect(page.getByRole("button", { name: /固定术语/ })).toBeVisible();
  await expectNoHorizontalOverflow(page);
});

test("禁用 JavaScript 后正文、章节导航、术语链接与深链接仍完整可用", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 320, height: 720 } });
  const page = await context.newPage();
  const response = await page.goto("http://127.0.0.1:4321/rules/core/10/#rule-10-44");
  expect(response?.status()).toBe(200);
  await expect(page.locator("#rule-10-44")).toContainText("结算卡牌效果时适用的效果");
  await expect(page.locator(".site-nav")).toBeVisible();
  await expect(page.locator("term-reference a").first()).toHaveAttribute("href", /\/glossary\/.+\/$/);
  await expect(page.locator(".term-window")).toHaveCount(0);
  await expectNoHorizontalOverflow(page);
  await context.close();
});

test("子路径构建支持深链刷新、资源与 Pagefind 搜索", async ({ page, request }) => {
  const ruleResponse = await page.goto(
    "http://127.0.0.1:4322/furuyoni-rules/rules/core/05/#rule-5-8-3",
  );
  expect(ruleResponse?.status()).toBe(200);
  await expect(page.locator("#rule-5-8-3")).toBeVisible();
  await expect(page.locator('link[rel="stylesheet"]')).toHaveAttribute(
    "href",
    /^\/furuyoni-rules\/_assets\//,
  );
  const pagefindResponse = await request.get(
    "http://127.0.0.1:4322/furuyoni-rules/pagefind/pagefind.js",
  );
  expect(pagefindResponse.status()).toBe(200);

  await page.goto("http://127.0.0.1:4322/furuyoni-rules/search/");
  await expect(page.locator("search-app")).toHaveClass(/is-ready/);
  await search(page, "护盾");
  await expect(
    page.locator('.search-result a[href="/furuyoni-rules/glossary/zone.aura/"]').first(),
  ).toBeVisible();
});

test("桌面宽屏、200% 重排代理及代表页通过 WCAG A/AA 自动检查", async ({ page }) => {
  const representativeRoutes = [
    "/rules/front/",
    "/rules/core/05/",
    "/rules/additional/08/",
    "/rules/additional/10/",
    "/rules/appendix/01/",
    "/rules/appendix/02/",
    "/search/",
    "/glossary/zone.aura/",
    "/about/source/",
  ];
  for (const route of representativeRoutes) {
    await page.goto(route);
    await expectNoHorizontalOverflow(page);
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    expect(results.violations, `${route} 的无障碍违规`).toEqual([]);
  }

  await page.setViewportSize({ width: 640, height: 900 });
  await page.goto("/rules/additional/10/");
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: "artifacts/site-qa/200-percent-reflow.png", fullPage: true });
});
