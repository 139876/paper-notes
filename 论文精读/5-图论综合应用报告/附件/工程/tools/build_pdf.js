// 报告 Markdown -> PDF（pandoc -> HTML -> MathJax -> Chrome 打印）
// 用法: node tools/build_pdf.js <input.md> <output.pdf>
const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const PANDOC = "/opt/anaconda3/bin/pandoc";
const MATHJAX = path.join(ROOT, "tools/vendor/mathjax/tex-svg.js");

const CSS = `
@page { size: A4; margin: 20mm 18mm 18mm 18mm; }
html { -webkit-print-color-adjust: exact; }
body {
  font-family: "Songti SC", "PingFang SC", "Heiti SC", "STSong", serif;
  font-size: 10.5pt; line-height: 1.75; color: #1a1a1a; margin: 0;
  text-align: justify;
}
h1, h2, h3, h4 {
  font-family: "PingFang SC", "Heiti SC", "Helvetica Neue", sans-serif;
  color: #16324f; line-height: 1.4; page-break-after: avoid;
}
h1 { font-size: 20pt; margin: 0 0 14pt; padding-bottom: 7pt;
     border-bottom: 2.2pt solid #16324f; page-break-before: always; text-align: center; }
h2 { font-size: 14.5pt; margin: 20pt 0 9pt; padding-left: 8pt;
     border-left: 4pt solid #2e7d9e; }
h3 { font-size: 12pt; margin: 15pt 0 7pt; color: #2e5c7a; }
h4 { font-size: 11pt; margin: 12pt 0 6pt; }
p { margin: 0 0 8pt; }
strong { color: #0d2b45; }
table { border-collapse: collapse; width: 100%; margin: 10pt 0 14pt;
        font-size: 9pt; page-break-inside: avoid; }
th { background: #16324f; color: #fff; font-weight: 600; padding: 5pt 7pt;
     border: 0.6pt solid #16324f; text-align: left; }
td { padding: 4.5pt 7pt; border: 0.5pt solid #b8c4d0; vertical-align: top; }
tr:nth-child(even) td { background: #f4f7fa; }
img { max-width: 100%; height: auto; display: block; margin: 10pt auto 4pt;
      page-break-inside: avoid; }
code { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 9pt;
       background: #eef2f6; padding: 1pt 3pt; border-radius: 3pt; }
pre { background: #f4f6f8; border-left: 3pt solid #2e7d9e; padding: 8pt 10pt;
      overflow-x: auto; font-size: 8.5pt; line-height: 1.5; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
blockquote { border-left: 3.5pt solid #d9a441; background: #fdf9ef;
             margin: 10pt 0; padding: 8pt 12pt; color: #4a3c1c; page-break-inside: avoid; }
blockquote p { margin: 0 0 5pt; }
hr { border: none; border-top: 0.6pt solid #ccd6e0; margin: 16pt 0; }
ul, ol { margin: 0 0 8pt; padding-left: 22pt; }
li { margin: 2pt 0; }
.mjx-container { margin: 8pt 0 !important; }
code.md-math-block { display: block; text-align: center; }
`;

async function main() {
  const input = path.resolve(process.argv[2]);
  const output = path.resolve(process.argv[3]);
  const htmlPath = output.replace(/\.pdf$/, ".html");

  execFileSync(PANDOC, [
    input, "-f", "markdown+raw_html+tex_math_dollars", "-t", "html5",
    "--standalone", "--metadata", "title=基于图论的重庆大学虎溪校区快递配送路径优化研究",
    "--css", path.join(__dirname, "report.css"),
    "-o", htmlPath,
  ], { stdio: "inherit" });

  // 注入 MathJax（本地，离线可用）
  let html = fs.readFileSync(htmlPath, "utf8");
  const mj = fs.readFileSync(MATHJAX, "utf8");
  html = html.replace("</body>", `
<script>
window.MathJax = { tex: { inlineMath: [['$','$']], displayMath: [['$$','$$']] },
                    svg: { fontCache: 'global' }, startup: { typeset: true } };
</script>
<script>${mj}</script>
</body>`);
  fs.writeFileSync(htmlPath, html);

  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto("file://" + htmlPath, { waitUntil: "networkidle" });
  await page.waitForFunction(
    () => window.MathJax && window.MathJax.startup && window.MathJax.startup.document,
    null, { timeout: 30000 });
  await page.waitForTimeout(2500);

  await page.pdf({
    path: output,
    format: "A4",
    printBackground: true,
    margin: { top: "18mm", bottom: "16mm", left: "16mm", right: "16mm" },
    displayHeaderFooter: true,
    headerTemplate: `<div style="font-size:7pt;color:#8a97a5;width:100%;
      padding:0 16mm;display:flex;justify-content:space-between;">
      <span>基于图论的重庆大学虎溪校区快递配送路径优化研究</span>
      <span>图论综合应用报告</span></div>`,
    footerTemplate: `<div style="font-size:7.5pt;color:#8a97a5;width:100%;
      padding:0 16mm;display:flex;justify-content:center;">
      <span class="pageNumber"></span> / <span class="totalPages"></span></div>`,
  });
  await browser.close();
  console.log("[pdf] " + output);
}

main().catch((e) => { console.error(e); process.exit(1); });
