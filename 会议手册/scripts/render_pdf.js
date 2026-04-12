const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");

async function main() {
  const [, , htmlPath, pdfPath] = process.argv;
  if (!htmlPath || !pdfPath) {
    throw new Error("Usage: node render_pdf.js <input-html> <output-pdf>");
  }

  const chromePath =
    process.env.CHROME_PATH ||
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

  const browser = await chromium.launch({
    headless: true,
    executablePath: chromePath,
    args: [
      "--allow-file-access-from-files",
      "--disable-web-security",
      "--font-render-hinting=medium",
    ],
  });

  const page = await browser.newPage({
    viewport: { width: 1280, height: 1800 },
    deviceScaleFactor: 1,
  });

  await page.goto(pathToFileURL(path.resolve(htmlPath)).href, {
    waitUntil: "networkidle",
  });

  try {
    await page.waitForFunction(() => window.__HANDBOOK_READY__ === true, {
      timeout: 20000,
    });
  } catch (error) {
    console.warn("Math rendering wait timed out, continuing with current page state.");
  }

  await page.emulateMedia({ media: "print" });
  await page.pdf({
    path: path.resolve(pdfPath),
    width: "210mm",
    height: "297mm",
    margin: {
      top: "0",
      right: "0",
      bottom: "0",
      left: "0",
    },
    printBackground: true,
  });

  await browser.close();
  console.log(`Wrote ${path.resolve(pdfPath)}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
