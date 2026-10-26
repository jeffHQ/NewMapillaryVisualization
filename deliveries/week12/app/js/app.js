/* Praga a pie de calle — visualización con deck.gl (semana 12) */
(function () {
  'use strict';

  const fmt = new Intl.NumberFormat('es', { useGrouping: 'always' });
  const pct = (x, d = 0) => (x * 100).toFixed(d).replace('.', ',') + ' %';
  const $ = (id) => document.getElementById(id);

  // ---- Paletas (Okabe-Ito, seguras para daltonismo) ----
  const CAT_COLORS = {
    signage: '#E69F00', lighting: '#F0E442', commerce: '#CC79A7', marking: '#56B4E9',
    furniture: '#009E73', utilities: '#0072B2', traffic_light: '#D55E00', other: '#999999',
  };
  const MODES = [
    { id: 'vehicle', label: 'Vehículo (> 25 km/h)', color: '#D55E00' },
    { id: 'micro', label: 'Bici / scooter (7–25 km/h)', color: '#F0E442' },
    { id: 'walk', label: 'A pie (< 7 km/h)', color: '#56B4E9' },
  ];
  const HEX_RAMP = ['#1b0c41', '#4a0c6b', '#a52c60', '#ed6925', '#fbb61a', '#fcffa4'];
  const hex2rgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));

  // ---- Nombres legibles para los valores más frecuentes ----
  const VALUE_ES = {
    'object--street-light': 'Farola',
    'object--traffic-sign--front': 'Señal de tráfico (frente)',
    'object--traffic-sign--back': 'Señal de tráfico (reverso)',
    'object--sign--advertisement': 'Anuncio publicitario',
    'object--support--pole': 'Poste',
    'object--support--utility-pole': 'Poste de servicios',
    'object--sign--store': 'Rótulo de comercio',
    'object--trash-can': 'Papelera',
    'object--manhole': 'Registro / alcantarilla',
    'marking--discrete--crosswalk-zebra': 'Paso de peatones',
    'marking--discrete--symbol--bicycle': 'Símbolo de bicicleta',
    'object--bench': 'Banco',
    'object--junction-box': 'Caja de conexiones',
    'object--catch-basin': 'Sumidero',
    'construction--flat--driveway': 'Entrada de vehículos',
    'construction--barrier--temporary': 'Barrera temporal',
  };
  const prettyValue = (v) => VALUE_ES[v] ||
    v.split('--').slice(-2).join(' · ').replace(/-/g, ' ').replace(/^./, (c) => c.toUpperCase());

  // ---- Estado ----
  const state = {
    layer: 'objects',
    years: [2014, 2026],
    hours: [0, 23],
    cats: new Set(),
    modes: new Set(MODES.map((m) => m.id)),
  };
  let F, T, S;           // features, trips, summary
  let YEAR_DOMAIN = [], HOUR_DOMAIN = Array.from({ length: 24 }, (_, i) => i);
  let clockMode = 'day', dayMin = 0, deckgl, time = 0, playing = true, speed = 4, lastTs = null, selected = null;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------------------------------------------------------------- datos
  Promise.all(['data/features.json', 'data/trips.json', 'data/summary.json'].map((u) =>
    fetch(u).then((r) => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); })
  )).then(([f, t, s]) => {
    F = f; T = t; S = s;
    F.catIds = F.categories.map((c) => c.id);
    F.catColor = F.catIds.map((id) => hex2rgb(CAT_COLORS[id]));
    state.cats = new Set(F.catIds.map((_, i) => i));
    const ys = [...new Set(F.year)].sort((a, b) => a - b);
    YEAR_DOMAIN = Array.from({ length: ys[ys.length - 1] - ys[0] + 1 }, (_, i) => ys[0] + i);
    state.years = [YEAR_DOMAIN[0], YEAR_DOMAIN[YEAR_DOMAIN.length - 1]];
    init();
  }).catch((e) => {
    $('loading').textContent = 'No se pudieron cargar los datos (' + e.message + '). Sirve la carpeta con un servidor local: python -m http.server';
  });

  // ---------------------------------------------------------------- filtrado
  const inRange = (v, [a, b]) => v >= a && v <= b;

  function objectIndices(skip) {
    const out = [];
    for (let i = 0; i < F.lon.length; i++) {
      if (skip !== 'year' && !inRange(F.year[i], state.years)) continue;
      if (skip !== 'hour' && !inRange(F.hour[i], state.hours)) continue;
      if (skip !== 'cat' && !state.cats.has(F.cat[i])) continue;
      out.push(i);
    }
    return out;
  }
  function tripsFiltered(skip) {
    return T.filter((t) =>
      (skip === 'year' || inRange(t.y, state.years)) &&
      (skip === 'hour' || inRange(t.h, state.hours)) &&
      (skip === 'mode' || state.modes.has(t.m)));
  }
  const isTrips = () => state.layer === 'trips';

  // ---------------------------------------------------------------- mapa
  function init() {
    deckgl = new deck.DeckGL({
      container: 'map',
      map: maplibregl,
      mapStyle: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      initialViewState: { longitude: S.area.center[0], latitude: S.area.center[1], zoom: 12.6, pitch: 0, bearing: 0 },
      controller: true,
      getTooltip: null,
      onHover: onHover,
      onClick: onClick,
      onLoad: () => { $('loading').hidden = true; },
    });
    setTimeout(() => { $('loading').hidden = true; }, 1500);

    buildControls();
    buildCharts();
    bindUI();
    playing = !reducedMotion;
    syncPlayButton();
    const h = new URLSearchParams(location.hash.slice(1));   // enlaces directos: #step=3
    goStep(h.has('step') ? +h.get('step') - 1 : 0);
    requestAnimationFrame(tick);
  }

  function layers() {
    const out = [];
    if (state.layer === 'objects') {
      const idx = objectIndices();
      out.push(new deck.ScatterplotLayer({
        id: 'objects', data: idx, pickable: true,
        getPosition: (i) => [F.lon[i], F.lat[i]],
        getFillColor: (i) => [...F.catColor[F.cat[i]], 210],
        getRadius: 6, radiusMinPixels: 2, radiusMaxPixels: 9, radiusUnits: 'meters',
        updateTriggers: { getPosition: [idx.length] },
      }));
    } else if (state.layer === 'density') {
      const idx = objectIndices();
      out.push(new deck.HexagonLayer({
        id: 'density', data: idx, pickable: true, extruded: true,
        getPosition: (i) => [F.lon[i], F.lat[i]],
        radius: 90, elevationScale: 5, elevationRange: [0, 400], coverage: 0.9,
        colorRange: HEX_RAMP.map(hex2rgb), upperPercentile: 99,
        material: { ambient: 0.6, diffuse: 0.6, shininess: 24 },
      }));
    } else {
      const data = tripsFiltered();
      const color = (m) => hex2rgb(MODES.find((x) => x.id === m).color);
      out.push(new deck.PathLayer({
        id: 'trips-base', data, getPath: (d) => d.p.map((p) => [p[0], p[1]]),
        getColor: (d) => [...color(d.m), 120], widthMinPixels: 2, rounded: true,
      }));
      out.push(new deck.TripsLayer({
        id: 'trips', data, pickable: true,
        getPath: (d) => d.p.map((p) => [p[0], p[1]]),
        getTimestamps: clockMode === 'day'
          ? (d) => d.p.map((p) => d.t + (p[2] / Math.max(d.d, 1)) * DAY_SPAN)   // minuto del día real
          : (d) => d.p.map((p) => p[2]),
        getColor: (d) => color(d.m), widthMinPixels: 4, rounded: true,
        trailLength: clockMode === 'day' ? DAY_TRAIL : TRAIL,
        currentTime: clockMode === 'day' ? dayMin : time, fadeTrail: true,
        updateTriggers: { getTimestamps: [clockMode] },
      }));
    }
    return out;
  }

  function render() {
    deckgl.setProps({ layers: layers() });
    updateCharts();
    updateSummary();
    updateLegend();
    if (isTrips()) updateClock();
  }

  function flyTo(view) {
    deckgl.setProps({
      initialViewState: Object.assign(
        { longitude: S.area.center[0], latitude: S.area.center[1], zoom: 12.6, pitch: 0, bearing: 0 },
        view,
        { transitionDuration: reducedMotion ? 0 : 1200, transitionInterpolator: new deck.FlyToInterpolator() }),
    });
  }

  // animación de trayectorias (solo redibuja la capa de viajes)
  let lastClock = 0;
  const TRAIL = 18, CLOCK_MAX = 60;
  const DAY_SPAN = 10, DAY_TRAIL = 25;   // minutos de reloj: duración visual de un viaje y su estela
  const hhmm = (m) => String(Math.floor(m / 60) % 24).padStart(2, '0') + ':' + String(Math.floor(m % 60)).padStart(2, '0');
  // Reloj de la animación + qué hay "en pantalla" en este instante
  function updateClock() {
    const day = clockMode === 'day';
    const hours = new Map();
    let active = 0;
    for (const d of tripsFiltered()) {
      const on = day ? (dayMin >= d.t && dayMin <= d.t + DAY_SPAN + DAY_TRAIL) : (time <= d.d + TRAIL);
      if (on) { active++; hours.set(d.h, (hours.get(d.h) || 0) + 1); }
    }
    if (day) {
      $('clock-display').textContent = hhmm(dayMin);
      $('clock-fill').style.width = (dayMin / 1440 * 100) + '%';
      $('clock-scrub').value = Math.floor(dayMin);
    } else {
      const t = Math.min(time, CLOCK_MAX);
      $('clock-display').textContent = t.toFixed(1).replace('.', ',') + ' s';
      $('clock-fill').style.width = (t / CLOCK_MAX * 100) + '%';
      $('clock-scrub').value = t;
    }
    $('clock-active').textContent = fmt.format(active);
    let best = null;
    hours.forEach((n, h) => { if (!best || n > best[1]) best = [h, n]; });
    $('clock-hour').textContent = best ? String(best[0]).padStart(2, '0') + ':00 h' : '—';
  }

  function setClockMode(mode) {
    clockMode = mode;
    const day = mode === 'day';
    document.querySelectorAll('[data-clock]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.clock === mode)));
    $('clock-title').textContent = day ? 'Reloj diario (24 h, hora de Praga)' : 'Reloj relativo de la animación';
    $('clock-hour-row').hidden = day;
    const sc = $('clock-scrub');
    sc.max = day ? 1439 : CLOCK_MAX; sc.step = day ? 1 : 0.1;
    $('clock-note').textContent = day
      ? 'Cada trayectoria aparece a la hora real del día en que se capturó; se superponen todas las fechas (2014–2026).'
      : 'Las trayectorias de todas las fechas se reproducen a la vez sobre 60 s relativos.';
    updateClock();
    deckgl.setProps({ layers: layers() });
  }

  function tick(ts) {
    if (isTrips() && playing) {
      if (lastTs != null) {
        const dt = (ts - lastTs) / 1000;
        if (clockMode === 'day') dayMin = (dayMin + dt * speed * 7.5) % (1440 + DAY_SPAN + DAY_TRAIL);   // 1× ≈ 30 min/s
        else time = (time + dt * speed) % 75;
      }
      deckgl.setProps({ layers: layers() });
    }
    if (isTrips() && (!lastClock || ts - lastClock > 100)) { updateClock(); lastClock = ts; }
    lastTs = ts;
    requestAnimationFrame(tick);
  }

  // ---------------------------------------------------------------- tooltip / selección
  function onHover(info) {
    const tip = $('tooltip');
    if (!info || !info.object) { tip.hidden = true; return; }
    let html = '';
    if (state.layer === 'objects') {
      const i = info.object;
      html = `<b>${prettyValue(F.values[F.val[i]])}</b><br>${F.categories[F.cat[i]].label}<br>${F.year[i]} · ${String(F.hour[i]).padStart(2, '0')}:00 h`;
    } else if (state.layer === 'density') {
      // En deck.gl 8.x el bin trae `points` (los datos agregados); `count` no existe.
      const o = info.object;
      const n = o.points ? o.points.length : (o.elevationValue ?? o.colorValue ?? 0);
      html = `<b>${fmt.format(n)}</b> detecciones<br>en esta celda (~${Math.round(90 * 2)} m)`;
    } else {
      const d = info.object, m = MODES.find((x) => x.id === d.m);
      html = `<b>${m.label.split(' (')[0]}</b><br>${d.s.toFixed(1).replace('.', ',')} km/h · ${d.y}<br>${String(d.h).padStart(2, '0')}:00 h`;
    }
    tip.innerHTML = html;
    tip.style.left = Math.min(info.x + 14, tip.parentElement.clientWidth - 250) + 'px';
    tip.style.top = Math.max(info.y - 10, 50) + 'px';
    tip.hidden = false;
  }
  function onClick(info) {
    if (state.layer !== 'objects' || !info || info.object == null) { selected = null; return; }
    selected = info.object;
    const i = selected;
    $('top-hint').textContent = `Seleccionado: ${prettyValue(F.values[F.val[i]])} (${F.year[i]}). Clic en el vacío para limpiar.`;
  }

  // ---------------------------------------------------------------- controles
  function buildControls() {
    const catList = $('cat-list');
    F.categories.forEach((c, i) => {
      const li = document.createElement('li');
      li.innerHTML = `<label><input type="checkbox" checked data-cat="${i}"><span class="swatch" style="background:${CAT_COLORS[c.id]}"></span><span>${c.label}</span><span class="n">${fmt.format(c.count)}</span></label>`;
      catList.appendChild(li);
    });
    const modeList = $('mode-list');
    MODES.forEach((m) => {
      const n = S.trips_by_mode[m.id] || 0;
      const li = document.createElement('li');
      li.innerHTML = `<label><input type="checkbox" checked data-mode="${m.id}"><span class="swatch" style="background:${m.color}"></span><span>${m.label}</span><span class="n">${fmt.format(n)}</span></label>`;
      modeList.appendChild(li);
    });
    const fill = (sel, values, fmtFn) => { sel.innerHTML = values.map((v) => `<option value="${v}">${fmtFn(v)}</option>`).join(''); };
    fill($('year-from'), YEAR_DOMAIN, (v) => v); fill($('year-to'), YEAR_DOMAIN, (v) => v);
    fill($('hour-from'), HOUR_DOMAIN, (v) => String(v).padStart(2, '0') + ':00');
    fill($('hour-to'), HOUR_DOMAIN, (v) => String(v).padStart(2, '0') + ':59');
    syncSelects();
  }

  function syncSelects() {
    $('year-from').value = state.years[0]; $('year-to').value = state.years[1];
    $('hour-from').value = state.hours[0]; $('hour-to').value = state.hours[1];
  }

  function bindUI() {
    document.querySelectorAll('.layer-switch button').forEach((b) =>
      b.addEventListener('click', () => setLayer(b.dataset.layer)));
    const range = (key, a, b, lo) => {
      $(a).addEventListener('change', () => { state[key][0] = +$(a).value; if (state[key][0] > state[key][1]) state[key][1] = state[key][0]; syncSelects(); render(); });
      $(b).addEventListener('change', () => { state[key][1] = +$(b).value; if (state[key][1] < state[key][0]) state[key][0] = state[key][1]; syncSelects(); render(); });
    };
    range('years', 'year-from', 'year-to'); range('hours', 'hour-from', 'hour-to');
    $('cat-list').addEventListener('change', (e) => {
      const i = +e.target.dataset.cat;
      e.target.checked ? state.cats.add(i) : state.cats.delete(i);
      render();
    });
    $('mode-list').addEventListener('change', (e) => {
      const id = e.target.dataset.mode;
      e.target.checked ? state.modes.add(id) : state.modes.delete(id);
      render();
    });
    $('cat-all').onclick = () => setCats(F.catIds.map((_, i) => i));
    $('cat-none').onclick = () => setCats([]);
    $('reset').onclick = resetFilters;
    $('play').onclick = () => { playing = !playing; syncPlayButton(); };
    $('speed').onchange = (e) => { speed = +e.target.value; };
    document.querySelectorAll('[data-clock]').forEach((b) => b.addEventListener('click', () => setClockMode(b.dataset.clock)));
    $('clock-scrub').addEventListener('input', (e) => {
      if (clockMode === 'day') dayMin = +e.target.value; else time = +e.target.value;
      updateClock();
      if (!playing) deckgl.setProps({ layers: layers() });
    });
    $('tour-prev').onclick = () => goStep(step - 1);
    $('tour-next').onclick = () => goStep(step + 1);
    window.addEventListener('keydown', (e) => {
      if (e.target.matches('input, select, textarea')) return;
      if (e.key === 'ArrowRight') goStep(step + 1);
      if (e.key === 'ArrowLeft') goStep(step - 1);
    });
  }

  function setCats(arr) {
    state.cats = new Set(arr);
    document.querySelectorAll('[data-cat]').forEach((cb) => { cb.checked = state.cats.has(+cb.dataset.cat); });
    render();
  }
  function setModes(ids) {
    state.modes = new Set(ids);
    document.querySelectorAll('[data-mode]').forEach((cb) => { cb.checked = state.modes.has(cb.dataset.mode); });
  }
  function resetFilters() {
    state.years = [YEAR_DOMAIN[0], YEAR_DOMAIN[YEAR_DOMAIN.length - 1]];
    state.hours = [0, 23];
    setModes(MODES.map((m) => m.id));
    syncSelects();
    setCats(F.catIds.map((_, i) => i));
  }
  function syncPlayButton() {
    const b = $('play');
    b.textContent = playing ? 'Pausar' : 'Reproducir';
    b.setAttribute('aria-pressed', String(playing));
  }

  function setLayer(layer, opts = {}) {
    state.layer = layer;
    document.querySelectorAll('.layer-switch button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.layer === layer)));
    $('cat-fieldset').hidden = isTrips();
    $('mode-fieldset').hidden = !isTrips();
    $('clock').hidden = !isTrips();
    if (isTrips()) setClockMode(clockMode);
    $('top-list').closest('.card').hidden = isTrips();
    if (!opts.keepView) {
      flyTo(layer === 'density' ? { pitch: 50, bearing: -15, zoom: 12.2 } : layer === 'trips' ? { zoom: 12.9, pitch: 30 } : {});
    }
    render();
  }

  // ---------------------------------------------------------------- gráficos (barras + selección por arrastre)
  const charts = {};
  function makeChart(svgId, domain, key, labelFn) {
    const svg = $(svgId);
    const W = 360, H = 86, padB = 16, padT = 4;
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    const bw = W / domain.length;
    const c = { svg, domain, key, W, H, padB, padT, bw, labelFn, counts: [] };
    const xToIdx = (ev) => {
      const r = svg.getBoundingClientRect();
      const x = ((ev.clientX - r.left) / r.width) * W;
      return Math.max(0, Math.min(domain.length - 1, Math.floor(x / bw)));
    };
    let anchor = null;
    svg.addEventListener('pointerdown', (ev) => { svg.setPointerCapture(ev.pointerId); anchor = xToIdx(ev); apply(anchor, anchor); });
    svg.addEventListener('pointermove', (ev) => { if (anchor != null) apply(anchor, xToIdx(ev)); });
    svg.addEventListener('pointerup', () => { anchor = null; });
    svg.addEventListener('dblclick', () => { state[key] = [domain[0], domain[domain.length - 1]]; syncSelects(); render(); });
    function apply(a, b) {
      const lo = Math.min(a, b), hi = Math.max(a, b);
      state[key] = [domain[lo], domain[hi]];
      syncSelects(); render();
    }
    charts[svgId] = c;
  }
  function buildCharts() {
    makeChart('chart-year', YEAR_DOMAIN, 'years');
    makeChart('chart-hour', HOUR_DOMAIN, 'hours');
  }

  function countBy(domain, values) {
    const m = new Map(domain.map((d) => [d, 0]));
    values.forEach((v) => m.set(v, (m.get(v) || 0) + 1));
    return domain.map((d) => m.get(d));
  }

  function drawChart(c, counts, range, everyLabel) {
    const max = Math.max(1, ...counts);
    const plotH = c.H - c.padB - c.padT;
    let html = '';
    counts.forEach((n, i) => {
      const d = c.domain[i];
      const h = (n / max) * plotH;
      const on = d >= range[0] && d <= range[1];
      html += `<rect class="bar${on ? ' on' : ''}" x="${i * c.bw + 1}" y="${c.padT + plotH - h}" width="${c.bw - 2}" height="${Math.max(h, n ? 1 : 0)}"><title>${d}: ${fmt.format(n)}</title></rect>`;
      if (i % everyLabel === 0) html += `<text x="${i * c.bw + c.bw / 2}" y="${c.H - 3}" text-anchor="middle">${d}</text>`;
    });
    html += `<text x="2" y="11" text-anchor="start" style="font-size:9px">máx ${fmt.format(max)}</text>`;
    c.svg.innerHTML = html;
  }

  function updateCharts() {
    const yc = charts['chart-year'], hc = charts['chart-hour'];
    let yVals, hVals;
    if (isTrips()) {
      yVals = tripsFiltered('year').map((t) => t.y);
      hVals = tripsFiltered('hour').map((t) => t.h);
    } else {
      const iy = objectIndices('year'); yVals = iy.map((i) => F.year[i]);
      const ih = objectIndices('hour'); hVals = ih.map((i) => F.hour[i]);
    }
    drawChart(yc, countBy(yc.domain, yVals), state.years, 2);
    drawChart(hc, countBy(hc.domain, hVals), state.hours, 3);
  }

  // ---------------------------------------------------------------- resumen, top, leyenda
  function updateSummary() {
    const el = $('result-count');
    if (isTrips()) {
      const n = tripsFiltered().length;
      el.textContent = `${fmt.format(n)} de ${fmt.format(T.length)} trayectorias`;
      return;
    }
    const idx = objectIndices();
    el.textContent = `${fmt.format(idx.length)} de ${fmt.format(F.lon.length)} detecciones`;
    const counts = new Map();
    idx.forEach((i) => counts.set(F.val[i], (counts.get(F.val[i]) || 0) + 1));
    const top = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);
    const max = top.length ? top[0][1] : 1;
    $('top-list').innerHTML = top.length ? top.map(([v, n]) =>
      `<li><span>${prettyValue(F.values[v])}</span><span class="n">${fmt.format(n)}</span><span class="bar" style="width:${(n / max) * 100}%;background:${CAT_COLORS[F.catIds[catOfValue(v)]]}"></span></li>`).join('')
      : '<li class="muted">Sin datos con los filtros actuales.</li>';
  }
  let valueCat = null;
  function catOfValue(v) {
    if (!valueCat) { valueCat = {}; for (let i = 0; i < F.val.length; i++) valueCat[F.val[i]] = F.cat[i]; }
    return valueCat[v];
  }

  function updateLegend() {
    const el = $('legend');
    if (state.layer === 'objects') {
      el.innerHTML = '<h4>Categoría de objeto</h4>' + F.categories.filter((_, i) => state.cats.has(i))
        .map((c) => `<div class="row"><span class="swatch" style="background:${CAT_COLORS[c.id]}"></span>${c.label}</div>`).join('');
    } else if (state.layer === 'density') {
      el.innerHTML = `<h4>Detecciones por celda hexagonal</h4><div class="ramp" style="background:linear-gradient(90deg,${HEX_RAMP.join(',')})"></div><div class="row" style="justify-content:space-between"><span>menos</span><span>más</span></div><div class="hint">Altura y color = número de detecciones</div>`;
    } else {
      el.innerHTML = '<h4>Modo inferido</h4>' + MODES.map((m) => `<div class="row"><span class="swatch" style="background:${m.color}"></span>${m.label}</div>`).join('') +
        '<div class="hint">Reloj diario: cada viaje aparece a su hora real (todas las fechas superpuestas)</div>';
    }
  }

  // ---------------------------------------------------------------- recorrido guiado
  let step = 0;
  function steps() {
    const cats = S.categories, total = S.n_detections;
    const share = (id) => cats[id] / total;
    const dy = S.detections_by_year;
    const peakYear = Object.keys(dy).filter((y) => y >= 2014).sort((a, b) => dy[b] - dy[a])[0];
    const modeTot = Object.values(S.trips_by_mode).reduce((a, b) => a + b, 0);
    const vShare = S.trips_by_mode.vehicle / modeTot;
    const peakH = S.peak_trip_hour;
    return [
      {
        q: '¿Qué tan completa es la cobertura?',
        text: `La zona de estudio (~${S.area.width_km.toString().replace('.', ',')} × ${S.area.height_km.toString().replace('.', ',')} km, oeste de Praga) reúne ${fmt.format(total)} detecciones de objetos urbanos en ${fmt.format(S.n_sequences_detections)} secuencias de captura (${fmt.format(S.n_images)} imágenes). Cada punto es un objeto; el color indica su categoría.`,
        hint: 'Acerca el mapa y pasa el cursor sobre un punto para ver qué es y cuándo se detectó.',
        apply: () => { resetFilters(); setLayer('objects'); },
      },
      {
        q: '¿Cuándo se capturó la ciudad?',
        text: `La captura es muy desigual: ${peakYear} concentra ${pct(dy[peakYear] / total)} de las detecciones (${fmt.format(dy[peakYear])}) y varios años apenas aportan datos. Mostramos solo ${peakYear}; compáralo con otros años.`,
        hint: 'Arrastra sobre el histograma de años para elegir un periodo (doble clic para restablecer).',
        apply: () => { resetFilters(); state.years = [+peakYear, +peakYear]; syncSelects(); setLayer('objects'); },
      },
      {
        q: '¿Qué elementos dominan el paisaje urbano?',
        text: `Señalización vertical (${pct(share('signage'))}), alumbrado y postes (${pct(share('lighting'))}) y comercio/publicidad (${pct(share('commerce'))}) suman ${pct(share('signage') + share('lighting') + share('commerce'))} de lo detectado. El mobiliario urbano es minoritario (${pct(share('furniture'))}).`,
        hint: 'Activa o desactiva categorías en el panel; la lista inferior se recalcula.',
        apply: () => { resetFilters(); setLayer('objects'); },
      },
      {
        q: '¿Dónde se concentra la actividad?',
        text: `El ${pct(S.concentration.top10pct_cells_share)} de las detecciones cae en el 10 % de las celdas de ~100 m con actividad (de ${fmt.format(S.concentration.occupied_cells_100m)} celdas ocupadas). Las torres muestran los ejes y barrios más recorridos.`,
        hint: 'Inclina el mapa con Ctrl + arrastrar. Combina con el filtro de categoría para ver dónde está cada tipo.',
        apply: () => { resetFilters(); setLayer('density'); },
      },
      {
        q: '¿Cómo se desplaza quien captura?',
        text: `De ${fmt.format(modeTot)} trayectorias reconstruidas, ${pct(vShare)} corresponde a velocidades de vehículo motorizado. La actividad se concentra a mediodía y primera tarde, con pico a las ${String(peakH).padStart(2, '0')}:00 h (hora local); casi no hay capturas nocturnas.`,
        hint: 'Mueve el reloj de 24 h o pulsa Reproducir para ver cómo se llena el día; filtra por modo y año.',
        apply: () => { resetFilters(); setLayer('trips'); },
      },
      {
        q: 'Conclusión provisional y límites',
        text: 'Mapillary describe bien dónde y cuándo se ha mirado la ciudad, pero no es un censo: la cobertura la determinan pocas campañas y dispositivos, y el modo de desplazamiento es solo una inferencia por velocidad. Cualquier lectura "urbana" debe ir acompañada de la pregunta: ¿quién capturó y cuándo?',
        hint: 'Explora libremente: todos los filtros siguen activos.',
        apply: () => { resetFilters(); setLayer('objects'); },
      },
    ];
  }
  let STEPS = null;
  function goStep(n) {
    STEPS = STEPS || steps();
    step = Math.max(0, Math.min(STEPS.length - 1, n));
    const s = STEPS[step];
    $('tour-count').textContent = `${step + 1} / ${STEPS.length}`;
    $('tour-q').textContent = s.q;
    $('tour-text').textContent = s.text;
    $('tour-hint').textContent = s.hint;
    $('tour-prev').disabled = step === 0;
    $('tour-next').disabled = step === STEPS.length - 1;
    s.apply();
  }
})();
