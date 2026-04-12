const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");

async function main() {
  const [, , htmlPath, pngPath, pdfPath] = process.argv;
  if (!htmlPath || !pngPath || !pdfPath) {
    throw new Error("Usage: node render_poster.js <input-html> <output-png> <output-pdf>");
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
    viewport: { width: 1000, height: 1400 },
    deviceScaleFactor: 2,
  });

  await page.goto(pathToFileURL(path.resolve(htmlPath)).href, {
    waitUntil: "networkidle",
  });

  const poster = page.locator(".poster-page");
  await poster.screenshot({
    path: path.resolve(pngPath),
    type: "png",
    scale: "device",
  });

  const wrapperHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>
    @page { size: 210mm 297mm; margin: 0; }
    html, body { margin: 0; padding: 0; width: 210mm; height: 297mm; background: #f6f0e7; }
    img { display: block; width: 210mm; height: 297mm; }
  </style>
</head>
<body>
  <img src="${pathToFileURL(path.resolve(pngPath)).href}" alt="ICCM 2026 Poster">
</body>
</html>`;

  const wrapperPath = path.resolve(path.dirname(pdfPath), `${path.parse(pdfPath).name}_print.html`);
  fs.writeFileSync(wrapperPath, wrapperHtml, "utf8");

  const pdfPage = await browser.newPage({
    viewport: { width: 1000, height: 1400 },
    deviceScaleFactor: 1,
  });
  await pdfPage.goto(pathToFileURL(wrapperPath).href, {
    waitUntil: "networkidle",
  });
  await pdfPage.emulateMedia({ media: "screen" });
  await pdfPage.pdf({
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
  fs.unlinkSync(wrapperPath);

  console.log(`Wrote ${path.resolve(pngPath)}`);
  console.log(`Wrote ${path.resolve(pdfPath)}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
