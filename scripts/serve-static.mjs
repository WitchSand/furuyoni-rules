#!/usr/bin/env node

import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize, resolve, sep } from "node:path";

function argument(name, fallback) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

const directoryName = argument("--dir", "dist");
const port = Number(argument("--port", "4321"));
const requestedBase = argument("--base", "/");
const base = requestedBase === "/"
  ? "/"
  : `/${requestedBase}`.replace(/\/{2,}/g, "/").replace(/\/+$/g, "") + "/";
if (!/^[a-zA-Z0-9._-]+$/.test(directoryName) || !directoryName.startsWith("dist")) {
  throw new Error(`静态目录必须是以 dist 开头的仓库根目录单层目录，收到：${directoryName}`);
}
if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error(`端口无效：${port}`);
const root = resolve(directoryName);
if (!existsSync(root)) throw new Error(`${root} 不存在，请先构建`);

const types = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".wasm": "application/wasm",
  ".webp": "image/webp",
};

createServer((request, response) => {
  const pathname = decodeURIComponent(new URL(request.url ?? "/", "http://localhost").pathname);
  if (base !== "/" && !pathname.startsWith(base)) {
    const notFound = join(root, "404.html");
    response.statusCode = 404;
    response.setHeader("Content-Type", types[".html"]);
    createReadStream(notFound).pipe(response);
    return;
  }
  const routedPath = base === "/" ? pathname : pathname.slice(base.length - 1);
  const safe = normalize(routedPath).replace(/^([/\\])+/, "");
  let file = resolve(root, safe);
  if (!file.startsWith(`${root}${sep}`) && file !== root) {
    response.writeHead(403).end("Forbidden");
    return;
  }
  if (existsSync(file) && statSync(file).isDirectory()) file = join(file, "index.html");
  if (!existsSync(file) && !extname(file)) file = join(file, "index.html");
  if (!existsSync(file) || !statSync(file).isFile()) {
    file = join(root, "404.html");
    response.statusCode = 404;
  }
  response.setHeader("Content-Type", types[extname(file)] ?? "application/octet-stream");
  response.setHeader("Cache-Control", "no-store");
  createReadStream(file).pipe(response);
}).listen(port, "127.0.0.1", () => {
  console.log(`静态站点：http://127.0.0.1:${port}${base} （${directoryName}）`);
});
