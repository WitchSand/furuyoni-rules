#!/usr/bin/env node

import { spawnSync } from "node:child_process";

function run(command, args, env = process.env) {
  console.log(`\n==> ${command} ${args.join(" ")}`);
  const result = spawnSync(command, args, { stdio: "inherit", env });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}

const auditArgs = ["scripts/audit-public-source.mjs"];
if (process.argv.includes("--git-history")) auditArgs.push("--git-history");
if (process.argv.includes("--single-commit")) auditArgs.push("--single-commit");

run(process.execPath, auditArgs);
run("npm", ["audit", "--omit=dev", "--audit-level=high"]);
run("npm", ["test"]);
run("npm", ["run", "check"]);
run("npm", ["run", "build"]);
run("npm", ["run", "build:pages"]);
run("npm", ["run", "test:e2e"], { ...process.env, PAGES_DIST_DIR: "dist-pages" });

console.log("\n公开发布门禁全部通过");
