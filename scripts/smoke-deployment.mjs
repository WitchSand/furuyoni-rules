#!/usr/bin/env node

import { setDefaultResultOrder } from "node:dns";

setDefaultResultOrder("ipv6first");

const TRANSIENT_NETWORK_ERRORS = new Set([
  "EAI_AGAIN",
  "ECONNRESET",
  "ETIMEDOUT",
  "UND_ERR_CONNECT_TIMEOUT",
]);
const RETRY_DELAYS_MS = [0, 250, 750];

function delay(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function fetchWithRetry(url, options) {
  let lastError;
  for (const retryDelay of RETRY_DELAYS_MS) {
    if (retryDelay > 0) await delay(retryDelay);
    try {
      return await fetch(url, options);
    } catch (error) {
      lastError = error;
      const code = error?.cause?.code;
      if (!TRANSIENT_NETWORK_ERRORS.has(code)) throw error;
    }
  }
  throw lastError;
}

function argument(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

function fail(message) {
  throw new Error(`线上冒烟失败：${message}`);
}

const requestedUrl = argument("--url");
if (!requestedUrl) fail("必须传入 --url");
const baseUrl = new URL(requestedUrl);
if (baseUrl.protocol !== "https:") fail("部署地址必须使用 HTTPS");
baseUrl.hash = "";
baseUrl.search = "";
if (!baseUrl.pathname.endsWith("/")) baseUrl.pathname += "/";
const basePath = baseUrl.pathname;

async function fetchText(path, expectedStatus = 200) {
  const url = new URL(path.replace(/^\//u, ""), baseUrl);
  const response = await fetchWithRetry(url, { redirect: "follow", headers: { "user-agent": "furuyoni-release-smoke/1.0" } });
  const text = await response.text();
  if (response.status !== expectedStatus) fail(`${url} 应返回 ${expectedStatus}，实际为 ${response.status}`);
  return { url, response, text };
}

const routes = [
  "",
  "rules/",
  "rules/front/",
  ...Array.from({ length: 10 }, (_, index) => `rules/core/${String(index + 1).padStart(2, "0")}/`),
  ...Array.from({ length: 24 }, (_, index) => `rules/additional/${String(index + 1).padStart(2, "0")}/`),
  "rules/appendix/01/",
  "rules/appendix/02/",
  "search/",
  "glossary/zone.aura/",
  "about/source/",
];
const pages = [];
for (const route of routes) pages.push(await fetchText(route));

const deepLink = await fetchText("rules/core/05/");
if (!deepLink.text.includes('id="rule-5-8-3"')) fail("稳定深链目标 rule-5-8-3 不存在");

const sourcePage = pages.find((page) => page.url.pathname.endsWith("/about/source/"));
const requiredSourceText = [
  "1.14.1",
  "86",
  "b96c743b343d7522db61af03952db73189283816868b8e8747f289a71801ab98",
  "非官方",
];
for (const text of requiredSourceText) {
  if (!sourcePage?.text.includes(text)) fail(`来源页缺少 ${text}`);
}

const notFound = await fetchText(`__release-smoke-not-found-${Date.now()}/`, 404);
for (const text of requiredSourceText) {
  if (!notFound.text.includes(text)) fail(`404 页缺少 ${text}`);
}
if (!/<meta\s+name="robots"\s+content="noindex"/iu.test(notFound.text)) fail("404 页缺少 noindex");

const home = pages[0];
const canonical = home.text.match(/<link\s+rel="canonical"\s+href="([^"]+)"/iu)?.[1];
if (canonical !== baseUrl.toString()) fail(`首页 canonical 错误：${canonical}`);
const ogUrl = home.text.match(/<meta\s+property="og:url"\s+content="([^"]+)"/iu)?.[1];
if (ogUrl !== baseUrl.toString()) fail(`首页 Open Graph URL 错误：${ogUrl}`);

const assetUrls = new Set();
for (const page of [home, pages.find((item) => item.url.pathname.endsWith("/search/"))]) {
  for (const match of page.text.matchAll(/(?:href|src)="([^"]+)"/giu)) {
    const value = match[1];
    if (!value.startsWith(basePath)) continue;
    if (/\.(?:css|js|mjs|wasm)(?:\?|$)/iu.test(value)) assetUrls.add(new URL(value, baseUrl.origin).toString());
  }
}
assetUrls.add(new URL("pagefind/pagefind.js", baseUrl).toString());
for (const url of assetUrls) {
  const response = await fetchWithRetry(url, { redirect: "follow", headers: { "user-agent": "furuyoni-release-smoke/1.0" } });
  if (!response.ok) fail(`资源 ${url} 返回 ${response.status}`);
  if (!new URL(response.url).pathname.startsWith(basePath)) fail(`资源越出 Pages 子路径：${response.url}`);
}

const glossaryResponse = await fetchText("data/glossary.json");
const glossary = JSON.parse(glossaryResponse.text);
if (!Array.isArray(glossary.terms) || glossary.terms.length !== 171) fail("线上术语 JSON 不是 171 条");
const revisedTerms = [
  ["zone.attack-in-progress", "攻击中区", "攻击中"],
  ["goddess.21", "卡姆伊", "神居"],
  ["goddess.24", "西斯伊", "志水"],
  ["goddess.nonselectable.kodama", "科达玛", "菰珠"],
  ["goddess.nonselectable.zanka", "赞卡", "斩华"],
  ["goddess.nonselectable.wouka", "沃卡", "奥华"],
];
for (const [id, previousName, currentName] of revisedTerms) {
  const term = glossary.terms.find((candidate) => candidate.id === id);
  if (!term) fail(`线上术语 JSON 缺少 ${id}`);
  if (term.recommended_zh !== currentName) fail(`${id} 的线上推荐名不是“${currentName}”`);
  if (!term.aliases.includes(previousName)) fail(`${id} 未在线上别名中保留旧译“${previousName}”`);
  if (term.aliases.includes(currentName)) fail(`${id} 的线上别名仍与推荐名“${currentName}”重复`);
}

const normativeChecks = [
  ["/rules/core/07/", "攻击中", "攻击中区"],
  ["/rules/additional/19/", "神居", "卡姆伊"],
  ["/rules/additional/22/", "志水", "西斯伊"],
  ["/rules/appendix/01/", "菰珠", "科达玛"],
  ["/rules/appendix/01/", "斩华", "赞卡"],
  ["/rules/appendix/01/", "奥华", "沃卡"],
];
for (const [route, currentName, previousName] of normativeChecks) {
  const page = pages.find((candidate) => candidate.url.pathname.endsWith(route));
  if (!page?.text.includes(currentName)) fail(`${route} 缺少现行译名“${currentName}”`);
  if (page.text.includes(previousName)) fail(`${route} 的规范正文仍含旧译“${previousName}”`);
}

const wrongBase = new URL("/rules/core/05/", baseUrl.origin);
const wrongBaseResponse = await fetchWithRetry(wrongBase, { redirect: "manual" });
if (wrongBaseResponse.status !== 404) fail(`无前缀规则路径应返回 404，实际为 ${wrongBaseResponse.status}`);

console.log(JSON.stringify({
  status: "passed",
  url: baseUrl.toString(),
  https: true,
  routes: routes.length,
  deepLink: `${baseUrl}rules/core/05/#rule-5-8-3`,
  glossaryTerms: glossary.terms.length,
  revisedTerms: revisedTerms.length,
  checkedAssets: assetUrls.size,
  custom404: true,
  wrongBase404: true,
  canonical: true,
  openGraph: true,
}, null, 2));
