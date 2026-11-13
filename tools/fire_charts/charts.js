// Charts of the national fire-by-land-status summary, drawn with D3 v7 into one page (rendered by render.mjs).
// Data: window.DATA (figdata.json from re-peat/tools/fire_landstatus_figs.py). Style: window.STYLE.kind = report | slides.
// Palette: the validated dashboard palette (dataviz reference); ramps validated as ordinal (light end clears the surface).
/* global d3 */
(async () => {
  const S = window.STYLE, D = window.DATA, F = D.facts, NOW = D.now, PAST = D.past
  const R = S.kind === 'report'
  const fs = R ? 11 : 17, fsS = fs - 1.5, fsT = fs - 2.5
  const C = { ink: '#0b0b0b', ink2: '#52514e', muted: '#898781', grid: '#e1e0d9', base: '#c3c2b7', track: '#ecebe6',
    orange: '#eb6834', blue: '#2a78d6', green: '#008300', magenta: '#e87ba4', violet: '#6250d6', aqua: '#1baf7a', red: '#e34948', yellow: '#eda100' }
  const SEQ = ['#f4a172', '#ee7a45', '#d9592a', '#a8410f', '#6e2a08']           // orange ramp, validated ordinal
  const BLUES = ['#86b6ef', '#3987e5', '#1c5cab', '#0d366b']                      // blue ramp, validated ordinal
  const RATE_BR = [10, 20, 40, 80]
  const TYPES = [['sawit', 'Oil palm', C.orange], ['pphtr', 'Plantation forest (PPHTR)', C.violet], ['tambang', 'Mining', C.red], ['pbph', 'Forest concession (PBPH)', C.aqua], ['none', 'No concession', C.blue]]
  const TYPE = Object.fromEntries(TYPES.map(([k, l, c]) => [k, { label: l, color: c }]))
  const FUN = [['cons', 'Conservation'], ['hl', 'Protection'], ['prod', 'Production'], ['hpk', 'Convertible'], ['apl', 'APL'], ['other', 'Water, undefined']]
  const FUNL = Object.fromEntries(FUN)
  const GROUP = { kawasan: 'Forest area', apl: 'Other land use (APL)', other: 'Water, undefined' }
  const DARK = new Set(['#d9592a', '#a8410f', '#6e2a08', '#1c5cab', '#0d366b', C.blue, C.violet, C.red, C.green, C.orange])
  const inkOn = (c) => (DARK.has(c) ? '#fff' : C.ink)
  const f0 = d3.format(',.0f'), kfmt = (v) => (v >= 1e4 ? `${f0(v / 1e3)}k` : f0(v))
  const rateCol = (r, br = RATE_BR, ramp = SEQ) => (Number.isFinite(r) ? ramp[d3.bisectRight(br, r)] : C.track)
  await document.fonts.load(`400 12px '${S.font}'`); await document.fonts.load(`600 12px '${S.font}'`)

  function chart(name, title, w, h) {
    const fig = d3.select('body').append('figure')
    fig.append('figcaption').text(`${name}: ${title}`)
    const svg = fig.append('svg').attr('data-name', name).attr('xmlns', 'http://www.w3.org/2000/svg').attr('width', w).attr('height', h)
      .attr('viewBox', `0 0 ${w} ${h}`).style('font-family', `'${S.font}', sans-serif`)
    svg.append('rect').attr('width', w).attr('height', h).attr('fill', '#fff')
    return svg
  }
  const size = (rw, rh, sw = 880, sh = 520) => (R ? [rw, rh] : [sw, sh])
  function txt(g, x, y, s, o = {}) {
    const t = g.append('text').attr('x', x).attr('y', y).attr('font-size', o.size ?? fsS).attr('fill', o.fill ?? C.ink).attr('text-anchor', o.anchor ?? 'start')
      .attr('dominant-baseline', o.base ?? 'middle').attr('font-weight', o.weight ?? 400).text(s)
    if (o.halo) t.attr('stroke', '#fff').attr('stroke-width', 3).attr('paint-order', 'stroke').attr('stroke-linejoin', 'round')
    return t
  }
  const tw = (t) => t.node().getComputedTextLength()
  function hbar(g, x, y, len, h, col, r = 3) {          // rounded data end, square at the baseline
    if (!(len > 0)) return
    const q = Math.min(r, len, h / 2)
    g.append('path').attr('fill', col).attr('d', `M${x},${y}H${x + len - q}Q${x + len},${y} ${x + len},${y + q}V${y + h - q}Q${x + len},${y + h} ${x + len - q},${y + h}H${x}Z`)
  }
  function axis(sel) {
    sel.selectAll('text').attr('font-size', fsT).attr('fill', C.muted).style('font-family', `'${S.font}', sans-serif`)
    sel.selectAll('.domain').attr('stroke', C.base)
    sel.selectAll('.tick line').attr('stroke', C.grid)
    return sel
  }
  function legend(g, items, x, y, gap = 14) {
    let xx = x
    for (const [l, c, dash] of items) {
      if (dash !== undefined) g.append('line').attr('x1', xx).attr('x2', xx + 16).attr('y1', y).attr('y2', y).attr('stroke', c).attr('stroke-width', 2).attr('stroke-dasharray', dash || null)
      else g.append('rect').attr('x', xx).attr('y', y - 5).attr('width', 10).attr('height', 10).attr('rx', 2).attr('fill', c)
      const t = txt(g, xx + (dash !== undefined ? 20 : 14), y, l, { size: fsT, fill: C.ink2 })
      xx += (dash !== undefined ? 20 : 14) + tw(t) + gap
    }
    return xx
  }
  function rateLegend(g, x, y, title, br = RATE_BR, ramp = SEQ, extra = []) {
    txt(g, x, y, title, { size: fsT, fill: C.ink2, weight: 600 })
    const labs = [`< ${br[0]}`, ...br.slice(0, -1).map((b, i) => `${b}–${br[i + 1]}`), `≥ ${br.at(-1)}`]
    legend(g, [...extra, ...labs.map((l, i) => [l, ramp[i]])], x, y + fsT + 6, 10)
  }
  function gridY(g, y, x0, x1, ticks = 4, f = kfmt) {
    for (const v of y.ticks(ticks)) {
      g.append('line').attr('x1', x0).attr('x2', x1).attr('y1', y(v)).attr('y2', y(v)).attr('stroke', C.grid)
      txt(g, x0 - 6, y(v), f(v), { anchor: 'end', size: fsT, fill: C.muted })
    }
  }
  function line(g, pts, x, y, col, dash) {
    g.append('path').datum(pts).attr('fill', 'none').attr('stroke', col).attr('stroke-width', 2).attr('stroke-linejoin', 'round').attr('stroke-linecap', 'round')
      .attr('stroke-dasharray', dash || null).attr('d', d3.line().x((d) => x(d[0])).y((d) => y(d[1])))
    const e = pts.at(-1)
    g.append('circle').attr('cx', x(e[0])).attr('cy', y(e[1])).attr('r', 4).attr('fill', col).attr('stroke', '#fff').attr('stroke-width', 2)
  }

  // ---- 1 shares: does each class carry more fire than its share of the land? ----
  {
    const [w, h] = size(640, 300, 880, 430)
    const svg = chart('shares', 'share of the land against share of the fire, and hotspot density inside each class against the rest of the land', w, h)
    const M = [['land_pct', 'share of the land', C.muted], ['burned_pct', `burned area ${PAST[0]}–${PAST[1]}`, C.blue], ['viirs26_pct', `hotspots ${NOW}`, C.orange]]
    const cls = [['peat', 'Peat'], ['conc', 'Concessions'], ['kawasan', 'Forest area']]   // DMPG: like-for-like in dmpg_years
      .map(([k, n]) => ({ k, n, c: F.classes[k] })).sort((a, b) => b.c.rate26 / b.c.rate26_outside - a.c.rate26 / a.c.rate26_outside)
    const L = R ? 120 : 170, top = R ? 80 : 112, rh = (h - top - (R ? 26 : 34)) / cls.length
    const xa = d3.scaleLinear([0, 70], [L, L + (w - L) * 0.47]), xb = d3.scaleLinear([0, 200], [xa(70) + (R ? 70 : 96), w - (R ? 86 : 118)])
    txt(svg, L, 10, 'Share of Indonesia\'s total (%)', { weight: 600, size: fsS })
    txt(svg, xb(0), 10, `Hotspots ${NOW} per 100 km²`, { weight: 600, size: fsS })
    let lx = L
    M.forEach(([, lab, col], i) => {
      if (i === 0) svg.append('circle').attr('cx', lx + 5).attr('cy', 32).attr('r', 5).attr('fill', '#fff').attr('stroke', col).attr('stroke-width', 2)
      else svg.append('circle').attr('cx', lx + 5).attr('cy', 32).attr('r', 5).attr('fill', col)
      const t = txt(svg, lx + 14, 32, lab, { size: fsT, fill: C.ink2 }); lx += 14 + tw(t) + 14
    })
    for (const v of [0, 20, 40, 60]) { svg.append('line').attr('x1', xa(v)).attr('x2', xa(v)).attr('y1', top - 10).attr('y2', top + cls.length * rh - 6).attr('stroke', C.grid); txt(svg, xa(v), top + cls.length * rh + 6, `${v}%`, { anchor: 'middle', size: fsT, fill: C.muted }) }
    for (const v of [0, 50, 100, 150, 200]) { svg.append('line').attr('x1', xb(v)).attr('x2', xb(v)).attr('y1', top - 10).attr('y2', top + cls.length * rh - 6).attr('stroke', C.grid); txt(svg, xb(v), top + cls.length * rh + 6, v, { anchor: 'middle', size: fsT, fill: C.muted }) }
    let lx2 = xb(0)
    ;[['inside the class', C.orange], ['rest of the land', C.base]].forEach(([lab, col]) => { svg.append('rect').attr('x', lx2).attr('y', (R ? 50 : 66) - 5).attr('width', 10).attr('height', 10).attr('rx', 2).attr('fill', col); const t = txt(svg, lx2 + 14, R ? 50 : 66, lab, { size: fsT, fill: C.ink2 }); lx2 += 14 + tw(t) + 14 })
    cls.forEach(({ n, c }, i) => {
      const y = top + i * rh + rh * 0.35
      txt(svg, L - 12, y - fs * 0.35, n, { anchor: 'end', weight: 600 })
      txt(svg, L - 12, y + fs * 0.75, `${c.land_mha.toFixed(1)} Mha`, { anchor: 'end', size: fsT, fill: C.muted })
      const hi = Math.max(c.burned_pct, c.viirs26_pct), lo = Math.min(c.land_pct, c.burned_pct)
      svg.append('line').attr('x1', xa(lo)).attr('x2', xa(hi)).attr('y1', y).attr('y2', y).attr('stroke', C.base).attr('stroke-width', 2)
      svg.append('circle').attr('cx', xa(c.land_pct)).attr('cy', y).attr('r', R ? 6 : 8).attr('fill', '#fff').attr('stroke', C.muted).attr('stroke-width', 2)
      svg.append('circle').attr('cx', xa(c.burned_pct)).attr('cy', y).attr('r', R ? 6 : 8).attr('fill', C.blue).attr('stroke', '#fff').attr('stroke-width', 1.5)
      svg.append('circle').attr('cx', xa(c.viirs26_pct)).attr('cy', y).attr('r', R ? 6 : 8).attr('fill', C.orange).attr('stroke', '#fff').attr('stroke-width', 1.5)
      txt(svg, xa(c.land_pct), y + (R ? 15 : 21), `${Math.round(c.land_pct)}%`, { anchor: 'middle', size: fsT, fill: C.muted, halo: true })
      const right = Math.max(c.land_pct, c.burned_pct, c.viirs26_pct)
      txt(svg, xa(right) + (R ? 11 : 14), y, `${Math.round(c.burned_pct)}% · ${Math.round(c.viirs26_pct)}%`, { size: fsT, fill: C.ink2, halo: true })
      const bh = R ? 7 : 10
      ;[[c.rate26, C.orange, -bh - 1], [c.rate26_outside, C.base, 1]].forEach(([r, col, dy]) => {
        hbar(svg, xb(0), y + dy, xb(r) - xb(0), bh, col)
        txt(svg, xb(r) + 5, y + dy + bh / 2, Math.round(r), { size: fsT, fill: C.ink2 })
      })
      txt(svg, w - 4, y, `${(c.rate26 / c.rate26_outside).toFixed(1)}× the rest`, { anchor: 'end', size: fsS, weight: 600, fill: c.rate26 / c.rate26_outside >= 2 ? C.ink : C.ink2 })
    })
  }

  // ---- 2 months: 2026 against the 2015-2025 mean ----
  {
    const [w, h] = size(620, 250, 900, 480)
    const svg = chart('months_2026', 'VIIRS hotspots per month: 2026, 2015 and the 2015-2025 mean', w, h)
    const m = { l: 46, r: R ? 120 : 190, t: 26, b: 26 }
    const ms = Object.keys(F.month26).map(Number).sort((a, b) => a - b)
    const x = d3.scalePoint(ms, [m.l, w - m.r])
    const y = d3.scaleLinear().domain([0, d3.max(ms, (k) => Math.max(F.month26[k], F.month_mean_past[k], F.month2015[k] || 0))]).nice().range([h - m.b, m.t])
    gridY(svg, y, m.l, w - m.r)
    const mon = (k) => new Date(2026, k - 1, 1).toLocaleString('en-GB', { month: 'short' })
    ms.forEach((k) => txt(svg, x(k), h - m.b + 14, mon(k), { anchor: 'middle', size: fsT, fill: C.muted }))
    line(svg, ms.map((k) => [k, F.month_mean_past[k]]), x, y, C.muted, '5 3')
    line(svg, ms.map((k) => [k, F.month2015[k] || 0]), x, y, C.violet)
    line(svg, ms.map((k) => [k, F.month26[k]]), x, y, C.orange)
    const e = ms.at(-1)
    txt(svg, x(e) + 9, y(F.month2015[e] || 0), '2015', { size: fsT, fill: C.ink2, weight: 600 })
    txt(svg, x(e) + 9, y(F.month26[e]), `${NOW}`, { size: fsS, weight: 600 })
    txt(svg, x(e) + 9, y(F.month_mean_past[e]), `mean ${PAST[0]}–${PAST[1]}`, { size: fsT, fill: C.ink2 })
    const p = F.peak_month
    txt(svg, x(p), y(F.month26[p]) - 12, `${kfmt(F.month26[p])} in ${new Date(2026, p - 1, 1).toLocaleString('en-GB', { month: 'long' })}`, { anchor: 'end', size: fsT, fill: C.ink })
  }

  // ---- 3 years: VIIRS per year, same window, inside and outside concessions ----
  {
    const [w, h] = size(620, 250, 640, 480)
    const svg = chart('years', 'VIIRS hotspots per year, 1 Jan to 31 Oct', w, h)
    const m = { l: 46, r: R ? 110 : 170, t: 18, b: 26 }
    const x = d3.scaleLinear(d3.extent(D.years, (d) => d.year), [m.l, w - m.r])
    const y = d3.scaleLinear().domain([0, d3.max(D.years, (d) => d.out)]).nice().range([h - m.b, m.t])
    gridY(svg, y, m.l, w - m.r)
    D.years.filter((d) => d.year % 2 === 0).forEach((d) => txt(svg, x(d.year), h - m.b + 14, d.year, { anchor: 'middle', size: fsT, fill: C.muted }))
    for (const [k, col, lab] of [['out', C.blue, 'Outside concessions'], ['conc', C.orange, 'In concessions']]) {
      line(svg, D.years.map((d) => [d.year, d[k]]), x, y, col)
      const e = D.years.at(-1)
      txt(svg, x(e.year) + 9, y(e[k]), lab, { size: fsT, fill: C.ink })
    }
  }

  // ---- 4 burned area per year, inside and outside concessions (incomplete years marked) ----
  {
    const [w, h] = size(620, 250, 640, 480)
    const svg = chart('burned_years', 'burned area per year', w, h)
    const m = { l: 52, r: 34, t: 30, b: 26 }
    const x = d3.scaleLinear(d3.extent(D.burned, (d) => d.year), [m.l, w - m.r])
    const y = d3.scaleLinear().domain([0, d3.max(D.burned, (d) => d.out) / 1e3]).nice().range([h - m.b, m.t])
    for (const yr of [2024, NOW]) {
      svg.append('rect').attr('x', x(yr) - 9).attr('y', m.t).attr('width', 18).attr('height', h - m.b - m.t).attr('fill', C.track)
      txt(svg, x(yr), m.t - 7, 'incomplete', { anchor: 'middle', size: fsT - 1, fill: C.muted })
    }
    gridY(svg, y, m.l, w - m.r, 4, (v) => `${f0(v)}k`)
    D.burned.filter((d) => d.year % 2 === 1).forEach((d) => txt(svg, x(d.year), h - m.b + 14, d.year, { anchor: 'middle', size: fsT, fill: C.muted }))
    line(svg, D.burned.map((d) => [d.year, d.out / 1e3]), x, y, C.blue)
    line(svg, D.burned.map((d) => [d.year, d.conc / 1e3]), x, y, C.orange)
    legend(svg, [['Outside concessions', C.blue], ['In concessions', C.orange]], m.l + 140, m.t - 16)
    txt(svg, m.l - 6, m.t - 16, 'thousand ha', { anchor: 'end', size: fsT, fill: C.muted })
  }

  // ---- 5 rates by class ----
  {
    const groups = [...new Set(F.rates.map((r) => r.group))]
    const n = F.rates.length
    const [w, h] = size(620, 22 * n + 90, 700, 520)
    const svg = chart('rates', `VIIRS hotspots ${NOW} per 100 km2 by class`, w, h)
    const L = R ? 170 : 210
    const x = d3.scaleLinear([0, d3.max(F.rates, (r) => r.rate) * 1.08], [L, w - 34])
    const step = (h - 40 - groups.length * 22) / n, bh = Math.min(R ? 12 : 16, step * 0.66)
    for (const v of x.ticks(5)) { svg.append('line').attr('x1', x(v)).attr('x2', x(v)).attr('y1', 8).attr('y2', h - 34).attr('stroke', C.grid); txt(svg, x(v), h - 22, v, { anchor: 'middle', size: fsT, fill: C.muted }) }
    let y = 8
    for (const g of groups) {
      txt(svg, 8, y + 9, g, { size: fsS, weight: 600, fill: C.ink })
      y += 22
      for (const r of F.rates.filter((q) => q.group === g).sort((a, b) => b.rate - a.rate)) {
        hbar(svg, x(0), y + (step - bh) / 2, x(r.rate) - x(0), bh, C.orange)
        txt(svg, x(0) - 6, y + step / 2, r.label, { anchor: 'end', size: fsT, fill: C.ink2 })
        txt(svg, x(r.rate) + 4, y + step / 2, f0(r.rate), { size: fsT, fill: C.ink })
        y += step
      }
    }
    svg.append('line').attr('x1', x(F.rate26)).attr('x2', x(F.rate26)).attr('y1', 8).attr('y2', h - 34).attr('stroke', C.ink).attr('stroke-dasharray', '3 3')
    txt(svg, x(F.rate26) + 4, h - 40, `Indonesia, all land: ${f0(F.rate26)}`, { size: fsT, halo: true })
    txt(svg, (L + w) / 2, h - 6, `VIIRS hotspots ${NOW} per 100 km²`, { anchor: 'middle', size: fsT, fill: C.ink2 })
  }

  // ---- 6 province map ----
  {
    const [w, h] = size(620, 330, 820, 520)
    const svg = chart('map_2026', `VIIRS hotspots ${NOW} per 100 km2 of land by province`, w, h)
    const rate = new Map(F.provinces.map((p) => [p.province, p.rate]))
    const proj = d3.geoIdentity().reflectY(true).fitExtent([[6, 34], [w - 6, h - 40]], D.provinces_geo)
    const path = d3.geoPath(proj)
    const br = [5, 15, 40, 80]
    svg.append('g').selectAll('path').data(D.provinces_geo.features).join('path').attr('d', path)
      .attr('fill', (d) => rateCol(rate.get(d.properties.province) ?? 0, br)).attr('stroke', '#fff').attr('stroke-width', 0.6)
    const top = [...D.provinces_geo.features].sort((a, b) => (rate.get(b.properties.province) ?? 0) - (rate.get(a.properties.province) ?? 0)).slice(0, 4)
    for (const f of top) {
      const [cx, cy] = path.centroid(f), up = cy < h * 0.5
      const ty = up ? 26 : h - 34, tx = Math.min(w - 70, Math.max(70, cx))
      svg.append('line').attr('x1', cx).attr('y1', cy).attr('x2', tx).attr('y2', up ? ty + 4 : ty - 10).attr('stroke', C.ink2).attr('stroke-width', 0.7)
      txt(svg, tx, up ? ty - 2 : ty, `${f.properties.province} ${f0(rate.get(f.properties.province))}`, { anchor: 'middle', size: fsT, halo: true })
    }
    rateLegend(svg, w - (R ? 290 : 380), h - 26, `VIIRS hotspots ${NOW} per 100 km²`, br)
  }

  // ---- 7 provinces: hotspots inside and outside concessions ----
  {
    const P = F.provinces.slice(0, 10)
    const [w, h] = size(620, 300, 480, 520)
    const svg = chart('provinces', `provinces with the most VIIRS hotspots ${NOW}`, w, h)
    const L = R ? 130 : 150
    const x = d3.scaleLinear([0, d3.max(P, (p) => p.viirs26) * 1.3], [L, w - 10])
    const head = 2 * fsT + 18
    const step = (h - head - 30) / P.length, bh = Math.min(R ? 13 : 18, step * 0.66)
    P.forEach((p, i) => {
      const y = head + i * step + (step - bh) / 2, c = p.viirs26 * (p.conc_pct ?? 0) / 100
      hbar(svg, x(0), y, x(c) - x(0), bh, C.orange, 0)
      hbar(svg, x(c) + 2, y, x(p.viirs26) - x(c) - 2, bh, C.blue)
      txt(svg, x(0) - 6, y + bh / 2, p.province, { anchor: 'end', size: fsT, fill: C.ink2 })
      txt(svg, x(p.viirs26) + 4, y + bh / 2, `${kfmt(p.viirs26)} · ${f0(p.conc_pct)}%`, { size: fsT })
    })
    legend(svg, [['In concessions', C.orange], ['Outside', C.blue]], L, 10)
    txt(svg, L, 10 + fsT + 8, 'Labels: hotspots · share in concessions', { size: fsT, fill: C.muted })
    const ax = svg.append('g').attr('transform', `translate(0,${h - 22})`).call(d3.axisBottom(x).ticks(4).tickFormat(kfmt).tickSize(0))
    axis(ax).select('.domain').remove()
  }

  // ---- 8 DMPG dumbbell ----
  {
    const P = F.dmpg_by_province
    const [w, h] = size(620, 40 + 26 * P.length)
    const svg = chart('dmpg', `VIIRS hotspots ${NOW} per 100 km2 of peat, DMPG villages and other peat`, w, h)
    const L = R ? 130 : 170
    const x = d3.scaleLinear([0, d3.max(P, (p) => Math.max(p.dmpg_rate, p.other_rate)) * 1.05], [L, w - 20])
    const step = (h - 46) / P.length
    for (const v of x.ticks(5)) { svg.append('line').attr('x1', x(v)).attr('x2', x(v)).attr('y1', 22).attr('y2', h - 24).attr('stroke', C.grid); txt(svg, x(v), h - 12, v, { anchor: 'middle', size: fsT, fill: C.muted }) }
    ;[...P].reverse().forEach((p, i) => {
      const y = 28 + i * step + step / 2
      svg.append('line').attr('x1', x(p.other_rate)).attr('x2', x(p.dmpg_rate)).attr('y1', y).attr('y2', y).attr('stroke', C.base).attr('stroke-width', 2)
      svg.append('circle').attr('cx', x(p.other_rate)).attr('cy', y).attr('r', 5).attr('fill', C.blue).attr('stroke', '#fff').attr('stroke-width', 2)
      svg.append('circle').attr('cx', x(p.dmpg_rate)).attr('cy', y).attr('r', 5).attr('fill', C.magenta).attr('stroke', '#fff').attr('stroke-width', 2)
      txt(svg, L - 8, y, p.province, { anchor: 'end', size: fsT, fill: C.ink2 })
    })
    legend(svg, [['DMPG village peat', C.magenta], ['Other peat', C.blue]], L, 10)
  }

  // ---- 8b DMPG village peat against other peat in the same provinces, every year (same window) ----
  {
    const P = F.dmpg_years, y0 = F.dmpg_first_year
    const [w, h] = size(640, 300, 880, 470)
    const svg = chart('dmpg_years', `VIIRS hotspots per 100 km² of peat, DMPG villages and other peat in the same ${F.dmpg_years_provinces} provinces, 1 January to the last ${NOW} date`, w, h)
    const m = { l: 46, r: R ? 128 : 178, t: R ? 46 : 66, b: 26 }
    const x = d3.scaleLinear(d3.extent(P, (p) => p.year), [m.l, w - m.r])
    const y = d3.scaleLinear([0, d3.max(P, (p) => p.dmpg_rate) * 1.12], [h - m.b, m.t]).nice()
    svg.append('rect').attr('x', m.l).attr('y', m.t - 4).attr('width', x(y0) - m.l).attr('height', h - m.b - m.t + 4).attr('fill', C.track)
    gridY(svg, y, m.l, w - m.r, 4, (v) => v)
    P.forEach((p) => { if (p.year % 2 === 1 || p.year === NOW) txt(svg, x(p.year), h - m.b + 14, p.year, { anchor: 'middle', size: fsT, fill: C.muted }) })
    txt(svg, (m.l + x(y0)) / 2, m.t + 4, 'Before DMPG', { anchor: 'middle', size: fsT, fill: C.ink2, weight: 600 })
    svg.append('line').attr('x1', x(y0)).attr('x2', x(y0)).attr('y1', m.t - 4).attr('y2', h - m.b).attr('stroke', C.ink2).attr('stroke-dasharray', '3 3')
    txt(svg, x(y0) + 6, m.t + 4, `${y0}: first DMPG villages`, { size: fsT, fill: C.ink2 })
    line(svg, P.map((p) => [p.year, p.other_rate]), x, y, C.blue)
    line(svg, P.map((p) => [p.year, p.dmpg_rate]), x, y, C.magenta)
    P.filter((p) => p.other_rate >= 10).forEach((p) => {
      svg.append('circle').attr('cx', x(p.year)).attr('cy', y(p.dmpg_rate)).attr('r', 4).attr('fill', C.magenta).attr('stroke', '#fff').attr('stroke-width', 2)
      svg.append('circle').attr('cx', x(p.year)).attr('cy', y(p.other_rate)).attr('r', 4).attr('fill', C.blue).attr('stroke', '#fff').attr('stroke-width', 2)
      const last = p.year === NOW
      txt(svg, x(p.year) + (last ? -10 : 0), y(p.dmpg_rate) - (last ? 0 : R ? 12 : 16), `${(p.dmpg_rate / p.other_rate).toFixed(1)}×`, { anchor: last ? 'end' : 'middle', size: fsS, weight: 600, halo: true })
    })
    const e = P.at(-1)
    txt(svg, w - m.r + 10, y(e.dmpg_rate), 'DMPG village peat', { size: fsS, weight: 600 })
    txt(svg, w - m.r + 10, y(e.dmpg_rate) + fsS + 4, `${F.dmpg_years_mha[0].toFixed(1)} Mha`, { size: fsT, fill: C.muted })
    txt(svg, w - m.r + 10, y(e.other_rate), 'Other peat', { size: fsS, weight: 600 })
    txt(svg, w - m.r + 10, y(e.other_rate) + fsS + 4, `${F.dmpg_years_mha[1].toFixed(1)} Mha`, { size: fsT, fill: C.muted })
    legend(svg, [['DMPG village peat', C.magenta], ['Other peat, same provinces', C.blue]], m.l, 10)
    txt(svg, m.l, 10 + fsT + 10, `Labels: DMPG peat against other peat in fire years. Hotspots per 100 km², 1 January to ${new Date(F.window_end).toLocaleString('en-GB', { day: 'numeric', month: 'long' })} each year`, { size: fsT, fill: C.muted })
  }

  // ---- 9 mosaic (Marimekko): forest group x concession, all land and peat ----
  {
    const [w, h] = size(620, 330)
    const svg = chart('mosaic', 'land by forest group and concession; colour = hotspots per 100 km2', w, h)
    const pw = (w - 24) / 2, top = 22, bot = 70, ph = h - top - bot
    ;[['all', 'All land'], ['peat', 'Peat']].forEach(([basis, title], pi) => {
      const g = svg.append('g').attr('transform', `translate(${8 + pi * (pw + 8)},0)`)
      const cells = D.mosaic.filter((c) => c.basis === basis)
      const tot = d3.sum(cells, (c) => c.area_ha)
      txt(g, 0, 10, `${title} · ${(tot / 1e6).toFixed(1)} Mha`, { size: fsS, weight: 600 })
      let x = 0
      for (const grp of ['kawasan', 'apl', 'other']) {
        const gc = cells.filter((c) => c.group === grp), ga = d3.sum(gc, (c) => c.area_ha)
        if (!ga) continue
        const cw = pw * ga / tot
        let y = top
        for (const conc of [true, false]) {
          const c = gc.find((q) => q.conc === conc)
          if (!c) continue
          const ch = ph * c.area_ha / ga, r = c.n / c.area_ha * 1e4, col = rateCol(r)
          g.append('rect').attr('x', x + 1).attr('y', y + 1).attr('width', Math.max(cw - 2, 0.5)).attr('height', Math.max(ch - 2, 0.5)).attr('fill', col)
          if (cw > 64 && ch > 40) {
            txt(g, x + 6, y + 13, conc ? 'Concession' : 'No concession', { size: fsT, fill: inkOn(col), weight: 600 })
            txt(g, x + 6, y + 13 + fsT + 3, `${f0(r)} per 100 km²`, { size: fsT, fill: inkOn(col) })
            txt(g, x + 6, y + 13 + 2 * (fsT + 3), `${(c.area_ha / 1e6).toFixed(1)} Mha`, { size: fsT, fill: inkOn(col) })
          }
          y += ch
        }
        if (cw > 50) txt(g, x + cw / 2, top + ph + 12, GROUP[grp], { anchor: 'middle', size: fsT, fill: C.ink2 })
        if (cw > 50) txt(g, x + cw / 2, top + ph + 12 + fsT + 2, `${f0(100 * ga / tot)}%`, { anchor: 'middle', size: fsT, fill: C.muted })
        x += cw
      }
    })
    rateLegend(svg, 8, h - 26, `VIIRS hotspots ${NOW} per 100 km² (width = land in the forest group, height = share in concessions)`)
  }

  // ---- 10 treemap: concession type, then forest function; size = land, colour = hotspot density ----
  {
    const [w, h] = size(620, 420)
    const svg = chart('treemap', 'land by concession type and forest function; colour = hotspots per 100 km2', w, h)
    const kids = TYPES.map(([k, l]) => ({ name: k, children: D.hier.filter((d) => d.type === k && d.area_ha > 0).map((d) => ({ name: d.fun, area: d.area_ha, n: d.n })) }))
    const root = d3.hierarchy({ children: kids }).sum((d) => d.area ?? 0).sort((a, b) => b.value - a.value)
    d3.treemap().size([w, h - 50]).paddingOuter(2).paddingTop(fsS + 8).paddingInner(2).tile(d3.treemapSquarify)(root)
    for (const p of root.children) {
      for (const s of [`${TYPE[p.data.name].label} · ${(p.value / 1e6).toFixed(1)} Mha`, TYPE[p.data.name].label.replace(/ \(.*\)/, ''), '']) {   // longest label that fits
        if (!s) break
        const t = txt(svg, p.x0 + 4, p.y0 + fsS / 2 + 3, s, { size: fsS, weight: 600 })
        if (tw(t) <= p.x1 - p.x0 - 8) break
        t.remove()
      }
      for (const l of p.children) {
        const r = l.data.n / l.data.area * 1e4, col = rateCol(r), cw = l.x1 - l.x0, ch = l.y1 - l.y0
        svg.append('rect').attr('x', l.x0).attr('y', l.y0).attr('width', cw).attr('height', ch).attr('fill', col)
          .append('title').text(`${TYPE[p.data.name].label}, ${FUNL[l.data.name]}: ${(l.data.area / 1e6).toFixed(2)} Mha, ${f0(r)} per 100 km²`)
        if (cw > 58 && ch > 30) {
          txt(svg, l.x0 + 4, l.y0 + 10, FUNL[l.data.name], { size: fsT, fill: inkOn(col) })
          txt(svg, l.x0 + 4, l.y0 + 10 + fsT + 2, f0(r), { size: fsT, fill: inkOn(col), weight: 600 })
        }
      }
    }
    rateLegend(svg, 4, h - 28, `VIIRS hotspots ${NOW} per 100 km² (box size = land)`)
  }

  // ---- 11 concession types: hotspots, density and the forest functions inside each type ----
  {
    const FC = { cons: C.green, hl: C.aqua, prod: C.violet, hpk: C.magenta, apl: C.yellow, other: C.muted }
    const rows = TYPES.map(([k, l, c]) => {
      const hs = D.hier.filter((d) => d.type === k)
      return { k, l, c, n: d3.sum(hs, (d) => d.n), area: d3.sum(hs, (d) => d.area_ha), fun: FUN.map(([f]) => [f, d3.sum(hs.filter((d) => d.fun === f), (d) => d.n)]) }
    }).sort((a, b) => b.n - a.n)
    const tot = d3.sum(rows, (r) => r.n), area = d3.sum(rows, (r) => r.area), all = tot / area * 1e4
    const L = R ? 160 : 270, top = R ? 74 : 104, rh = R ? 40 : 58
    const [w, h] = size(640, top + rows.length * rh + 26, 900, top + rows.length * rh + 34)
    const svg = chart('types', `VIIRS hotspots ${NOW} by concession type: number, density and forest function`, w, h)
    const W = w - L, wa = W * 0.27, wb = W * 0.27
    const xa = d3.scaleLinear([0, d3.max(rows, (r) => r.n) * 1.75], [L, L + wa - 16])
    const xb = d3.scaleLinear([0, d3.max(rows, (r) => r.n / r.area * 1e4) * 1.2], [L + wa + 10, L + wa + wb - 16])
    const xc = d3.scaleLinear([0, 100], [L + wa + wb + 10, w - 8])
    ;[[xa(0), 'Hotspots'], [xb(0), 'Per 100 km²'], [xc(0), 'Forest function']].forEach(([x, t]) => txt(svg, x, 10, t, { weight: 600, size: fsS }))
    const colw = (xc(100) - xc(0)) / 2
    FUN.forEach(([f, l], i) => {
      const y = 28 + Math.floor(i / 2) * (fsT + 5), x = xc(0) + (i % 2) * colw
      svg.append('rect').attr('x', x).attr('y', y - 5).attr('width', 10).attr('height', 10).attr('rx', 2).attr('fill', FC[f])
      txt(svg, x + 14, y, l.replace('Water, undefined', 'Water, undef.'), { size: fsT - 0.5, fill: C.ink2 })
    })
    svg.append('line').attr('x1', xb(all)).attr('x2', xb(all)).attr('y1', top - 8).attr('y2', top + rows.length * rh - 8).attr('stroke', C.ink2).attr('stroke-dasharray', '3 3')
    txt(svg, xb(all), top + rows.length * rh + 4, `all land ${all.toFixed(0)}`, { anchor: 'middle', size: fsT, fill: C.ink2 })
    rows.forEach((r, i) => {
      const y = top + i * rh, bh = rh * 0.5, cy = y + bh / 2
      svg.append('rect').attr('x', 8).attr('y', cy - 5).attr('width', 10).attr('height', 10).attr('rx', 2).attr('fill', r.c)
      txt(svg, 24, cy, r.l, { size: fsS })
      hbar(svg, xa(0), y, xa(r.n) - xa(0), bh, r.c)
      txt(svg, xa(r.n) + 5, cy, `${kfmt(r.n)} · ${100 * r.n / tot < 1 ? '<1' : Math.round(100 * r.n / tot)}%`, { size: fsT, fill: C.ink2 })
      const d = r.n / r.area * 1e4
      svg.append('line').attr('x1', xb(0)).attr('x2', xb(d)).attr('y1', cy).attr('y2', cy).attr('stroke', C.base).attr('stroke-width', 2)
      svg.append('circle').attr('cx', xb(d)).attr('cy', cy).attr('r', R ? 5 : 7).attr('fill', r.c)
      txt(svg, xb(d) + 9, cy, d.toFixed(0), { size: fsT, fill: C.ink2 })
      let x = xc(0)
      r.fun.forEach(([f, n]) => {
        const len = (xc(100) - xc(0)) * n / r.n
        if (len > 0) svg.append('rect').attr('x', x).attr('y', y).attr('width', Math.max(0, len - 1.5)).attr('height', bh).attr('fill', FC[f]).append('title').text(`${FUNL[f]}: ${f0(n)}`)
        if (len > 34) txt(svg, x + len / 2, cy, `${Math.round(100 * n / r.n)}%`, { anchor: 'middle', size: fsT - 1, fill: ['apl', 'hl', 'hpk'].includes(f) ? C.ink : '#fff' })
        x += len
      })
    })
  }

  // ---- 11b concessions as donuts: share of the land, of the burned area and of the 2026 hotspots ----
  {
    const c = F.classes.conc
    const parts = [['Land', c.land_pct, `${c.land_mha.toFixed(1)} of ${(c.land_mha / c.land_pct * 100).toFixed(0)} Mha`],
      [`Burned area ${PAST[0]}–${PAST[1]}`, c.burned_pct, `${c.burned_mha.toFixed(2)} of ${(c.burned_mha / c.burned_pct * 100).toFixed(2)} Mha`],
      [`Hotspots ${NOW}`, c.viirs26_pct, `${kfmt(c.viirs26)} of ${kfmt(c.viirs26 / c.viirs26_pct * 100)}`]]
    const [w, h] = size(640, 250, 620, 330)
    const svg = chart('conc_donuts', `share inside concessions: land, burned area ${PAST[0]}-${PAST[1]} and hotspots ${NOW}`, w, h)
    const r = Math.min(h * 0.3, w / 8), cw = w / 3
    legend(svg, [['inside concessions', C.orange], ['outside', C.track]], 8, 12)
    parts.forEach(([lab, p, sub], i) => {
      const cx = cw * i + cw / 2, cy = h * 0.5
      const g = svg.append('g').attr('transform', `translate(${cx},${cy})`)
      const arc = d3.arc().innerRadius(r * 0.62).outerRadius(r)
      g.append('path').attr('d', arc({ startAngle: 0, endAngle: 2 * Math.PI })).attr('fill', C.track)
      g.append('path').attr('d', arc({ startAngle: 0, endAngle: 2 * Math.PI * p / 100 })).attr('fill', C.orange)
      txt(g, 0, 0, `${Math.round(p)}%`, { anchor: 'middle', size: fs + 6, weight: 600 })
      txt(svg, cx, cy + r + (R ? 16 : 22), lab, { anchor: 'middle', size: fsS, weight: 600 })
      txt(svg, cx, cy + r + (R ? 30 : 42), sub, { anchor: 'middle', size: fsT, fill: C.ink2 })
    })
  }

  // ---- 12 alluvial: burned area 2015-2025, forest group -> concession type -> peat ----
  {
    const [w, h] = size(620, 400)
    const svg = chart('alluvial', `burned area ${PAST[0]}–${PAST[1]} by forest group, concession type and peat`, w, h)
    const colsDef = [['kawasan', 'apl', 'other'], TYPES.map(([k]) => k), ['peat', 'nopeat', 'unknown']]
    const lab = { ...GROUP, ...Object.fromEntries(TYPES.map(([k, l]) => [k, l])), peat: 'Peat', nopeat: 'Not peat', unknown: 'Peat not mapped' }
    const colr = { kawasan: C.green, apl: C.yellow, other: C.base, ...Object.fromEntries(TYPES.map(([k, , c]) => [k, c])), peat: C.violet, nopeat: C.base, unknown: C.track }
    const flows = D.flows
    const node = (ci) => {           // node totals: sources of the first step, then targets of each step (a middle node counted once)
      const m = new Map()
      for (const f of flows) {
        if (ci === 0 && f.step === 0) m.set(f.s, (m.get(f.s) ?? 0) + f.v)
        if (ci > 0 && f.step === ci - 1) m.set(f.t, (m.get(f.t) ?? 0) + f.v)
      }
      return m
    }
    const T = d3.sum(flows.filter((f) => f.step === 0), (f) => f.v)
    const top = 24, H = h - top - 10, gapPx = 10
    const xs = [R ? 120 : 160, w / 2, w - (R ? 120 : 170)], nw = 10
    const pos = {}
    const nPresent = colsDef.map((order, ci) => order.filter((k) => (node(ci).get(k) ?? 0) > 0).length)
    const k = (H - gapPx * (Math.max(...nPresent) - 1)) / T          // one scale for every column, so ribbons keep their width
    colsDef.forEach((order, ci) => {
      const vals = node(ci), present = order.filter((q) => (vals.get(q) ?? 0) > 0)
      let y = top
      for (const key of present) { const hh = vals.get(key) * k; pos[`${ci}:${key}`] = { y0: y, y1: y + hh, out: y, inn: y, k }; y += hh + gapPx }
    })
    for (const step of [0, 1]) {
      for (const s of colsDef[step]) for (const t of colsDef[step + 1]) {
        const f = flows.find((q) => q.step === step && q.s === s && q.t === t)
        const ps = pos[`${step}:${s}`], pt = pos[`${step + 1}:${t}`]
        if (!f || !ps || !pt) continue
        const hh = f.v * ps.k, ya = ps.out, yb = pt.inn
        ps.out += hh; pt.inn += hh
        const x0 = xs[step] + nw / 2, x1 = xs[step + 1] - nw / 2, xm = (x0 + x1) / 2
        svg.append('path').attr('fill', colr[s]).attr('fill-opacity', 0.35)
          .attr('d', `M${x0},${ya}C${xm},${ya} ${xm},${yb} ${x1},${yb}V${yb + hh}C${xm},${yb + hh} ${xm},${ya + hh} ${x0},${ya + hh}Z`)
          .append('title').text(`${lab[s]} → ${lab[t]}: ${(f.v / 1e6).toFixed(2)} Mha`)
      }
    }
    for (const [key, p] of Object.entries(pos)) {
      const [ci, k] = key.split(':'), c = Number(ci)
      svg.append('rect').attr('x', xs[c] - nw / 2).attr('y', p.y0).attr('width', nw).attr('height', Math.max(1, p.y1 - p.y0)).attr('fill', colr[k])
      if (p.y1 - p.y0 > fsT) {
        const v = `${lab[k]} ${((p.y1 - p.y0) / p.k / 1e6).toFixed(2)} Mha`
        txt(svg, c === 0 ? xs[c] - nw : xs[c] + nw, (p.y0 + p.y1) / 2, v, { anchor: c === 0 ? 'end' : 'start', size: fsT, halo: c === 1 })
      }
    }
    ;['Forest area', 'Concession type', 'Peat'].forEach((t, i) => txt(svg, xs[i], 10, t, { anchor: 'middle', size: fsS, weight: 600, fill: C.ink2 }))
  }

  // ---- 13 heatmap: province x year ----
  {
    const land = D.heat_land
    const rate = new Map(D.heat.map((d) => [`${d.province}|${d.year}`, d.rate]))
    const years = [...new Set(D.heat.map((d) => d.year))].sort((a, b) => a - b)
    const islMean = d3.rollup(land, (v) => d3.mean(v, (d) => rate.get(`${d.province}|${NOW}`) ?? 0), (d) => d.island)
    const islands = [...islMean.keys()].sort((a, b) => islMean.get(b) - islMean.get(a))
    const rows = islands.flatMap((i) => land.filter((d) => d.island === i).sort((a, b) => (rate.get(`${b.province}|${NOW}`) ?? 0) - (rate.get(`${a.province}|${NOW}`) ?? 0)))
    const ch = R ? 13 : 16, L = R ? 140 : 170, gapI = 8
    const [w, h] = [R ? 620 : 880, 34 + rows.length * ch + islands.length * gapI + 50]
    const svg = chart('heatmap', `VIIRS hotspots per 100 km2 of land, province by year (1 Jan to 31 Oct)`, w, h)
    const cw = (w - L - 90) / years.length
    const br = [1, 3, 10, 30, 100], ramp = [C.track, ...SEQ]
    years.forEach((y, i) => txt(svg, L + i * cw + cw / 2, 14, y === NOW ? y : `'${String(y).slice(2)}`, { anchor: 'middle', size: fsT, fill: y === NOW ? C.ink : C.muted, weight: y === NOW ? 600 : 400 }))
    let y = 26, prev = null
    for (const r of rows) {
      if (r.island !== prev) { if (prev) y += gapI; txt(svg, L + years.length * cw + 8, y + ch / 2, r.island.replace('Pulau ', ''), { size: fsT, fill: C.ink2, weight: 600 }); prev = r.island }
      txt(svg, L - 6, y + ch / 2, r.province, { anchor: 'end', size: fsT - 0.5, fill: C.ink2 })
      years.forEach((yr, i) => {
        const v = rate.get(`${r.province}|${yr}`) ?? 0
        svg.append('rect').attr('x', L + i * cw + 1).attr('y', y + 1).attr('width', cw - 2).attr('height', ch - 2).attr('fill', ramp[d3.bisectRight(br, v)])
          .append('title').text(`${r.province} ${yr}: ${v.toFixed(1)}`)
      })
      y += ch
    }
    const xi = L + years.indexOf(NOW) * cw
    svg.append('rect').attr('x', xi).attr('y', 24).attr('width', cw).attr('height', y - 22).attr('fill', 'none').attr('stroke', C.ink).attr('stroke-width', 1.2)
    rateLegend(svg, L, y + 22, 'VIIRS hotspots per 100 km² of land, 1 January to 31 October', br, ramp)
  }

  // ---- 14 KHG bubbles ----
  {
    const K = D.khg
    const [w, h] = size(620, 380)
    const svg = chart('khg_bubbles', `KHG: land against VIIRS hotspots ${NOW} per 100 km2`, w, h)
    const m = { l: 54, r: R ? 150 : 190, t: 34, b: 40 }
    const x = d3.scaleLog(d3.extent(K, (d) => d.km2), [m.l, w - m.r]).nice()
    const y = d3.scaleLog([Math.max(0.1, d3.min(K, (d) => d.rate)), d3.max(K, (d) => d.rate)], [h - m.b, m.t]).nice()
    const rs = d3.scaleSqrt([0, d3.max(K, (d) => d.n)], [1.5, R ? 22 : 28])
    for (const v of y.ticks(5).filter((v) => [0.1, 1, 10, 100, 1000].includes(v))) { svg.append('line').attr('x1', m.l).attr('x2', w - m.r).attr('y1', y(v)).attr('y2', y(v)).attr('stroke', C.grid); txt(svg, m.l - 6, y(v), v, { anchor: 'end', size: fsT, fill: C.muted }) }
    for (const v of x.ticks().filter((v) => [10, 100, 1000, 10000].includes(v))) txt(svg, x(v), h - m.b + 14, f0(v), { anchor: 'middle', size: fsT, fill: C.muted })
    txt(svg, (m.l + w) / 2, h - 8, 'KHG land (km², log scale)', { anchor: 'middle', size: fsT, fill: C.ink2 })
    txt(svg, m.l - 6, m.t - 14, `hotspots ${NOW} per 100 km² (log)`, { size: fsT, fill: C.ink2 })
    const br = [10, 25, 50]
    svg.append('g').selectAll('circle').data([...K].sort((a, b) => b.n - a.n)).join('circle').attr('cx', (d) => x(d.km2)).attr('cy', (d) => y(Math.max(d.rate, 0.1)))
      .attr('r', (d) => rs(d.n)).attr('fill', (d) => BLUES[d3.bisectRight(br, d.conc_pct)]).attr('fill-opacity', 0.9).attr('stroke', '#fff').attr('stroke-width', 1)
      .append('title').text((d) => `${d.name}: ${f0(d.n)} hotspots, ${d.rate.toFixed(0)} per 100 km², ${f0(d.conc_pct)}% in concessions`)
    svg.append('line').attr('x1', m.l).attr('x2', w - m.r).attr('y1', y(F.rate26)).attr('y2', y(F.rate26)).attr('stroke', C.ink).attr('stroke-dasharray', '3 3')
    txt(svg, w - m.r, y(F.rate26) - 7, `Indonesia ${f0(F.rate26)}`, { anchor: 'end', size: fsT, halo: true })
    // the eight KHG with the most hotspots: labels in a column right of the plot, spread so they never overlap, with leader lines
    const top8 = [...K].sort((a, b) => b.n - a.n).slice(0, 8).map((d) => ({ d, ly: y(d.rate) })).sort((a, b) => a.ly - b.ly)
    const lh = fsT + 4
    top8.forEach((t, i) => { if (i) t.ly = Math.max(t.ly, top8[i - 1].ly + lh) })
    const over = top8.at(-1).ly - (h - m.b)
    if (over > 0) top8.forEach((t) => { t.ly -= over })
    const lx = w - m.r + 14
    for (const t of top8) {
      svg.append('line').attr('x1', x(t.d.km2) + rs(t.d.n) * 0.7).attr('y1', y(t.d.rate)).attr('x2', lx - 3).attr('y2', t.ly).attr('stroke', C.muted).attr('stroke-width', 0.6)
      txt(svg, lx, t.ly, `${t.d.name} · ${(t.d.n / 1e3).toFixed(t.d.n >= 1e4 ? 0 : 1)}k`, { size: fsT - 0.5 })
    }
    rateLegend(svg, m.l + 200, 12, 'share of hotspots in concessions', br.map((b) => b), BLUES)
    svg.selectAll('text').filter(function () { return /^< 10$|^10–25$|^25–50$|^≥ 50$/.test(this.textContent) }).text(function () { return this.textContent + '%' })
  }

  // ---- 15 repeated burns: share of each class burned 1, 2, 3, 4+ times; share of the land burned twice or more ----
  {
    const TB = ['#f4a172', '#d9592a', '#a8410f', '#6e2a08']                    // 1, 2, 3, 4+ times (validated ordinal)
    const T = D.times, tot = D.times_total, tot2 = tot[2] + tot[3] + tot[4], totA = d3.sum(tot)
    const rows = [
      ...[[true, 'kawasan'], [true, 'apl'], [false, 'kawasan'], [false, 'apl']].map(([c, g]) => ({ r: T.find((d) => d.set === 'conc' && d.conc === c && d.group === g), label: `${c ? 'Concession' : 'No concession'} · ${g === 'kawasan' ? 'forest area' : 'APL'}`, sec: 0 })),
      ...[true, false].map((d) => ({ r: T.find((x) => x.set === 'dmpg' && x.dmpg === d), label: d ? 'DMPG village peat' : 'Other peat', sec: 1 }))]
    const L = R ? 150 : 210, top = R ? 54 : 84, rh = R ? 30 : 46, gap = R ? 18 : 26, ly = R ? 30 : 46
    const [w, h] = size(640, top + rows.length * rh + gap + 34, 880, top + rows.length * rh + gap + 44)
    const svg = chart('repeat', 'land burned once, twice, three and four or more times in 2015-2026, and shares of the land burned twice or more', w, h)
    const xa = [L, L + (w - L) * 0.52], xb = [xa[1] + 34, w - 40]
    const pc = (r) => r.ha.slice(1).map((v) => 100 * v / d3.sum(r.ha))
    const maxA = d3.max(rows, (o) => d3.sum(pc(o.r)))
    const a = d3.scaleLinear().domain([0, maxA * 1.12]).range(xa)
    const maxB = d3.max(rows, (o) => Math.max(100 * (o.r.ha[2] + o.r.ha[3] + o.r.ha[4]) / tot2, 100 * d3.sum(o.r.ha) / totA))
    const b = d3.scaleLinear().domain([0, maxB * 1.08]).range(xb)
    txt(svg, xa[0], 12, 'Share of the land burned (% of the class)', { weight: 600, size: fsT })
    txt(svg, xb[0], 12, 'Share of land burned 2+ times (%)', { weight: 600, size: fsT })
    legend(svg, [['1 time', TB[0]], ['2', TB[1]], ['3', TB[2]], ['4 or more', TB[3]]], xa[0], ly, 10)
    const lx2 = legend(svg, [['burned 2+ times', TB[2]]], xb[0], ly, 10) + 4
    svg.append('line').attr('x1', lx2).attr('x2', lx2).attr('y1', ly - 6).attr('y2', ly + 6).attr('stroke', C.ink).attr('stroke-width', 2)
    txt(svg, lx2 + 6, ly, 'land', { size: fsT, fill: C.ink2 })
    rows.forEach((o, i) => {
      const y = top + i * rh + o.sec * gap, bh = rh * 0.56, yb = y + (rh - bh) / 2
      if (i === 4) svg.append('line').attr('x1', 8).attr('x2', w - 8).attr('y1', y - gap / 2).attr('y2', y - gap / 2).attr('stroke', C.grid)
      txt(svg, L - 10, y + rh / 2, o.label, { anchor: 'end', size: fsS })
      let x0 = xa[0]
      pc(o.r).forEach((p, k) => { const len = a(p) - a(0); svg.append('rect').attr('x', x0).attr('y', yb).attr('width', Math.max(0, len - (len > 2 ? 1 : 0))).attr('height', bh).attr('fill', TB[k]); x0 += len })
      txt(svg, x0 + 6, y + rh / 2, `${d3.sum(pc(o.r)).toFixed(1)}%`, { size: fsT, fill: C.ink2 })
      const s2 = 100 * (o.r.ha[2] + o.r.ha[3] + o.r.ha[4]) / tot2, sl = 100 * d3.sum(o.r.ha) / totA
      hbar(svg, b(0), yb, b(s2) - b(0), bh, TB[2])
      svg.append('line').attr('x1', b(sl)).attr('x2', b(sl)).attr('y1', yb - 3).attr('y2', yb + bh + 3).attr('stroke', C.ink).attr('stroke-width', 2)
      const lx = b(sl) > b(s2) && b(sl) < b(s2) + 36 ? b(sl) + 6 : b(s2) + 6
      txt(svg, lx, y + rh / 2, `${s2.toFixed(0)}%`, { size: fsT, fill: C.ink2, halo: true })
    })
    const yAx = top + rows.length * rh + gap + 4
    axis(svg.append('g').attr('transform', `translate(0,${yAx})`).call(d3.axisBottom(a).ticks(4).tickFormat((v) => `${v}%`).tickSizeOuter(0)))
    axis(svg.append('g').attr('transform', `translate(0,${yAx})`).call(d3.axisBottom(b).ticks(4).tickFormat((v) => `${v}%`).tickSizeOuter(0)))
  }

  // ---- 16-19: the KLH priority area and who covers it (only when the PPEG summary is present) ----
  if (D.prio) {
    const TB16 = ['#f4a172', '#d9592a', '#a8410f', '#6e2a08']
    const P = D.prio, mh = (v) => `${(v / 1e6).toFixed(2)} Mha`, pc = (v, t) => `${Math.round(100 * v / t)}%`
    const ACTC = [C.orange, C.violet, C.green, C.blue]
    const ACTL = ['Licence holders, inside licences', 'Licence holders and communities, 5 km buffer', 'Ministry of Forestry, forest area', 'KLH/BPLH, APL']
    // 16 parts of the priority area: one 100% bar per attribute, segments labelled directly
    {
      const khgN = P.khg_both + P.khg_villages_only + P.khg_skeg_only
      const rows = [
        ['Priority KHG', `${khgN} KHG`, [['in target villages and damaged peat', P.khg_both, C.blue], ['target villages only', P.khg_villages_only, C.aqua], ['damaged peat only', P.khg_skeg_only, C.orange]], (v) => String(v)],
        ['SKEG damage class', mh(P.ha), [['light', P.damage[0], TB16[0]], ['moderate', P.damage[1], TB16[1]], ['heavy', P.damage[2], TB16[2]], ['very heavy', P.damage[3], TB16[3]], ['outside KHG, no class', P.ha - d3.sum(P.damage), C.track]], null],
        ['Target villages', mh(P.ha), [['inside', P.ha_in_villages, C.blue], ['outside', P.ha - P.ha_in_villages, C.track]], null],
        ['Peat dome', mh(P.ha), [['on a dome', P.dome, C.blue], ['other or no landform', P.ha - P.dome, C.track]], null],
        ['Peat thickness', mh(P.ha), [['3 m or deeper', P.thick3m, C.blue], ['shallower or no class', P.ha - P.thick3m, C.track]], null]]
      const L = R ? 130 : 190, rh = R ? 52 : 74, top = 10
      const [w, h] = size(640, top + rows.length * rh + 6, 880, top + rows.length * rh + 6)
      const svg = chart('prio_parts', 'the priority KHG and the damaged peat by attribute', w, h)
      const x0 = L, x1 = w - 12, bh = R ? 18 : 26
      rows.forEach(([lab, sub, parts, fmt], i) => {
        const y = top + i * rh, tot = d3.sum(parts, (p) => p[1])
        txt(svg, L - 10, y + bh / 2, lab, { anchor: 'end', weight: 600 })
        txt(svg, L - 10, y + bh / 2 + fs, sub, { anchor: 'end', size: fsT, fill: C.muted })
        let x = x0, lx = x0
        parts.forEach(([name, v, col]) => {
          const len = (x1 - x0) * v / tot
          if (len > 0) svg.append('rect').attr('x', x).attr('y', y).attr('width', Math.max(0, len - 2)).attr('height', bh).attr('fill', col)
          const label = `${name} ${fmt ? fmt(v) : pc(v, tot)}`
          const t = txt(svg, lx + 14, y + bh + (R ? 11 : 16), label, { size: fsT, fill: C.ink2 })
          svg.append('rect').attr('x', lx).attr('y', y + bh + (R ? 6 : 9)).attr('width', 10).attr('height', 10).attr('rx', 2).attr('fill', col)
          lx += 14 + tw(t) + 14
          x += len
        })
      })
    }
    // 17 the 20 KHG with the most damaged peat, dome part dark
    {
      const K = D.prio_khg, L = R ? 170 : 240, rh = R ? 17 : 23, top = 30
      const [w, h] = size(640, top + K.length * rh + 30, 880, top + K.length * rh + 34)
      const svg = chart('prio_khg', 'the 20 KHG with the most damaged peat, on a peat dome and elsewhere', w, h)
      const x = d3.scaleLinear().domain([0, d3.max(K, (k) => k.ha) * 1.12]).range([L, w - 16])
      legend(svg, [['on a peat dome', '#1c5cab'], ['other damaged peat', '#86b6ef']], L, 12)
      for (const v of x.ticks(5)) { svg.append('line').attr('x1', x(v)).attr('x2', x(v)).attr('y1', top - 4).attr('y2', top + K.length * rh).attr('stroke', C.grid); txt(svg, x(v), top + K.length * rh + 12, `${v / 1e3}k`, { anchor: 'middle', size: fsT, fill: C.muted }) }
      K.forEach((k, i) => {
        const y = top + i * rh, bh = rh * 0.7
        txt(svg, L - 8, y + bh / 2, k.name + (k.villages ? '' : ' *'), { anchor: 'end', size: fsT })
        svg.append('rect').attr('x', x(0)).attr('y', y).attr('width', x(k.dome) - x(0)).attr('height', bh).attr('fill', '#1c5cab')
        hbar(svg, x(k.dome) + (k.dome > 0 ? 1 : 0), y, x(k.ha) - x(k.dome) - 1, bh, '#86b6ef')
        txt(svg, x(k.ha) + 5, y + bh / 2, `${Math.round(k.ha / 1e3)}k ha`, { size: fsT, fill: C.ink2 })
      })
      if (K.some((k) => !k.villages)) txt(svg, L, h - 6, '* not in a target village', { size: fsT, fill: C.muted })
    }
    // 18 actors: land status (left) and what the land needs (right, % of the actor's area)
    {
      const A = D.actors, L = R ? 200 : 280, rh = R ? 44 : 62, top = 44
      const [w, h] = size(640, top + A.length * rh + 26, 880, top + A.length * rh + 30)
      const svg = chart('actors', 'damaged peat by actor: forest area and APL, and the share canal-affected, burned and near primary or secondary canals', w, h)
      const xa = [L, L + (w - L) * 0.4], xb = [xa[1] + 46, w - 34]
      const a = d3.scaleLinear().domain([0, d3.max(A, (r) => r.ha) * 1.18]).range(xa), b = d3.scaleLinear().domain([0, 100]).range(xb)
      txt(svg, xa[0], 10, 'Thousand ha', { weight: 600, size: fsT }); txt(svg, xb[0], 10, '% of the actor\'s area', { weight: 600, size: fsT })
      legend(svg, [['forest area', C.green], ['APL', C.yellow]], xa[0], 28, 10)
      legend(svg, [['R1 canal-affected', C.blue], ['R2 burned', C.orange], ['main canals', C.violet]], xb[0], 28, 8)
      A.forEach((r, i) => {
        const y = top + i * rh, bh = rh * 0.42
        txt(svg, L - 10, y + rh * 0.3, ACTL[i], { anchor: 'end', size: fsS })
        svg.append('rect').attr('x', a(0)).attr('y', y).attr('width', a(r.forest_ha) - a(0)).attr('height', bh).attr('fill', C.green)
        hbar(svg, a(r.forest_ha) + (r.forest_ha > 0 ? 1 : 0), y, a(r.ha) - a(r.forest_ha) - 1, bh, C.yellow)
        txt(svg, a(r.ha) + 5, y + bh / 2, f0(r.ha / 1e3), { size: fsT, fill: C.ink2 })
        ;[[r.r1_ha, C.blue], [r.r2_ha, C.orange], [r.ps_ha, C.violet]].forEach(([v, col], j) => {
          const yy = y + j * (rh * 0.27), p = 100 * v / r.ha
          hbar(svg, b(0), yy, b(p) - b(0), rh * 0.2, col)
          txt(svg, b(p) + 4, yy + rh * 0.1, `${Math.round(p)}%`, { size: fsT - 1, fill: C.ink2 })
        })
      })
      axis(svg.append('g').attr('transform', `translate(0,${top + A.length * rh})`).call(d3.axisBottom(a).ticks(4).tickFormat((v) => f0(v / 1e3)).tickSizeOuter(0)))
      axis(svg.append('g').attr('transform', `translate(0,${top + A.length * rh})`).call(d3.axisBottom(b).ticks(4).tickFormat((v) => `${v}%`).tickSizeOuter(0)))
    }
    // 19 provinces by actor
    {
      const PV = D.actor_prov, L = R ? 130 : 190, rh = R ? 19 : 26, top = 30
      const [w, h] = size(640, top + PV.length * rh + 24, 880, top + PV.length * rh + 28)
      const svg = chart('actor_prov', 'damaged peat by province and actor', w, h)
      const x = d3.scaleLinear().domain([0, d3.max(PV, (p) => p.total) * 1.1]).range([L, w - 16])
      legend(svg, ACTL.map((l, i) => [l.split(',')[0] + (i === 1 ? ' (buffer)' : ''), ACTC[i]]), L, 12, 12)
      for (const v of x.ticks(5)) { svg.append('line').attr('x1', x(v)).attr('x2', x(v)).attr('y1', top - 4).attr('y2', top + PV.length * rh).attr('stroke', C.grid); txt(svg, x(v), top + PV.length * rh + 12, `${v / 1e3}k`, { anchor: 'middle', size: fsT, fill: C.muted }) }
      PV.forEach((p, i) => {
        const y = top + i * rh, bh = rh * 0.7
        txt(svg, L - 8, y + bh / 2, p.province, { anchor: 'end', size: fsT })
        let xx = x(0)
        p.v.forEach((v, j) => { const len = x(v) - x(0); if (len > 0) svg.append('rect').attr('x', xx).attr('y', y).attr('width', Math.max(0, len - 1)).attr('height', bh).attr('fill', ACTC[j]); xx += len })
        txt(svg, xx + 5, y + bh / 2, `${Math.round(p.total / 1e3)}k ha`, { size: fsT, fill: C.ink2 })
      })
    }
  }

  window.__done = true
})()
