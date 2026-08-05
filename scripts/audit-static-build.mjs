#!/usr/bin/env node

import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { extname, join, relative, resolve } from "node:path";

function argument(name, fallback) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

function normalizeBase(value) {
  const clean = `/${value}`.replace(/\/{2,}/g, "/").replace(/\/+$/g, "");
  return clean === "" || clean === "/" ? "/" : `${clean}/`;
}

function walk(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    return entry.isDirectory() ? walk(path) : [path];
  });
}

function fail(message) {
  throw new Error(`静态构建审计失败：${message}`);
}

const directoryName = argument("--dir", "dist");
const base = normalizeBase(argument("--base", "/"));
const siteOrigin = (process.env.SITE_ORIGIN || "https://witchsand.github.io").replace(/\/+$/u, "");
if (!/^[a-zA-Z0-9._-]+$/.test(directoryName) || !directoryName.startsWith("dist")) {
  fail(`不安全的审计目录 ${directoryName}`);
}
const root = resolve(directoryName);
if (!existsSync(root) || !statSync(root).isDirectory()) fail(`${directoryName} 不存在`);
const files = walk(root);
const relativeFiles = files.map((path) => relative(root, path));

const expectedRoutes = [
  "index.html",
  "404.html",
  "rules/index.html",
  "rules/front/index.html",
  ...Array.from({ length: 10 }, (_, index) => `rules/core/${String(index + 1).padStart(2, "0")}/index.html`),
  ...Array.from({ length: 24 }, (_, index) => `rules/additional/${String(index + 1).padStart(2, "0")}/index.html`),
  "rules/appendix/01/index.html",
  "rules/appendix/02/index.html",
  "glossary/index.html",
  "search/index.html",
  "about/source/index.html",
  "data/glossary.json",
  "pagefind/pagefind.js",
];
for (const route of expectedRoutes) {
  if (!relativeFiles.includes(route)) fail(`缺少 ${route}`);
}

const glossary = JSON.parse(readFileSync(join(root, "data/glossary.json"), "utf8"));
if (!Array.isArray(glossary.terms) || glossary.terms.length !== 171) fail("公开术语数据不为 171 条");
for (const term of glossary.terms) {
  const route = `glossary/${term.id}/index.html`;
  if (!relativeFiles.includes(route)) fail(`缺少独立术语页 ${route}`);
}

const forbiddenExtensions = new Set([".pdf", ".sqlite", ".sqlite3", ".db", ".docx", ".psd", ".ai"]);
const forbiddenNames = /furuyoni_comprehensive_rule|japanese-pages|page-render|official-logo|card-image|立绘|卡图/i;
const conflictCopyName = / [23](?=(?:\.[^/]+)?$)/;
for (const file of relativeFiles) {
  if (file.split("/").includes(".DS_Store")) fail(`包含 macOS 元数据 ${file}`);
  if (forbiddenExtensions.has(extname(file).toLowerCase())) fail(`包含禁止文件 ${file}`);
  if (forbiddenNames.test(file)) fail(`疑似包含受限或内部素材 ${file}`);
  if (file.split("/").some((name) => conflictCopyName.test(name))) {
    fail(`包含冲突副本 ${file}`);
  }
}

const htmlFiles = files.filter((path) => extname(path) === ".html");
if (htmlFiles.length !== 214) fail(`HTML 页面应为 214，实际为 ${htmlFiles.length}`);
if (files.length !== 453) fail(`总文件数应为 453，实际为 ${files.length}`);
const externalRuntime = /<(?:script|img|iframe|audio|video|source|embed|object)[^>]+(?:src|poster|data)=["']https?:\/\//i;
const externalLinkResource = /<link\b(?=[^>]*\brel=["'](?:stylesheet|preload|modulepreload|icon|manifest)["'])(?=[^>]*\bhref=["']https?:\/\/)[^>]*>/i;
const externalCssUrl = /url\(["']?https?:\/\//i;
let semanticTableCount = 0;
for (const file of htmlFiles) {
  const html = readFileSync(file, "utf8");
  if (externalRuntime.test(html) || externalLinkResource.test(html) || externalCssUrl.test(html)) {
    fail(`${relative(root, file)} 含运行时外部资源`);
  }
  const canonicalTag = html.match(/<link\b(?=[^>]*\brel=["']canonical["'])[^>]*>/i)?.[0];
  const canonical = canonicalTag?.match(/\bhref=["']([^"']+)["']/i)?.[1];
  if (!canonical || !canonical.startsWith(`${siteOrigin}${base}`)) {
    fail(`${relative(root, file)} 缺少当前基址下的 canonical URL`);
  }
  const openGraphUrlTag = html.match(/<meta\b(?=[^>]*\bproperty=["']og:url["'])[^>]*>/i)?.[0];
  const openGraphUrl = openGraphUrlTag?.match(/\bcontent=["']([^"']+)["']/i)?.[1];
  if (openGraphUrl !== canonical) fail(`${relative(root, file)} 的 og:url 与 canonical 不一致`);
  for (const property of ["og:type", "og:title", "og:description", "og:locale"]) {
    if (!new RegExp(`<meta\\b(?=[^>]*\\bproperty=["']${property}["'])[^>]*>`, "i").test(html)) {
      fail(`${relative(root, file)} 缺少 ${property}`);
    }
  }
  for (const match of html.matchAll(/(?:href|src)=["'](\/[^"'#?]*)/g)) {
    const url = match[1];
    if (base !== "/" && !url.startsWith(base)) {
      fail(`${relative(root, file)} 含越出 base=${base} 的绝对内部路径 ${url}`);
    }
  }

  for (const match of html.matchAll(/<table\b[^>]*>[\s\S]*?<\/table>/gi)) {
    const table = match[0];
    semanticTableCount += 1;
    if (!/<caption\b[^>]*>[\s\S]*?<\/caption>/i.test(table)) {
      fail(`${relative(root, file)} 的表格缺少 caption`);
    }
    if (!/<th\b[^>]*\bscope=["']row["'][^>]*>/i.test(table)) {
      fail(`${relative(root, file)} 的表格缺少 scope=row 行标题`);
    }
    const tableHead = table.match(/<thead\b[^>]*>[\s\S]*?<\/thead>/i)?.[0];
    if (tableHead) {
      const columnHeaders = [...tableHead.matchAll(/<th\b[^>]*>/gi)].map((header) => header[0]);
      if (
        columnHeaders.length === 0
        || columnHeaders.some((header) => !/\bscope=["']col["']/i.test(header))
      ) {
        fail(`${relative(root, file)} 的表头缺少 scope=col`);
      }
    }
  }
}
if (semanticTableCount !== 9) fail(`语义表格应为 9，实际为 ${semanticTableCount}`);

const htmlIdCache = new Map();
function htmlIds(file) {
  if (htmlIdCache.has(file)) return htmlIdCache.get(file);
  const ids = new Set(
    [...readFileSync(file, "utf8").matchAll(/\bid=["']([^"']+)["']/g)].map((match) => match[1]),
  );
  htmlIdCache.set(file, ids);
  return ids;
}

function pageUrl(file) {
  const local = relative(root, file).replaceAll("\\", "/");
  const route = local === "index.html"
    ? ""
    : local.endsWith("/index.html")
      ? local.slice(0, -"index.html".length)
      : local;
  return `https://static.invalid${base}${route}`;
}

for (const file of htmlFiles) {
  const html = readFileSync(file, "utf8");
  for (const match of html.matchAll(/\bhref=["']([^"']+)["']/g)) {
    const href = match[1];
    if (!href || /^(?:https?:|mailto:|tel:)/i.test(href)) continue;
    const target = new URL(href, pageUrl(file));
    if (target.origin !== "https://static.invalid") continue;
    if (!target.pathname.startsWith(base)) {
      fail(`${relative(root, file)} 的链接越出 base=${base}：${href}`);
    }
    const localPath = decodeURIComponent(target.pathname.slice(base.length));
    const targetRelative = localPath === ""
      ? "index.html"
      : localPath.endsWith("/")
        ? `${localPath}index.html`
        : localPath;
    if (!relativeFiles.includes(targetRelative)) {
      fail(`${relative(root, file)} 链接到不存在的文件 ${href}`);
    }
    if (!target.hash || extname(targetRelative) !== ".html") continue;
    const fragment = decodeURIComponent(target.hash.slice(1));
    if (!htmlIds(join(root, targetRelative)).has(fragment)) {
      fail(`${relative(root, file)} 链接到不存在的片段 ${href}`);
    }
  }
}

const cssAndJsFiles = files.filter((path) => [".css", ".js", ".mjs"].includes(extname(path)));
for (const file of cssAndJsFiles) {
  const source = readFileSync(file, "utf8");
  if (externalCssUrl.test(source) || /(?:import|fetch)\s*\(\s*["']https?:\/\//i.test(source)) {
    fail(`${relative(root, file)} 含运行时外部依赖`);
  }
}

const pagefindFiles = relativeFiles.filter((file) => file.startsWith("pagefind/"));
if (pagefindFiles.length < 5) fail("Pagefind 索引文件不完整");
const pagefindFilterFiles = relativeFiles.filter(
  (file) => file.startsWith("pagefind/filter/") && file.endsWith(".pf_filter"),
);
if (pagefindFilterFiles.length !== 4) {
  fail(`Pagefind 筛选索引应为 4，实际为 ${pagefindFilterFiles.length}`);
}

console.log(JSON.stringify({
  status: "passed",
  base,
  htmlPages: htmlFiles.length,
  glossaryPages: glossary.terms.length,
  files: files.length,
  pagefindFiles: pagefindFiles.length,
  pagefindFilters: pagefindFilterFiles.length,
  semanticTables: semanticTableCount,
  externalRuntimeDependencies: 0,
  forbiddenArtifacts: 0,
}, null, 2));
