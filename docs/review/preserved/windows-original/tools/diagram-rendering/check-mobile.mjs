import path from "node:path";
import { pathToFileURL } from "node:url";
import puppeteer from "puppeteer";

const root = path.resolve(import.meta.dirname, "../..");
const diagrams = [
  "auditor-workflow",
  "evidence-relationship-map",
  "approval-review-states",
];
const widths = [320, 390];

const browser = await puppeteer.launch({
  executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
  headless: true,
});

try {
  for (const width of widths) {
    const page = await browser.newPage();
    await page.setViewport({ width, height: 844, deviceScaleFactor: 1 });
    for (const name of diagrams) {
      const source = path.join(
        root,
        "docs",
        "diagrams",
        "presentation",
        "html",
        `${name}.html`,
      );
      await page.goto(pathToFileURL(source).href, { waitUntil: "load" });
      const result = await page.evaluate(() => ({
        innerWidth: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        svgWidth: document.querySelector("svg")?.getBoundingClientRect().width ?? 0,
      }));
      if (result.scrollWidth > result.innerWidth || result.svgWidth > result.innerWidth) {
        throw new Error(`${name} overflows at ${width}px: ${JSON.stringify(result)}`);
      }
      console.log(`${name}: ${width}px PASS`);
    }

    const guide = path.join(root, "ACE_PROGRESS_GUIDE.html");
    await page.goto(pathToFileURL(guide).href, { waitUntil: "load" });
    await page.evaluate(() =>
      document.querySelector("[aria-labelledby=diagram-title]")?.scrollIntoView(),
    );
    await page.waitForFunction(() =>
      [...document.querySelectorAll("[aria-labelledby=diagram-title] img")].every(
        (image) => image.complete && image.naturalWidth > 0,
      ),
    );
    const guideResult = await page.evaluate(() => ({
      innerWidth: window.innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      imageCount: document.querySelectorAll("[aria-labelledby=diagram-title] img").length,
    }));
    if (guideResult.scrollWidth > guideResult.innerWidth || guideResult.imageCount !== 4) {
      throw new Error(`Progress guide fails at ${width}px: ${JSON.stringify(guideResult)}`);
    }
    console.log(`ACE Progress Guide diagrams: ${width}px PASS`);
    await page.close();
  }
} finally {
  await browser.close();
}
