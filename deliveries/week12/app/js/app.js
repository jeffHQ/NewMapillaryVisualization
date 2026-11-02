/* Praga a pie de calle — visualización con deck.gl (semana 12) */
(function () {
  'use strict';

  const nf = new Intl.NumberFormat('es', { useGrouping: 'always' });
  const nf1 = new Intl.NumberFormat('es', { useGrouping: 'always', maximumFractionDigits: 1 });
  const fmt = Object.assign((n) => nf.format(n), { format: (n) => nf.format(n) });
  const fmt1 = (n) => nf1.format(n);
  const pct = (x, d = 0) => (x * 100).toFixed(d).replace('.', ',') + ' %';
  const $ = (id) => document.getElementById(id);

  // ---- Paletas ----
  // Categorías de objeto (Okabe-Ito, seguras para daltonismo). Estos colores SOLO significan categoría.
  const CAT_COLORS = {
    signage: '#E69F00', lighting: '#F0E442', commerce: '#CC79A7', marking: '#56B4E9',
    furniture: '#009E73', utilities: '#0072B2', traffic_light: '#D55E00', other: '#999999',
  };
  // Modos de desplazamiento: tonos distintos de los de categoría, para no mezclar significados.
  const MODES = [
    { id: 'vehicle', label: 'Vehículo (> 25 km/h)', color: '#3f2b96' },
    { id: 'micro', label: 'Bici / scooter (7–25 km/h)', color: '#a61e4d' },
    { id: 'walk', label: 'A pie (< 7 km/h)', color: '#0b7285' },
  ];
  // Densidad: rampa neutra azul-grisácea, sin relación con ninguna categoría ni modo.
  const DENSITY_RAMP = ['#dbe3ee', '#b9c6d8', '#8fa1bb', '#66789a', '#43547a', '#1f2d4d'];
  const GRAY = [170, 178, 190, 120];
  const hex2rgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const MODE_RGB = Object.fromEntries(MODES.map((m) => [m.id, hex2rgb(m.color)]));

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

  const MES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
  const YEAR0 = 2014;
  const monthIdx = (y, m) => (y - YEAR0) * 12 + (m - 1);
  const monthLabel = (ti) => `${MES[ti % 12]} ${YEAR0 + Math.floor(ti / 12)}`;
  const hh = (h) => String(h).padStart(2, '0');

  const SAMPLE_KM = 0.04;      // cada muestra de trayectoria ≈ 40 m (ver code/05_build_processed_data.py)
  const DAY_SPAN = 10, DAY_TRAIL = 25;  // minutos de reloj: duración visual de un viaje y su estela
  const TRAIL = 18, CLOCK_MAX = 60;

  // ---- Estado ----
  const state = {
    layer: 'objects',
    time: [0, 0],                 // rango de meses (índices)
    hours: [0, 23],
    cats: new Set(),
    modes: new Set(MODES.map((m) => m.id)),
    gray: true,                   // categorías no elegidas en gris en vez de ocultas
  };
  let F, T, S, TIME_N = 0;
  let clockMode = 'day', dayMin = 0, time = 0, playing = true, speed = 4, lastTs = null, lastClock = 0;
  let deckgl, cache = {};
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isTrips = () => state.layer === 'trips';
  const usesTrips = () => state.layer !== 'objects';

  // ---------------------------------------------------------------- datos
  Promise.all(['data/features.json', 'data/trips.json', 'data/summary.json'].map((u) =>
    fetch(u).then((r) => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); })
  )).then(([f, t, s]) => {
    F = f; T = t; S = s;
    F.catIds = F.categories.map((c) => c.id);
    F.catColor = F.catIds.map((id) => hex2rgb(CAT_COLORS[id]));
    F.ti = F.year.map((y, i) => monthIdx(y, F.month[i]));
    T.forEach((d) => { d.ti = monthIdx(d.y, d.o); d.rgb = MODE_RGB[d.m]; });
    TIME_N = Math.max(...F.ti, ...T.map((d) => d.ti)) + 1;
    state.time = [0, TIME_N - 1];
    state.cats = new Set(F.catIds.map((_, i) => i));
    init();
  }).catch((e) => {
    console.error(e);
    $('loading').hidden = false;
    $('loading').textContent = 'No se pudo iniciar la visualización (' + e.message + '). Si abriste el archivo directamente, sirve la carpeta con un servidor local: python -m http.server';
  });

  // ---------------------------------------------------------------- filtrado
  const inR = (v, r) => v >= r[0] && v <= r[1];

  // skip: dimensión que se ignora (para los histogramas enlazados). which: 'on' | 'off' (categorías elegidas / no elegidas)
  function objectIndices(skip, which = 'on') {
    const out = [];
    for (let i = 0; i < F.lon.length; i++) {
      if (skip !== 'time' && !inR(F.ti[i], state.time)) continue;
      if (skip !== 'hour' && !inR(F.hour[i], state.hours)) continue;
      if (skip !== 'cat') {
        const sel = state.cats.has(F.cat[i]);
        if ((which === 'on') !== sel) continue;
      }
      out.push(i);
    }
    return out;
  }
  function tripsFiltered(skip) {
    return T.filter((t) =>
      (skip === 'time' || inR(t.ti, state.time)) &&
      (skip === 'hour' || inR(t.h, state.hours)) &&
      state.modes.has(t.m));
  }
  const getTrips = () => (cache.trips || (cache.trips = tripsFiltered()));

  // ---------------------------------------------------------------- mapa
  const pathFn = (d) => d.p.map((p) => [p[0], p[1]]);
  const tsDay = (d) => d.p.map((p) => d.t + (p[2] / Math.max(d.d, 1)) * DAY_SPAN);   // minuto real del día
  const tsRel = (d) => d.p.map((p) => p[2]);
  const colorFn = (d) => d.rgb;
  const posObj = (i) => [F.lon[i], F.lat[i]];
  const posPt = (d) => d;

  function init() {
    deckgl = new deck.DeckGL({
      container: 'map',
      map: maplibregl,
      mapStyle: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      initialViewState: baseView(),
      controller: true,
      onHover,
      onLoad: () => { $('loading').hidden = true; },
    });
    setTimeout(() => { $('loading').hidden = true; }, 1500);

    buildCharts();
    bindUI();
    playing = !reducedMotion;
    syncPlayButton();
    const h = new URLSearchParams(location.hash.slice(1));   // enlaces directos: #step=3
    goStep(h.has('step') ? +h.get('step') - 1 : 0);
    requestAnimationFrame(tick);
  }

  const baseView = () => ({ longitude: S.area.center[0], latitude: S.area.center[1], zoom: 12.6, pitch: 0, bearing: 0 });

  function layers() {
    if (state.layer === 'objects') {
      const out = [];
      if (state.gray) {
        const off = cache.off || (cache.off = objectIndices(null, 'off'));
        if (off.length) out.push(new deck.ScatterplotLayer({
          id: 'objects-gray', data: off, pickable: true, getPosition: posObj, getFillColor: GRAY,
          getRadius: 5, radiusMinPixels: 2, radiusMaxPixels: 8, radiusUnits: 'meters',
        }));
      }
      const on = cache.on || (cache.on = objectIndices(null, 'on'));
      out.push(new deck.ScatterplotLayer({
        id: 'objects', data: on, pickable: true, getPosition: posObj,
        getFillColor: (i) => [...F.catColor[F.cat[i]], 225],
        getRadius: 6, radiusMinPixels: 2, radiusMaxPixels: 9, radiusUnits: 'meters',
        updateTriggers: { getFillColor: [on.length] },
      }));
      return out;
    }
    if (state.layer === 'density') {
      // Densidad de RECORRIDO: muestras cada ~40 m a lo largo de las trayectorias filtradas
      const pts = cache.pts || (cache.pts = getTrips().flatMap((d) => d.s));
      return [new deck.HexagonLayer({
        id: 'density', data: pts, pickable: true, extruded: true, getPosition: posPt,
        radius: 90, elevationScale: 4, elevationRange: [0, 450], coverage: 0.9,
        colorRange: DENSITY_RAMP.map(hex2rgb), upperPercentile: 99,
        material: { ambient: 0.65, diffuse: 0.6, shininess: 20 },
      })];
    }
    // Trayectorias: solo estelas que se desvanecen (sin líneas permanentes)
    return [new deck.TripsLayer({
      id: 'trips', data: getTrips(), pickable: true,
      getPath: pathFn, getTimestamps: clockMode === 'day' ? tsDay : tsRel, getColor: colorFn,
      widthMinPixels: 3, jointRounded: true, capRounded: true, fadeTrail: true,
      trailLength: clockMode === 'day' ? DAY_TRAIL : TRAIL,
      currentTime: clockMode === 'day' ? dayMin : time,
      updateTriggers: { getTimestamps: [clockMode] },
    })];
  }

  function render() {
    cache = {};
    deckgl.setProps({ layers: layers() });
    updateCharts();
    updateSummary();
    syncLegend();
    if (isTrips()) updateClock();
  }

  function flyTo(view) {
    deckgl.setProps({
      initialViewState: Object.assign(baseView(), view,
        { transitionDuration: reducedMotion ? 0 : 1200, transitionInterpolator: new deck.FlyToInterpolator() }),
    });
  }

  // ---------------------------------------------------------------- reloj y animación
  function updateClock() {
    const day = clockMode === 'day';
    const hours = new Map();
    let active = 0;
    for (const d of getTrips()) {
      const on = day ? (dayMin >= d.t && dayMin <= d.t + DAY_SPAN + DAY_TRAIL) : (time <= d.d + TRAIL);
      if (on) { active++; hours.set(d.h, (hours.get(d.h) || 0) + 1); }
    }
    if (day) {
      $('clock-display').textContent = `${hh(Math.floor(dayMin / 60) % 24)}:${hh(Math.floor(dayMin % 60))}`;
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
    $('clock-hour').textContent = best ? hh(best[0]) + ':00 h' : '—';
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
      ? 'Cada trayectoria aparece a la hora real del día en que se capturó y se desvanece; se superponen todas las fechas.'
      : 'Las trayectorias de todas las fechas se reproducen a la vez sobre 60 s relativos.';
    updateClock();
    if (isTrips()) deckgl.setProps({ layers: layers() });
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

  function syncPlayButton() {
    const b = $('play');
    b.textContent = playing ? 'Pausar' : 'Reproducir';
    b.setAttribute('aria-pressed', String(playing));
  }

  // ---------------------------------------------------------------- tooltip
  function onHover(info) {
    const tip = $('tooltip');
    if (!info || !info.object) { tip.hidden = true; return; }
    let html = '';
    if (state.layer === 'objects') {
      const i = info.object;
      html = `<b>${prettyValue(F.values[F.val[i]])}</b><br>${F.categories[F.cat[i]].label}<br>${MES[F.month[i] - 1]} ${F.year[i]} · ${hh(F.hour[i])}:00 h`;
    } else if (state.layer === 'density') {
      const n = info.object.points ? info.object.points.length : 0;
      html = `<b>≈ ${fmt1.format(n * SAMPLE_KM)} km</b> de recorrido<br>en esta celda (~180 m)<br><span class="muted">${fmt(n)} muestras de trayectoria</span>`;
    } else {
      const d = info.object, m = MODES.find((x) => x.id === d.m);
      html = `<b>${m.label.split(' (')[0]}</b><br>${fmt1.format(d.s)} km/h · ${MES[d.o - 1]} ${d.y}<br>inicia ${hh(d.h)}:00 h`;
    }
    tip.innerHTML = html;
    tip.style.left = Math.min(info.x + 14, tip.parentElement.clientWidth - 250) + 'px';
    tip.style.top = Math.max(info.y - 10, 50) + 'px';
    tip.hidden = false;
  }

  // ---------------------------------------------------------------- leyenda = filtro
  function modeRows() {
    return MODES.map((m) => `<div class="row"><label><input type="checkbox" data-mode="${m.id}" checked>
      <span class="swatch" style="background:${m.color}"></span><span>${m.label}</span></label>
      <span class="n">${fmt(S.trips_by_mode[m.id] || 0)}</span><button type="button" class="solo" data-solo-mode="${m.id}" aria-label="Solo ${m.label}">solo</button></div>`).join('');
  }
  function buildLegend() {
    const el = $('legend');
    if (state.layer === 'objects') {
      el.innerHTML = `<div class="group"><h4>Categoría de objeto</h4>
        ${F.categories.map((c, i) => `<div class="row"><label><input type="checkbox" data-cat="${i}" checked>
          <span class="swatch" style="background:${CAT_COLORS[c.id]}"></span><span>${c.label}</span></label>
          <span class="n">${fmt(c.count)}</span><button type="button" class="solo" data-solo-cat="${i}" aria-label="Solo ${c.label}">solo</button></div>`).join('')}
        <div class="presets"><button type="button" class="btn small" data-preset="all">Todas</button>
          <button type="button" class="btn small" data-preset="top3">Las 3 mayores</button>
          <button type="button" class="btn small" data-preset="none">Ninguna</button></div>
        <label class="opt"><input type="checkbox" id="opt-gray" checked> Mostrar el resto en gris</label></div>`;
    } else if (state.layer === 'density') {
      el.innerHTML = `<div class="group"><h4>Recorrido reconstruido por celda</h4>
        <div class="ramp" style="background:linear-gradient(90deg,${DENSITY_RAMP.join(',')})"></div>
        <div class="ramp-labels"><span>menos</span><span>más</span></div>
        <div class="hint">Altura y tono = km recorridos (muestras cada ~40 m). Basado en trayectorias, no en puntos.</div></div>
        <div class="group"><h4>Modo de desplazamiento (inferido)</h4>${modeRows()}</div>`;
    } else {
      el.innerHTML = `<div class="group"><h4>Modo de desplazamiento (inferido)</h4>${modeRows()}
        <div class="hint">Cada trayectoria se desvanece tras pasar.</div></div>`;
    }
    syncLegend();
  }
  function syncLegend() {
    const el = $('legend');
    el.querySelectorAll('[data-cat]').forEach((cb) => { cb.checked = state.cats.has(+cb.dataset.cat); });
    el.querySelectorAll('[data-mode]').forEach((cb) => { cb.checked = state.modes.has(cb.dataset.mode); });
    const g = $('opt-gray'); if (g) g.checked = state.gray;
  }
  function bindLegend() {
    const el = $('legend');
    el.addEventListener('change', (e) => {
      const t = e.target;
      if (t.dataset.cat != null) { t.checked ? state.cats.add(+t.dataset.cat) : state.cats.delete(+t.dataset.cat); }
      else if (t.dataset.mode) { t.checked ? state.modes.add(t.dataset.mode) : state.modes.delete(t.dataset.mode); }
      else if (t.id === 'opt-gray') state.gray = t.checked;
      else return;
      render();
    });
    el.addEventListener('click', (e) => {
      const b = e.target.closest('button'); if (!b) return;
      if (b.dataset.soloCat != null) state.cats = new Set([+b.dataset.soloCat]);
      else if (b.dataset.soloMode) state.modes = new Set([b.dataset.soloMode]);
      else if (b.dataset.preset === 'all') state.cats = new Set(F.catIds.map((_, i) => i));
      else if (b.dataset.preset === 'none') state.cats = new Set();
      else if (b.dataset.preset === 'top3') {
        state.cats = new Set(F.categories.map((c, i) => [i, c.count]).filter(([i]) => F.catIds[i] !== 'other')
          .sort((a, b2) => b2[1] - a[1]).slice(0, 3).map(([i]) => i));
      } else return;
      render();
    });
  }

  // ---------------------------------------------------------------- UI general
  function bindUI() {
    document.querySelectorAll('.layer-switch button').forEach((b) =>
      b.addEventListener('click', () => setLayer(b.dataset.layer)));
    bindLegend();
    $('reset').onclick = () => { resetFilters(); render(); };
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
      if (e.target.matches('input, select, textarea, svg, button')) return;
      if (e.key === 'ArrowRight') goStep(step + 1);
      if (e.key === 'ArrowLeft') goStep(step - 1);
    });
  }

  function resetFilters() {
    state.time = [0, TIME_N - 1];
    state.hours = [0, 23];
    state.cats = new Set(F.catIds.map((_, i) => i));
    state.modes = new Set(MODES.map((m) => m.id));
    state.gray = true;
  }

  function setLayer(layer, opts = {}) {
    state.layer = layer;
    document.querySelectorAll('.layer-switch button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.layer === layer)));
    $('clock').hidden = !isTrips();
    $('top-card').hidden = usesTrips();
    buildLegend();
    if (isTrips()) setClockMode(clockMode);
    if (!opts.keepView) {
      flyTo(layer === 'density' ? { pitch: 50, bearing: -15, zoom: 12.2 } : layer === 'trips' ? { zoom: 12.9, pitch: 30 } : {});
    }
    render();
  }

  // ---------------------------------------------------------------- series de tiempo (barras + selección por arrastre)
  const charts = {};
  function makeSeries(svgId, n, getRange, setRange, labelsFn) {
    const svg = $(svgId);
    const W = 360, H = 104, padB = 18, padT = 12;
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    const bw = W / n;
    const c = { svg, n, W, H, padB, padT, bw, getRange, labelsFn };
    const full = () => { const r = getRange(); return r[0] === 0 && r[1] === n - 1; };
    const idxOf = (ev) => {
      const r = svg.getBoundingClientRect();
      return Math.max(0, Math.min(n - 1, Math.floor(((ev.clientX - r.left) / r.width) * W / bw)));
    };
    const xOf = (ev) => { const r = svg.getBoundingClientRect(); return ((ev.clientX - r.left) / r.width) * W; };
    let drag = null;
    svg.addEventListener('pointerdown', (ev) => {
      svg.setPointerCapture(ev.pointerId);
      const [r0, r1] = getRange(), x = xOf(ev), i = idxOf(ev), tol = 8;
      if (!full() && Math.abs(x - r0 * bw) <= tol) drag = { mode: 'left' };
      else if (!full() && Math.abs(x - (r1 + 1) * bw) <= tol) drag = { mode: 'right' };
      else if (!full() && i >= r0 && i <= r1) drag = { mode: 'move', grab: i, r0, r1 };
      else { drag = { mode: 'new', anchor: i }; setRange([i, i]); }
    });
    svg.addEventListener('pointermove', (ev) => {
      if (!drag) return;
      const i = idxOf(ev), [r0, r1] = getRange();
      if (drag.mode === 'left') setRange([Math.min(i, r1), r1]);
      else if (drag.mode === 'right') setRange([r0, Math.max(i, r0)]);
      else if (drag.mode === 'new') setRange([Math.min(drag.anchor, i), Math.max(drag.anchor, i)]);
      else {
        const w = drag.r1 - drag.r0, a = Math.max(0, Math.min(n - 1 - w, drag.r0 + i - drag.grab));
        setRange([a, a + w]);
      }
    });
    const end = () => { drag = null; };
    svg.addEventListener('pointerup', end); svg.addEventListener('pointercancel', end);
    svg.addEventListener('dblclick', () => setRange([0, n - 1]));
    svg.addEventListener('keydown', (ev) => {
      const [r0, r1] = getRange();
      const d = ev.key === 'ArrowRight' ? 1 : ev.key === 'ArrowLeft' ? -1 : 0;
      if (ev.key === 'Escape' || ev.key === 'Home') { setRange([0, n - 1]); ev.preventDefault(); }
      else if (d && ev.shiftKey) { setRange([r0, Math.max(r0, Math.min(n - 1, r1 + d))]); ev.preventDefault(); }
      else if (d) { const w = r1 - r0, a = Math.max(0, Math.min(n - 1 - w, r0 + d)); setRange([a, a + w]); ev.preventDefault(); }
    });
    charts[svgId] = c;
  }

  function buildCharts() {
    makeSeries('chart-time', TIME_N, () => state.time, (r) => { state.time = r; render(); },
      (i) => (i % 12 === 0 && (YEAR0 + i / 12) % 2 === 0 ? String(YEAR0 + i / 12) : null));
    makeSeries('chart-hour', 24, () => state.hours, (r) => { state.hours = r; render(); },
      (i) => (i % 3 === 0 ? String(i) : null));
  }

  function countBy(n, values) {
    const out = new Array(n).fill(0);
    values.forEach((v) => { if (v >= 0 && v < n) out[v]++; });
    return out;
  }

  function drawSeries(c, counts) {
    const range = c.getRange();
    const max = Math.max(1, ...counts);
    const plotH = c.H - c.padB - c.padT;
    let html = `<line class="axis" x1="0" x2="${c.W}" y1="${c.H - c.padB}" y2="${c.H - c.padB}"/>`;
    counts.forEach((v, i) => {
      const h = (v / max) * plotH;
      const on = i >= range[0] && i <= range[1];
      html += `<rect class="bar${on ? ' on' : ''}" x="${i * c.bw + 0.5}" y="${c.padT + plotH - h}" width="${Math.max(c.bw - 1, 0.8)}" height="${Math.max(h, v ? 1 : 0)}"></rect>`;
      const lab = c.labelsFn(i);
      if (lab) html += `<text x="${Math.max(i * c.bw + c.bw / 2, 10)}" y="${c.H - 4}" text-anchor="middle">${lab}</text>`;
    });
    const full = range[0] === 0 && range[1] === c.n - 1;
    if (!full) {
      const x0 = range[0] * c.bw, x1 = (range[1] + 1) * c.bw;
      html += `<rect class="brush" x="${x0}" y="${c.padT - 2}" width="${x1 - x0}" height="${c.H - c.padB - c.padT + 2}"></rect>`;
      [x0, x1].forEach((x) => { html += `<rect class="grip" x="${x - 2}" y="${c.padT + plotH / 2 - 9}" width="4" height="18" rx="2"></rect>`; });
    }
    html += `<text x="2" y="9" text-anchor="start">máx ${fmt.format(max)}</text>`;
    c.svg.innerHTML = html;
  }

  function updateCharts() {
    let tv, hv;
    if (usesTrips()) {
      tv = tripsFiltered('time').map((t) => t.ti);
      hv = tripsFiltered('hour').map((t) => t.h);
    } else {
      tv = objectIndices('time').map((i) => F.ti[i]);
      hv = objectIndices('hour').map((i) => F.hour[i]);
    }
    drawSeries(charts['chart-time'], countBy(TIME_N, tv));
    drawSeries(charts['chart-hour'], countBy(24, hv));
    const [t0, t1] = state.time, [h0, h1] = state.hours;
    $('time-range').textContent = (t0 === 0 && t1 === TIME_N - 1) ? `Todo (${monthLabel(0)} – ${monthLabel(TIME_N - 1)})` : `${monthLabel(t0)} – ${monthLabel(t1)}`;
    $('hour-range').textContent = (h0 === 0 && h1 === 23) ? 'Todo el día' : `${hh(h0)}:00 – ${hh(h1)}:59`;
  }

  // ---------------------------------------------------------------- resumen y ranking
  function updateSummary() {
    const el = $('result-count');
    if (usesTrips()) {
      const tr = getTrips();
      const km = tr.reduce((a, d) => a + d.s.length, 0) * SAMPLE_KM;
      el.textContent = `${fmt(tr.length)} de ${fmt(T.length)} trayectorias · ≈ ${fmt(Math.round(km))} km`;
      return;
    }
    const on = cache.on || (cache.on = objectIndices(null, 'on'));
    el.textContent = `${fmt(on.length)} de ${fmt(F.lon.length)} detecciones`;
    const counts = new Map();
    on.forEach((i) => counts.set(F.val[i], (counts.get(F.val[i]) || 0) + 1));
    const top = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);
    const max = top.length ? top[0][1] : 1;
    $('top-list').innerHTML = top.length ? top.map(([v, n]) =>
      `<li><span>${prettyValue(F.values[v])}</span><span class="n">${fmt(n)}</span><span class="bar" style="width:${(n / max) * 100}%;background:${CAT_COLORS[F.catIds[catOfValue(v)]]}"></span></li>`).join('')
      : '<li class="muted">Sin datos con los filtros actuales.</li>';
  }
  let valueCat = null;
  function catOfValue(v) {
    if (!valueCat) { valueCat = {}; for (let i = 0; i < F.val.length; i++) valueCat[F.val[i]] = F.cat[i]; }
    return valueCat[v];
  }

  // ---------------------------------------------------------------- recorrido guiado
  let step = 0, STEPS = null;
  function steps() {
    const cats = S.categories, total = S.n_detections;
    const share = (id) => cats[id] / total;
    const dy = S.detections_by_year;
    const peakYear = +Object.keys(dy).filter((y) => y >= YEAR0).sort((a, b) => dy[b] - dy[a])[0];
    const modeTot = Object.values(S.trips_by_mode).reduce((a, b) => a + b, 0);
    const vShare = S.trips_by_mode.vehicle / modeTot;
    const tc = S.trip_concentration;
    const go = (layer, mut) => () => { resetFilters(); if (mut) mut(); setLayer(layer); };
    return [
      {
        q: '¿Qué tan completa es la cobertura?',
        text: `La zona de estudio (~${S.area.width_km.toString().replace('.', ',')} × ${S.area.height_km.toString().replace('.', ',')} km, oeste de Praga) reúne ${fmt.format(total)} detecciones de objetos urbanos en ${fmt.format(S.n_sequences_detections)} secuencias de captura (${fmt.format(S.n_images)} imágenes). Cada punto es un objeto; el color indica su categoría.`,
        hint: 'Acerca el mapa y pasa el cursor sobre un punto para ver qué es y cuándo se detectó.',
        apply: go('objects'),
      },
      {
        q: '¿Cuándo se capturó la ciudad?',
        text: `La captura es muy desigual: ${peakYear} concentra ${pct(dy[peakYear] / total)} de las detecciones (${fmt.format(dy[peakYear])}) y varios años apenas aportan datos. Mostramos solo ${peakYear}; compáralo con otros periodos.`,
        hint: 'Arrastra sobre la serie mensual para elegir un periodo; arrastra los bordes para ajustarlo (doble clic restablece).',
        apply: go('objects', () => { state.time = [monthIdx(peakYear, 1), monthIdx(peakYear, 12)]; }),
      },
      {
        q: '¿Qué elementos dominan el paisaje urbano?',
        text: `Señalización vertical (${pct(share('signage'))}), alumbrado y postes (${pct(share('lighting'))}) y comercio/publicidad (${pct(share('commerce'))}) suman ${pct(share('signage') + share('lighting') + share('commerce'))} de lo detectado. El mobiliario urbano es minoritario (${pct(share('furniture'))}). Resaltamos las tres categorías mayores y dejamos el resto en gris.`,
        hint: 'En la leyenda puedes elegir categorías, pulsar «solo» o usar «Las 3 mayores».',
        apply: go('objects', () => {
          state.cats = new Set(F.categories.map((c, i) => [i, c.count]).filter(([i]) => F.catIds[i] !== 'other')
            .sort((a, b) => b[1] - a[1]).slice(0, 3).map(([i]) => i));
        }),
      },
      {
        q: '¿Dónde se concentra el recorrido?',
        text: `Medido con trayectorias (≈ ${fmt.format(Math.round(tc.km_total))} km reconstruidos), el ${pct(tc.top10pct_cells_share)} del recorrido cae en el 10 % de las celdas de ~100 m recorridas (de ${fmt.format(tc.occupied_cells_100m)}). Las torres marcan las calles más transitadas por quienes capturan.`,
        hint: 'Inclina el mapa con Ctrl + arrastrar. Filtra por modo, periodo y hora para ver cómo cambia.',
        apply: go('density'),
      },
      {
        q: '¿Cómo se desplaza quien captura?',
        text: `De ${fmt.format(modeTot)} trayectorias reconstruidas, ${pct(vShare)} corresponde a velocidades de vehículo motorizado. La actividad se concentra a mediodía y primera tarde, con pico a las ${hh(S.peak_trip_hour)}:00 h (hora local); casi no hay capturas nocturnas.`,
        hint: 'Mueve el reloj de 24 h o pulsa Reproducir. Cada trayectoria se desvanece tras pasar.',
        apply: go('trips'),
      },
      {
        q: 'Conclusión provisional y límites',
        text: 'Mapillary describe bien dónde y cuándo se ha mirado la ciudad, pero no es un censo: la cobertura la determinan pocas campañas y dispositivos, y el modo de desplazamiento es solo una inferencia por velocidad. Cualquier lectura "urbana" debe ir acompañada de la pregunta: ¿quién capturó y cuándo?',
        hint: 'Explora libremente: todos los filtros siguen activos.',
        apply: go('objects'),
      },
    ];
  }
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
