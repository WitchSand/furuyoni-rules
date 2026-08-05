import { defineConfig } from "@playwright/test";

const useBundledChromium = process.env.PLAYWRIGHT_CHANNEL === "chromium";
const pagesDirectory = process.env.PAGES_DIST_DIR || "dist-subpath";

export default defineConfig({
  testDir: "tests/e2e",
  outputDir: "test-results",
  timeout: 30_000,
  expect: { timeout: 8_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"], ["html", { outputFolder: "playwright-report", open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:4321",
    ...(useBundledChromium ? {} : { channel: "chrome" }),
    viewport: { width: 1440, height: 900 },
    colorScheme: "light",
    locale: "zh-CN",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "node scripts/serve-static.mjs --dir dist --port 4321",
      url: "http://127.0.0.1:4321/",
      reuseExistingServer: true,
      timeout: 15_000,
    },
    {
      command: `node scripts/serve-static.mjs --dir ${pagesDirectory} --base /furuyoni-rules/ --port 4322`,
      url: "http://127.0.0.1:4322/furuyoni-rules/",
      reuseExistingServer: true,
      timeout: 15_000,
    },
  ],
});
