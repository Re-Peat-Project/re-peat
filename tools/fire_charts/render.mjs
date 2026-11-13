// Draw the charts of the national fire-by-land-status summary with D3 and save each as PNG and SVG.
//   node re-peat/tools/fire_charts/render.mjs --data <figdata.json> --style report|slides --out <dir> --prefix fig_
// figdata.json is written by re-peat/tools/fire_landstatus_figs.py. The page (charts_<style>.html, next to the data) is kept:
// open it in a browser to see every chart. D3 is the copy vendored in repeat-prioritisation; Chrome is driven with the
// playwright-core of repeat-dashboard (set PLAYWRIGHT_FROM to another package.json to use another install).
// Prints one line per chart: name <tab> png path.
import fs from 'node:fs'
import path from 'node:path'
import { createRequire } from 'node:module'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const ws = path.resolve(here, '../../..')
const arg = (k, d) => { const i = process.argv.indexOf(`--${k}`); return i > 0 ? process.argv[i + 1] : d }
const data = path.resolve(arg('data'))
const style = arg('style', 'report')
const out = path.resolve(arg('out'))
const prefix = arg('prefix', 'fig_')
const require = createRequire(process.env.PLAYWRIGHT_FROM || path.join(ws, 'repeat-dashboard/app/package.json'))
const { chromium } = require('playwright-core')

const FONTS = {
  report: { family: 'Source Sans 3', dir: path.join(ws, 're-peat/reports/project_report/fonts'), files: { 400: 'SourceSans3-Regular.ttf', 600: 'SourceSans3-Semibold.ttf', 700: 'SourceSans3-Bold.ttf' } },
  slides: { family: 'Plus Jakarta Sans', dir: path.join(ws, '_slides/fonts'), files: { 400: 'PlusJakartaSans-Regular.ttf', 600: 'PlusJakartaSans-SemiBold.ttf', 700: 'PlusJakartaSans-Bold.ttf' } },
}
const f = FONTS[style]
const faces = Object.entries(f.files).map(([w, file]) => `@font-face{font-family:'${f.family}';font-weight:${w};src:url('${pathToFileURL(path.join(f.dir, file)).href}')}`).join('\n')
const d3 = pathToFileURL(path.join(ws, 'repeat-prioritisation/src/repeat_prioritisation/national/assets/d3.v7.9.0.min.js')).href
const charts = pathToFileURL(path.join(here, 'charts.js')).href
const html = `<!doctype html><html><head><meta charset="utf-8"><title>Fire by land status: charts (${style})</title>
<style>${faces}
body{margin:16px;background:#fff;color:#0b0b0b;font-family:'${f.family}',sans-serif}
figure{margin:0 0 28px}figcaption{font-size:12px;color:#52514e;margin-bottom:6px}
</style>
<script src="${d3}"></script>
<script>window.DATA=${fs.readFileSync(data, 'utf8')};window.STYLE=${JSON.stringify({ kind: style, font: f.family })};</script>
</head><body><script src="${charts}"></script></body></html>`
const page_file = path.join(path.dirname(data), `charts_${style}.html`)
fs.writeFileSync(page_file, html)

const browser = await chromium.launch({ channel: 'chrome' })
const page = await browser.newPage({ deviceScaleFactor: style === 'report' ? 3 : 2.5, viewport: { width: 1400, height: 900 } })
const errors = []
page.on('pageerror', (e) => errors.push(String(e)))
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
await page.goto(pathToFileURL(page_file).href)
await page.waitForFunction('window.__done === true', null, { timeout: 60000 }).catch(() => {})
if (errors.length) { console.error(errors.join('\n')); await browser.close(); process.exit(1) }
fs.mkdirSync(out, { recursive: true })
const svgDir = path.join(path.dirname(data), `svg_${style}`)
fs.mkdirSync(svgDir, { recursive: true })
for (const el of await page.$$('svg[data-name]')) {
  const name = await el.getAttribute('data-name')
  const png = path.join(out, `${prefix}${name}.png`)
  await el.screenshot({ path: png, omitBackground: false })
  fs.writeFileSync(path.join(svgDir, `${name}.svg`), await el.evaluate((n) => n.outerHTML))
  console.log(`${name}\t${png}`)
}
await browser.close()
