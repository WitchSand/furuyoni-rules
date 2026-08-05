import { defineConfig } from "astro/config";

const base = process.env.SITE_BASE || "/";
const outDirName = process.env.SITE_OUT_DIR || "dist";
const site = process.env.SITE_ORIGIN || "https://witchsand.github.io";

export default defineConfig({
  output: "static",
  site,
  base,
  outDir: `./${outDirName}`,
  trailingSlash: "always",
  build: {
    format: "directory",
    assets: "_assets",
  },
  compressHTML: true,
  vite: {
    build: {
      cssMinify: true,
    },
  },
});
