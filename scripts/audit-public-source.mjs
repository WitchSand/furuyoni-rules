#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import {
  existsSync,
  mkdtempSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  statSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, extname, join, relative, resolve } from "node:path";

function argument(name, fallback) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

function hasFlag(name) {
  return process.argv.includes(name);
}

function run(command, args, options = {}) {
  return execFileSync(command, args, { encoding: "utf8", ...options });
}

function walk(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    return entry.isDirectory() ? walk(path) : [path];
  });
}

function fail(message) {
  throw new Error(`公开源码卫生审计失败：${message}`);
}

function portable(path) {
  return path.replaceAll("\\", "/");
}

const repositoryRoot = resolve(argument("--root", "."));
const treeish = argument("--treeish", "HEAD");
if (!existsSync(repositoryRoot) || !statSync(repositoryRoot).isDirectory()) {
  fail(`目录不存在：${repositoryRoot}`);
}

let auditRoot = repositoryRoot;
let temporaryRoot;
if (existsSync(join(repositoryRoot, ".git"))) {
  temporaryRoot = mkdtempSync(join(tmpdir(), "furuyoni-public-audit-"));
  const archivePath = join(temporaryRoot, "snapshot.tar");
  const snapshotPath = join(temporaryRoot, "snapshot");
  mkdirSync(snapshotPath);
  run("git", ["-C", repositoryRoot, "archive", "--format=tar", "--output", archivePath, treeish]);
  run("tar", ["-xf", archivePath, "-C", snapshotPath]);
  auditRoot = snapshotPath;
}

try {
  const files = walk(auditRoot);
  const relativeFiles = files.map((file) => portable(relative(auditRoot, file))).sort();
  const fileSet = new Set(relativeFiles);

  const requiredFiles = [
    ".github/CODEOWNERS",
    ".github/ISSUE_TEMPLATE/rule-correction.yml",
    ".github/ISSUE_TEMPLATE/site-bug.yml",
    ".github/dependabot.yml",
    ".github/pull_request_template.md",
    ".github/workflows/pages.yml",
    "CHANGELOG.md",
    "CONTEXT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "NOTICE.md",
    "README.md",
    "SECURITY.md",
    "content/rules/zh-Hans/00-front-matter.md",
    "data/glossary/decision-record.json",
    "data/glossary/terms.json",
    "docs/release/deployment.md",
    "docs/release/terminology-sources.md",
    "docs/release/translation-status.md",
    "docs/research/final-qa-report.md",
    "docs/research/pdf-coverage.md",
    "docs/research/source-evidence.md",
    "docs/research/terminology-review.md",
    "package-lock.json",
    "package.json",
    "scripts/audit-static-build.mjs",
    "scripts/smoke-deployment.mjs",
    "src/pages/index.astro",
    "tests/e2e/site.spec.ts",
  ];
  for (const file of requiredFiles) {
    if (!fileSet.has(file)) fail(`缺少公开必需文件 ${file}`);
  }

  const forbiddenExact = new Set([
    "AGENTS.md",
    "content/explanations/README.md",
    "docs/research/full-rule-translation-review.md",
    "docs/research/static-site-build-review.md",
    "furuyoni_comprehensive_rule.pdf",
  ]);
  const forbiddenSegments = new Set([
    ".astro",
    ".local",
    ".npm-cache",
    [".scr", "atch"].join(""),
    "__pycache__",
    "coverage",
    "dist",
    "dist-pages",
    "dist-subpath",
    "node_modules",
    "playwright-report",
    "test-results",
  ]);
  const forbiddenExtensions = new Set([
    ".ai",
    ".avif",
    ".bmp",
    ".db",
    ".docx",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".psd",
    ".sqlite",
    ".sqlite3",
    ".tif",
    ".tiff",
    ".webp",
  ]);
  for (const file of relativeFiles) {
    const segments = file.split("/");
    if (forbiddenExact.has(file)) fail(`包含禁止公开的文件 ${file}`);
    if (segments[0] === "docs" && segments[1] === "agents") fail(`包含内部治理文档 ${file}`);
    if (segments[0] === "artifacts") fail(`包含本地报告或截图 ${file}`);
    if (segments.some((segment) => forbiddenSegments.has(segment))) fail(`包含禁止路径 ${file}`);
    if (segments.some((segment) => segment === ".DS_Store")) fail(`包含 macOS 元数据 ${file}`);
    if (forbiddenExtensions.has(extname(file).toLowerCase())) fail(`包含禁止扩展名 ${file}`);
    if (segments.some((segment) => / [23](?=(?:\.[^/]+)?$)/u.test(segment))) {
      fail(`包含文件名冲突副本 ${file}`);
    }
  }

  const internalTaskLabel = new RegExp(`${["任", "务"].join("")}\\s*0[6-9]`, "u");
  const internalStateLabel = ["ready", "for", "agent"].join("-");
  const internalTrackerPath = [".scr", "atch"].join("");
  const absoluteMacPath = new RegExp(`/${"Users"}/[^/\\s]+/`, "u");
  const absoluteLinuxPath = new RegExp(`/${"home"}/[^/\\s]+/`, "u");
  const absoluteWindowsPath = new RegExp(`${"[A-Za-z]:\\\\Users\\\\"}[^\\\\\\s]+`, "u");
  const secretPatterns = [
    new RegExp(`gh${"[pousr]"}_[A-Za-z0-9]{20,}`, "u"),
    new RegExp(`${["github", "pat"].join("_") }_[A-Za-z0-9_]{20,}`, "u"),
    /AKIA[0-9A-Z]{16}/u,
    new RegExp(`${["BEGIN", "PRIVATE", "KEY"].join("[ -]")}`, "u"),
    /https?:\/\/[^\s/:]+:[^\s/@]+@/u,
  ];

  const markdownLinks = [];
  let scannedTextFiles = 0;
  for (const file of files) {
    const relativeFile = portable(relative(auditRoot, file));
    const buffer = readFileSync(file);
    if (buffer.includes(0)) continue;
    const source = buffer.toString("utf8");
    scannedTextFiles += 1;
    if (internalTaskLabel.test(source)) fail(`${relativeFile} 含内部任务标签`);
    if (source.includes(internalStateLabel)) fail(`${relativeFile} 含内部分诊状态`);
    if (source.includes(internalTrackerPath)) fail(`${relativeFile} 含内部任务目录引用`);
    if (absoluteMacPath.test(source) || absoluteLinuxPath.test(source) || absoluteWindowsPath.test(source)) {
      fail(`${relativeFile} 含绝对本机用户路径`);
    }
    if (secretPatterns.some((pattern) => pattern.test(source))) fail(`${relativeFile} 含疑似凭据`);

    if (extname(relativeFile).toLowerCase() === ".md") {
      for (const match of source.matchAll(/\[[^\]]*\]\(([^)]+)\)/gu)) {
        markdownLinks.push({ source: relativeFile, target: match[1].trim() });
      }
    }
  }

  for (const link of markdownLinks) {
    let target = link.target;
    if (!target || target.startsWith("#") || /^(?:https?:|mailto:|tel:)/iu.test(target)) continue;
    if (target.startsWith("<") && target.endsWith(">")) target = target.slice(1, -1);
    target = target.split("#", 1)[0].split("?", 1)[0];
    if (!target) continue;
    const resolved = portable(relative(auditRoot, resolve(auditRoot, dirname(link.source), decodeURIComponent(target))));
    const candidate = resolved.endsWith("/") ? `${resolved}README.md` : resolved;
    if (!fileSet.has(candidate)) fail(`${link.source} 链接到不存在的文件 ${link.target}`);
  }

  let historyObjects = 0;
  let commits;
  if (hasFlag("--git-history")) {
    if (!existsSync(join(repositoryRoot, ".git"))) fail("--git-history 需要 Git 仓库");
    const objectLines = run("git", ["-C", repositoryRoot, "rev-list", "--objects", "--all"])
      .split("\n")
      .filter(Boolean);
    historyObjects = objectLines.length;
    for (const line of objectLines) {
      const name = line.includes(" ") ? line.slice(line.indexOf(" ") + 1) : "";
      if (!name) continue;
      const segments = portable(name).split("/");
      if (
        forbiddenExact.has(portable(name))
        || segments.some((segment) => forbiddenSegments.has(segment))
        || forbiddenExtensions.has(extname(name).toLowerCase())
        || (segments[0] === "docs" && segments[1] === "agents")
        || segments[0] === "artifacts"
      ) {
        fail(`Git 历史对象包含禁止路径 ${name}`);
      }
    }
    commits = Number(run("git", ["-C", repositoryRoot, "rev-list", "--count", "--all"]).trim());
    if (hasFlag("--single-commit") && commits !== 1) fail(`公开初始历史应只有 1 个提交，实际为 ${commits}`);
  }

  console.log(JSON.stringify({
    status: "passed",
    files: relativeFiles.length,
    scannedTextFiles,
    markdownLinks: markdownLinks.length,
    forbiddenFiles: 0,
    absoluteMachinePaths: 0,
    internalTaskLabels: 0,
    suspectedCredentials: 0,
    historyObjects,
    commits,
  }, null, 2));
} finally {
  if (temporaryRoot) rmSync(temporaryRoot, { recursive: true, force: true });
}
