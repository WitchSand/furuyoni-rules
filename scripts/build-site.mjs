#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { existsSync, readdirSync, rmSync } from "node:fs";

function argument(name, fallback) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

function normalizeBase(value) {
  const clean = `/${value}`.replace(/\/{2,}/g, "/").replace(/\/+$/g, "");
  return clean === "" ? "/" : clean === "/" ? "/" : `${clean}/`;
}

function run(command, args, env = process.env) {
  const result = spawnSync(command, args, { stdio: "inherit", env });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}

const base = normalizeBase(argument("--base", "/"));
const outDir = argument("--out-dir", "dist");
const siteOrigin = process.env.SITE_ORIGIN || "https://witchsand.github.io";
if (!/^[a-zA-Z0-9._-]+$/.test(outDir) || !outDir.startsWith("dist")) {
  throw new Error(`输出目录必须是仓库根目录下以 dist 开头的单层目录，收到：${outDir}`);
}
const parsedOrigin = new URL(siteOrigin);
if (parsedOrigin.protocol !== "https:" || parsedOrigin.origin !== parsedOrigin.href.replace(/\/$/u, "")) {
  throw new Error(`SITE_ORIGIN 必须是无路径的 HTTPS origin，收到：${siteOrigin}`);
}

const env = {
  ...process.env,
  ASTRO_TELEMETRY_DISABLED: "1",
  SITE_BASE: base,
  SITE_OUT_DIR: outDir,
  SITE_ORIGIN: parsedOrigin.origin,
};

console.log(`清理旧输出目录：${outDir}`);
rmSync(outDir, { recursive: true, force: true, maxRetries: 20, retryDelay: 100 });
if (existsSync(outDir)) {
  const restoredEntries = readdirSync(outDir);
  if (restoredEntries.length > 0) {
    throw new Error(`输出目录在清理后被外部进程恢复：${outDir}/${restoredEntries.join(`、${outDir}/`)}`);
  }
}

console.log(`Astro 静态构建：base=${base} outDir=${outDir}`);
run("node_modules/.bin/astro", ["build"], env);

console.log("Pagefind extended 建立简中／日文全文索引");
run("node_modules/.bin/pagefind", [
  "--site",
  outDir,
  "--output-subdir",
  "pagefind",
  "--force-language",
  "zh",
]);

console.log("扫描静态路由、资源路径、外部运行时依赖与受限素材");
run(process.execPath, ["scripts/audit-static-build.mjs", "--dir", outDir, "--base", base], env);
