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

  const MAP_STYLE = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json';
  // Franjas del día para los mapas de insights (minutos desde 00:00, hora local de Praga)
  const BANDS = [
    { id: 'morning', label: 'Mañana', range: '04:00–10:59', lo: 240, hi: 660 },
    { id: 'afternoon', label: 'Tarde', range: '11:00–17:59', lo: 660, hi: 1080 },
    { id: 'night', label: 'Noche', range: '18:00–23:59', lo: 1080, hi: 1440 },
  ];
  // Insights: celdas hexagonales coloreadas por tráfico (km de recorrido), amarillo → naranja → rojo (YlOrRd, 5 clases)
  const INS_RAMP = ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026'];
  const INS_R = 120;   // radio de la celda hexagonal en metros
  // Ventana de hora de inicio elegida en la serie por hora, en minutos desde 00:00
  const startWindow = () => [state.hours[0] * 60, Math.min(1440, (state.hours[1] + 1) * 60)];
  const hhmm = (m) => `${hh(Math.floor(m / 60) % 24)}:${hh(Math.floor(m % 60))}`;
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
    scale: 'sqrt',                // escala vertical de la serie mensual: linear | sqrt | log
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
      (skip === 'hour' || state.layer === 'insights' || inR(t.h, state.hours)) &&
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
      mapStyle: MAP_STYLE,
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
    if (h.has('hours')) {                                      // enlaces directos: #step=5&hours=11-17
      const [a, b] = h.get('hours').split('-').map(Number);
      if (a >= 0 && b <= 23 && a <= b) { state.hours = [a, b]; render(); }
    }
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
    if (state.layer === 'insights') renderInsights(); else deckgl.setProps({ layers: layers() });
    updateCharts();
    updateSummary();
    renderChips();
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
    const [wlo, whi] = startWindow();
    const filtered = state.hours[0] > 0 || state.hours[1] < 23;
    $('clock-window-row').hidden = !day;
    if (day) {
      if (dayMin < wlo || dayMin > whi + DAY_SPAN + DAY_TRAIL) dayMin = wlo;     // si cambió el filtro, vuelve al inicio de la ventana
      $('clock-display').textContent = hhmm(dayMin);
      $('clock-fill').style.width = (dayMin / 1440 * 100) + '%';
      const w = $('clock-win'); w.style.left = (wlo / 1440 * 100) + '%'; w.style.width = ((whi - wlo) / 1440 * 100) + '%';
      $('clock-window').textContent = filtered ? `${hh(state.hours[0])}:00 – ${hh(state.hours[1])}:59` : 'Todo el día';
      const sc = $('clock-scrub'); sc.min = wlo; sc.max = Math.min(1439, whi); sc.value = Math.floor(dayMin);
    } else {
      $('clock-win').style.width = '0';
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
    sc.min = 0; sc.max = day ? 1439 : CLOCK_MAX; sc.step = day ? 1 : 0.1;
    $('clock-note').textContent = day
      ? 'Cada trayectoria aparece a su hora real de inicio y se desvanece; se superponen todas las fechas. Filtra la hora de inicio con la serie por hora (abajo): el reloj recorre solo esa ventana.'
      : 'Las trayectorias de todas las fechas se reproducen a la vez sobre 60 s relativos.';
    updateClock();
    if (isTrips()) deckgl.setProps({ layers: layers() });
  }

  function tick(ts) {
    if (isTrips() && playing) {
      if (lastTs != null) {
        const dt = (ts - lastTs) / 1000;
        if (clockMode === 'day') {                  // 1× ≈ 30 min/s, solo dentro de la ventana de hora de inicio
          const [lo, hi] = startWindow();
          dayMin = lo + ((dayMin - lo + dt * speed * 7.5) % (hi - lo + DAY_SPAN + DAY_TRAIL));
        }
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
    try { onHover_(info); } catch (e) { $('tooltip').hidden = true; }   // un error del tooltip nunca debe bloquear la interacción
  }
  function onHover_(info) {
    const tip = $('tooltip');
    if (!info || !info.object) { tip.hidden = true; return; }
    let html = '';
    if (state.layer === 'objects') {
      const i = info.object;
      html = `<b>${prettyValue(F.values[F.val[i]])}</b><br>${F.categories[F.cat[i]].label}<br>${MES[F.month[i] - 1]} ${F.year[i]} · ${hh(F.hour[i])}:00 h`;
    } else if (state.layer === 'density') {
      const n = info.object.points ? info.object.points.length : 0;
      html = `<b>≈ ${fmt1(n * SAMPLE_KM)} km</b> de recorrido<br>en esta celda (~180 m)<br><span class="muted">${fmt(n)} muestras de trayectoria</span>`;
    } else {
      const d = info.object, m = MODES.find((x) => x.id === d.m);
      html = `<b>${m.label.split(' (')[0]}</b><br>${fmt1(d.s)} km/h · ${MES[d.o - 1]} ${d.y}<br>inicia ${hhmm(d.t)} h`;
    }
    tip.innerHTML = html;
    tip.style.left = Math.min(info.x + 14, tip.parentElement.clientWidth - 250) + 'px';
    tip.style.top = Math.max(info.y - 10, 50) + 'px';
    tip.hidden = false;
  }

  // ---------------------------------------------------------------- leyenda = filtro
  function modeRows() {
    return MODES.map((m) => `<div class="row"><label title="Clic: activar o desactivar · doble clic: solo este"><input type="checkbox" data-mode="${m.id}" checked>
      <span class="swatch" style="background:${m.color}"></span><span>${m.label}</span><span class="n">${fmt(S.trips_by_mode[m.id] || 0)}</span></label></div>`).join('');
  }
  const legendFoot = '<div class="foot"><span class="hint">Clic: activar/desactivar · doble clic: solo</span><button type="button" class="btn small" data-legend-reset>Restablecer</button></div>';
  function buildLegend() {
    const el = $('legend');
    if (state.layer === 'objects') {
      el.innerHTML = `<div class="group"><h4>Categoría de objeto</h4>
        ${F.categories.map((c, i) => `<div class="row"><label title="Clic: activar o desactivar · doble clic: solo esta"><input type="checkbox" data-cat="${i}" checked>
          <span class="swatch" style="background:${CAT_COLORS[c.id]}"></span><span>${c.label}</span><span class="n">${fmt(c.count)}</span></label></div>`).join('')}
        ${legendFoot}</div>`;
    } else if (state.layer === 'insights') {
      el.innerHTML = `<div class="group"><h4>Tráfico por celda (km de recorrido)</h4>
        <div id="ins-classes"></div>
        <div class="hint">Cada celda es un hexágono de ~240 m. Amarillo = poco recorrido, rojo = mucho. La escala es la misma en las tres franjas, así que los colores se comparan directamente. De 00:00 a 04:00 no se muestra.</div></div>
        <div class="group"><h4>Modo de desplazamiento (inferido)</h4>${modeRows()}${legendFoot}</div>`;
    } else if (state.layer === 'density') {
      el.innerHTML = `<div class="group"><h4>Recorrido reconstruido por celda</h4>
        <div class="ramp" style="background:linear-gradient(90deg,${DENSITY_RAMP.join(',')})"></div>
        <div class="ramp-labels"><span>menos</span><span>más</span></div>
        <div class="hint">Altura y tono = km recorridos (muestras cada ~40 m). Basado en trayectorias, no en puntos.</div></div>
        <div class="group"><h4>Modo de desplazamiento (inferido)</h4>${modeRows()}${legendFoot}</div>`;
    } else {
      el.innerHTML = `<div class="group"><h4>Modo de desplazamiento (inferido)</h4>${modeRows()}
        <div class="hint">Cada trayectoria se desvanece tras pasar.</div>${legendFoot}</div>`;
    }
    syncLegend();
  }
  function syncLegend() {
    const el = $('legend');
    el.querySelectorAll('[data-cat]').forEach((cb) => { cb.checked = state.cats.has(+cb.dataset.cat); });
    el.querySelectorAll('[data-mode]').forEach((cb) => { cb.checked = state.modes.has(cb.dataset.mode); });
  }
  function resetLegendFilters() {
    state.cats = new Set(F.catIds.map((_, i) => i));
    state.modes = new Set(MODES.map((m) => m.id));
  }
  function bindLegend() {
    const el = $('legend');
    el.addEventListener('change', (e) => {
      const t = e.target;
      if (t.dataset.cat != null) { t.checked ? state.cats.add(+t.dataset.cat) : state.cats.delete(+t.dataset.cat); }
      else if (t.dataset.mode) { t.checked ? state.modes.add(t.dataset.mode) : state.modes.delete(t.dataset.mode); }
      else return;
      render();
    });
    // doble clic en un elemento = dejar solo ese
    el.addEventListener('dblclick', (e) => {
      const inp = e.target.closest('label') && e.target.closest('label').querySelector('input');
      if (!inp) return;
      if (inp.dataset.cat != null) state.cats = new Set([+inp.dataset.cat]);
      else if (inp.dataset.mode) state.modes = new Set([inp.dataset.mode]);
      else return;
      render();
    });
    el.addEventListener('click', (e) => {
      if (e.target.closest('[data-legend-reset]')) { resetLegendFilters(); render(); }
    });
  }

  // ---------------------------------------------------------------- chips de filtros activos
  function activeChips() {
    const out = [];
    const [t0, t1] = state.time;
    if (!(t0 === 0 && t1 === TIME_N - 1)) {
      const wholeYear = t0 % 12 === 0 && t1 % 12 === 11 && Math.floor(t0 / 12) === Math.floor(t1 / 12);
      out.push({ key: 'time', label: wholeYear ? String(YEAR0 + Math.floor(t0 / 12)) : `${monthLabel(t0)} – ${monthLabel(t1)}`,
        clear: () => { state.time = [0, TIME_N - 1]; } });
    }
    if (state.layer !== 'insights' && (state.hours[0] > 0 || state.hours[1] < 23)) {
      out.push({ key: 'hours', label: `${hh(state.hours[0])}:00–${hh(state.hours[1])}:59`, clear: () => { state.hours = [0, 23]; } });
    }
    if (state.layer === 'objects') {
      if (state.cats.size < F.catIds.length) {
        const n = state.cats.size;
        out.push({ key: 'cats', label: n === 0 ? 'Sin categorías' : n === 1 ? F.categories[[...state.cats][0]].label : `${n} categorías`,
          clear: () => { state.cats = new Set(F.catIds.map((_, i) => i)); } });
      }
    } else if (state.modes.size < MODES.length) {
      const n = state.modes.size;
      out.push({ key: 'modes', label: n === 0 ? 'Sin modos' : n === 1 ? MODES.find((m) => state.modes.has(m.id)).label.split(' (')[0] : `${n} modos`,
        clear: () => { state.modes = new Set(MODES.map((m) => m.id)); } });
    }
    return out;
  }
  let chipList = [];
  function renderChips() {
    chipList = activeChips();
    $('chips').innerHTML = chipList.length
      ? chipList.map((c) => `<span class="chip">${c.label}<button type="button" data-chip="${c.key}" aria-label="Quitar el filtro ${c.label}" title="Quitar filtro">✕</button></span>`).join('')
        + (chipList.length > 1 ? '<button type="button" class="link" data-chip="all">Limpiar todo</button>' : '')
      : '<span class="none">Sin filtros: se muestran todos los datos</span>';
  }
  function bindChips() {
    $('chips').addEventListener('click', (e) => {
      const b = e.target.closest('[data-chip]'); if (!b) return;
      stopSweep();
      if (b.dataset.chip === 'all') resetFilters();
      else { const c = chipList.find((x) => x.key === b.dataset.chip); if (c) c.clear(); }
      render();
    });
  }

  // ---------------------------------------------------------------- UI general
  function bindUI() {
    document.querySelectorAll('.layer-switch button').forEach((b) =>
      b.addEventListener('click', () => setLayer(b.dataset.layer)));
    bindLegend();
    bindChips();
    window.addEventListener('resize', () => { if (charts['chart-time']) updateCharts(); });
    $('play').onclick = () => { playing = !playing; syncPlayButton(); };
    document.querySelectorAll('[data-scale]').forEach((b) => b.addEventListener('click', () => {
      state.scale = b.dataset.scale;
      document.querySelectorAll('[data-scale]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
      updateCharts();
    }));
    $('t-last12').onclick = () => { stopSweep(); state.time = [Math.max(0, TIME_N - 12), TIME_N - 1]; setMenu(false); render(); };
    $('t-peak').onclick = () => {
      stopSweep();
      const cs = charts['chart-time'].counts, byYear = new Map();
      cs.forEach((v, i) => byYear.set(Math.floor(i / 12), (byYear.get(Math.floor(i / 12)) || 0) + v));
      const y = [...byYear.entries()].sort((a, b) => b[1] - a[1])[0][0];
      state.time = [y * 12, Math.min(TIME_N - 1, y * 12 + 11)]; setMenu(false); render();
    };
    $('t-play').onclick = () => { setMenu(false); sweepTimer ? stopSweep() : startSweep(); };
    // menú de opciones y opciones del reloj (se cierran al hacer clic fuera o con Escape)
    const menu = $('menu'), mbtn = $('menu-btn');
    function setMenu(open) { menu.hidden = !open; mbtn.setAttribute('aria-expanded', String(open)); }
    mbtn.onclick = (e) => { e.stopPropagation(); setMenu(menu.hidden); };
    document.addEventListener('click', (e) => { if (!menu.hidden && !menu.contains(e.target) && e.target !== mbtn) setMenu(false); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setMenu(false); });
    $('clock-more-btn').onclick = () => { const m = $('clock-more'); m.hidden = !m.hidden; $('clock-more-btn').setAttribute('aria-expanded', String(!m.hidden)); };
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
    stopSweep();
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
    const ins = layer === 'insights';
    $('insights').hidden = !ins;
    $('map').style.visibility = ins ? 'hidden' : 'visible';    // se oculta sin quitarlo del layout (conserva su tamaño)
    $('chart-hour').setAttribute('aria-disabled', String(ins));
    if (ins) state.hours = [0, 23];                            // las franjas ya dividen el día
    buildLegend();
    if (isTrips()) setClockMode(clockMode);
    if (!opts.keepView && !ins) {
      flyTo(layer === 'density' ? { pitch: 50, bearing: -15, zoom: 12.2 } : layer === 'trips' ? { zoom: 12.9, pitch: 30 } : {});
    }
    render();
  }

  // ---------------------------------------------------------------- series de tiempo (barras + selección por arrastre)
  const charts = {};
  let sweepTimer = null;
  const SCALES = { linear: (v) => v, sqrt: Math.sqrt, log: (v) => Math.log1p(v) };
  const SCALE_NAME = { linear: 'lineal', sqrt: 'raíz', log: 'log' };
  const HOUR_BANDS = [[0, 3], [4, 10], [11, 17], [18, 23]];     // franjas del eje de horas (mañana 4–10, tarde 11–17, noche 18–23)
  function makeSeries(svgId, n, getRange, setRange, labelsFn, opts = {}) {
    const svg = $(svgId);
    const W = 360, H = 92, padB = 18, padT = 12;      // se re-miden al dibujar (drawSeries)
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    const c = { svg, n, W, H, padB, padT, bw: W / n, getRange, labelsFn, useScale: !!opts.useScale, counts: [] };
    // tooltip y guía al pasar el cursor
    const host = svg.parentElement;
    const tip = document.createElement('div'); tip.className = 'chart-tip'; tip.hidden = true; host.appendChild(tip);
    const guide = document.createElement('div'); guide.className = 'chart-guide'; guide.hidden = true; host.appendChild(guide);
    const hideHover = () => { tip.hidden = true; guide.hidden = true; };
    const full = () => { const r = getRange(); return r[0] === 0 && r[1] === n - 1; };
    const idxOf = (ev) => {
      const r = svg.getBoundingClientRect();
      return Math.max(0, Math.min(n - 1, Math.floor(((ev.clientX - r.left) / r.width) * c.W / c.bw)));
    };
    const xOf = (ev) => { const r = svg.getBoundingClientRect(); return ((ev.clientX - r.left) / r.width) * c.W; };
    let drag = null;
    svg.addEventListener('pointerdown', (ev) => {
      stopSweep();
      hideHover();
      svg.setPointerCapture(ev.pointerId);
      const [r0, r1] = getRange(), x = xOf(ev), i = idxOf(ev), tol = 8;
      const onAxis = ev.clientY - svg.getBoundingClientRect().top > c.H - c.padB;
      if (onAxis && opts.axisSelect) { const r = opts.axisSelect(i); if (r) { drag = null; setRange(r); return; } }
      if (!full() && Math.abs(x - r0 * c.bw) <= tol) drag = { mode: 'left' };
      else if (!full() && Math.abs(x - (r1 + 1) * c.bw) <= tol) drag = { mode: 'right' };
      else if (!full() && i >= r0 && i <= r1) drag = { mode: 'move', grab: i, r0, r1 };
      else { drag = { mode: 'new', anchor: i }; setRange([i, i]); }
    });
    svg.addEventListener('pointermove', (ev) => {
      if (!drag) {
        const i = idxOf(ev), v = c.counts[i];
        if (v == null) return;
        const x = i * c.bw + c.bw / 2;
        tip.textContent = opts.tipFn ? opts.tipFn(i, v, c.total) : String(v);
        tip.style.left = Math.max(50, Math.min(c.W - 50, x)) + svg.offsetLeft + 'px';
        tip.style.top = svg.offsetTop + 14 + 'px';
        guide.style.left = x + svg.offsetLeft + 'px'; guide.style.top = svg.offsetTop + c.padT + 'px';
        guide.style.height = (c.H - c.padT - c.padB) + 'px';
        tip.hidden = false; guide.hidden = false;
        return;
      }
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
    svg.addEventListener('pointerleave', hideHover);
    svg.addEventListener('dblclick', () => setRange([0, n - 1]));
    svg.addEventListener('keydown', (ev) => {
      stopSweep();
      const [r0, r1] = getRange();
      const d = ev.key === 'ArrowRight' ? 1 : ev.key === 'ArrowLeft' ? -1 : 0;
      if (ev.key === 'Escape' || ev.key === 'Home') { setRange([0, n - 1]); ev.preventDefault(); }
      else if (d && ev.shiftKey) { setRange([r0, Math.max(r0, Math.min(n - 1, r1 + d))]); ev.preventDefault(); }
      else if (d) { const w = r1 - r0, a = Math.max(0, Math.min(n - 1 - w, r0 + d)); setRange([a, a + w]); ev.preventDefault(); }
    });
    charts[svgId] = c;
  }

  // Recorrido: desliza una ventana de meses por toda la serie (ancho = selección actual, o 12 meses)
  function stopSweep() {
    if (sweepTimer) { clearInterval(sweepTimer); sweepTimer = null; }
    const b = $('t-play');
    if (b) { b.setAttribute('aria-pressed', 'false'); b.textContent = '▶ Recorrer'; }
  }
  function startSweep() {
    const full = state.time[0] === 0 && state.time[1] === TIME_N - 1;
    const w = full ? 11 : state.time[1] - state.time[0];
    let a = full ? 0 : state.time[0];
    const step = () => {
      state.time = [a, a + w];
      render();
      a = a + 1 + w > TIME_N - 1 ? 0 : a + 1;
    };
    step();
    sweepTimer = setInterval(step, 450);
    const b = $('t-play'); b.setAttribute('aria-pressed', 'true'); b.textContent = '⏸ Detener';
  }

  function buildCharts() {
    makeSeries('chart-time', TIME_N, () => state.time, (r) => { state.time = r; render(); },
      (i) => (i % 12 === 0 && (YEAR0 + i / 12) % 2 === 0 ? String(YEAR0 + i / 12) : null),
      {
        useScale: true,
        tipFn: (i, v, tot) => `${monthLabel(i)} · ${fmt(v)}${tot ? ' (' + pct(v / tot, 1) + ')' : ''}`,
        axisSelect: (i) => { const a = Math.floor(i / 12) * 12; return [a, Math.min(TIME_N - 1, a + 11)]; },   // clic en el eje = año completo
      });
    makeSeries('chart-hour', 24, () => state.hours, (r) => { if (state.layer === 'insights') return; state.hours = r; render(); },
      (i) => (i % 3 === 0 ? String(i) : null),
      {
        tipFn: (i, v, tot) => `${hh(i)}:00–${hh(i)}:59 · ${fmt(v)}${tot ? ' (' + pct(v / tot, 1) + ')' : ''}`,
        axisSelect: (i) => HOUR_BANDS.find(([a, b]) => i >= a && i <= b),                                   // clic en el eje = franja del día
      });
  }

  function countBy(n, values) {
    const out = new Array(n).fill(0);
    values.forEach((v) => { if (v >= 0 && v < n) out[v]++; });
    return out;
  }

  function drawSeries(c, counts) {
    const rect = c.svg.getBoundingClientRect();       // el SVG se dibuja a 1:1 con su tamaño real
    if (rect.width > 0) {
      c.W = rect.width; c.H = rect.height || c.H; c.bw = c.W / c.n;
      c.svg.setAttribute('viewBox', `0 0 ${c.W} ${c.H}`);
    }
    const range = c.getRange();
    c.counts = counts; c.total = counts.reduce((a, b) => a + b, 0);
    const f = c.useScale ? SCALES[state.scale] : (v) => v;
    const max = Math.max(1, ...counts);
    const maxS = Math.max(1e-9, f(max));
    const plotH = c.H - c.padB - c.padT;
    let html = `<line class="axis" x1="0" x2="${c.W}" y1="${c.H - c.padB}" y2="${c.H - c.padB}"/>`;
    counts.forEach((v, i) => {
      const h = (f(v) / maxS) * plotH;
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
    if (c.svg.id === 'chart-hour' && state.layer === 'insights') {
      BANDS.forEach((b, i) => {
        const x0 = (b.lo / 60) * c.bw, x1 = (b.hi / 60) * c.bw;
        html += `<rect x="${x0}" y="${c.padT - 2}" width="${x1 - x0}" height="${c.H - c.padB - c.padT + 2}" fill="#0b5fb8" fill-opacity="${i === 1 ? 0.13 : 0.06}" stroke="#0b5fb8" stroke-opacity=".35"/>`;
        html += `<text x="${(x0 + x1) / 2}" y="9" text-anchor="middle" style="font-size:10px;font-weight:600">${b.label}</text>`;
      });
    }
    if (!(c.svg.id === 'chart-hour' && state.layer === 'insights')) html += `<text x="2" y="9" text-anchor="start">máx ${fmt.format(max)}${c.useScale && c.svg.id === 'chart-time' ? ' ' + (usesTrips() ? 'trayectorias' : 'detecciones') : ''}${c.useScale && state.scale !== 'linear' ? ' · escala ' + SCALE_NAME[state.scale] : ''}</text>`;
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
    const share = (c, [a, b]) => { const sel = c.counts.slice(a, b + 1).reduce((x, y) => x + y, 0); return c.total ? ` · ${fmt(sel)} (${pct(sel / c.total)})` : ''; };
    const ct = charts['chart-time'], ch = charts['chart-hour'];
    $('time-range').textContent = ((t0 === 0 && t1 === TIME_N - 1) ? `Todo (${monthLabel(0)} – ${monthLabel(TIME_N - 1)})` : `${monthLabel(t0)} – ${monthLabel(t1)}`) + share(ct, [t0, t1]);
    $('hour-range').textContent = state.layer === 'insights' ? 'Franjas: no aplica el filtro' : ((h0 === 0 && h1 === 23) ? 'Todo el día' : `${hh(h0)}:00 – ${hh(h1)}:59`) + share(ch, [h0, h1]);
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
        hint: 'En la leyenda: clic para activar o desactivar una categoría y doble clic para dejar solo esa.',
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
        text: `De ${fmt.format(modeTot)} trayectorias reconstruidas, ${pct(vShare)} corresponde a velocidades de vehículo motorizado (inferencia por velocidad poco fiable: tramos de ~2 s). La actividad se concentra a mediodía y primera tarde, con pico a las ${hh(S.peak_trip_hour)}:00 h (hora local); casi no hay capturas nocturnas.`,
        hint: 'Mueve el reloj de 24 h o pulsa Reproducir. Cada trayectoria se desvanece tras pasar.',
        apply: go('trips'),
      },
      {
        q: '¿Cómo cambia el recorrido durante el día?',
        text: (() => {
          const st = BANDS.map(bandStat);
          const tot = st.reduce((a, b) => a + b.km, 0);
          const early = T.filter((d) => d.t < 240).length;
          return `Entre 04:00 y 24:00 se reconstruyen ≈ ${fmt.format(Math.round(tot))} km: la tarde concentra el ${pct(st[1].km / tot)}, la mañana el ${pct(st[0].km / tot)} y la noche el ${pct(st[2].km / tot)}. Dentro de cada franja, el 10 % de las celdas más recorridas reúne el ${pct(st[0].topShare)} (mañana), ${pct(st[1].topShare)} (tarde) y ${pct(st[2].topShare)} (noche) del recorrido. ${fmt.format(early)} trayectorias ocurren entre 00:00 y 04:00 y no se muestran.`;
        })(),
        hint: 'Mueve o acerca un mapa: los tres se mueven a la vez. Comparten escala de color: amarillo = poco recorrido, rojo = mucho.',
        apply: go('insights'),
      },
      {
        q: 'Conclusión provisional y límites',
        text: 'Mapillary describe bien dónde y cuándo se ha mirado la ciudad, pero no es un censo: la cobertura la determinan pocas campañas y dispositivos, y el modo de desplazamiento es solo una inferencia por velocidad. Cualquier lectura "urbana" debe ir acompañada de la pregunta: ¿quién capturó y cuándo?',
        hint: 'Explora libremente: todos los filtros siguen activos.',
        apply: go('objects'),
      },
    ];
  }
  // ---------------------------------------------------------------- insights: tres mapas de celdas coloreadas por tráfico
  const LAT0 = 50.09, LON0 = 14.38;
  const MX = 111320 * Math.cos(LAT0 * Math.PI / 180), MY = 110574;           // metros por grado de longitud y latitud
  const INS_RGB = INS_RAMP.map(hex2rgb);
  // Hexágonos de lados planos (coordenadas axiales); R = radio en metros
  function hexOf(lon, lat, R) {
    const x = (lon - LON0) * MX, y = (lat - LAT0) * MY;
    const q = (2 / 3 * x) / R, r = (-1 / 3 * x + Math.sqrt(3) / 3 * y) / R;
    let rx = Math.round(q), rz = Math.round(r), ry = Math.round(-q - r);
    const dx = Math.abs(rx - q), dy = Math.abs(ry + q + r), dz = Math.abs(rz - r);
    if (dx > dy && dx > dz) rx = -ry - rz; else if (dy > dz) ry = -rx - rz; else rz = -rx - ry;
    return [rx, rz];
  }
  function hexCenter(q, r, R) {
    return [LON0 + (R * 1.5 * q) / MX, LAT0 + (R * Math.sqrt(3) * (r + q / 2)) / MY];
  }
  function binCells(points) {
    const m = new Map();
    for (const p of points) {
      const [q, r] = hexOf(p[0], p[1], INS_R), k = q + ',' + r;
      const c = m.get(k);
      if (c) c.n++; else m.set(k, { q, r, n: 1 });
    }
    return [...m.values()];
  }
  // Cortes de clase compartidos por las tres franjas (percentiles de las celdas con recorrido)
  function classBreaks(allKm) {
    if (!allKm.length) return [0.1, 0.2, 0.4, 0.8];
    const v = allKm.slice().sort((a, b) => a - b);
    const at = (p) => v[Math.min(v.length - 1, Math.floor(p * v.length))];
    const nice = (x) => (x < 1 ? Math.max(0.1, Math.round(x * 10) / 10) : Math.round(x));
    const b = [at(0.5), at(0.75), at(0.9), at(0.97)].map(nice);
    for (let i = 1; i < b.length; i++) if (b[i] <= b[i - 1]) b[i] = +(b[i - 1] + (b[i - 1] < 1 ? 0.1 : 1)).toFixed(1);
    return b;
  }
  const fkm = (x) => (x < 1 ? x.toFixed(1) : String(Math.round(x))).replace('.', ',');
  let insPanes = null, insView = null, insTips = [];
  function ensureInsights() {
    if (insPanes) return;
    insView = Object.assign(baseView(), { zoom: 11.6 });
    insPanes = BANDS.map((b, i) => {
      const host = $('ins-map-' + i);
      const tip = document.createElement('div'); tip.className = 'pane-tip'; tip.hidden = true; host.appendChild(tip); insTips[i] = tip;
      return new deck.DeckGL({
        container: host, map: maplibregl, mapStyle: MAP_STYLE, viewState: insView, controller: true,
        // las tres vistas comparten cámara: mover una mueve las demás
        onViewStateChange: ({ viewState }) => { insView = viewState; insPanes.forEach((pn) => pn.setProps({ viewState: insView })); },
        onHover: (info) => {
          try {
            if (!info || !info.object) { tip.hidden = true; return; }
            tip.innerHTML = `<b>≈ ${fkm(info.object.km)} km</b> de recorrido<br>en esta celda (~240 m)<br><span class="muted">${b.label} ${b.range}</span>`;
            tip.style.left = Math.min(info.x + 12, host.clientWidth - 200) + 'px';
            tip.style.top = Math.max(info.y - 10, 4) + 'px';
            tip.hidden = false;
          } catch (e) { tip.hidden = true; }
        },
      });
    });
  }
  function renderInsights() {
    ensureInsights();
    const trips = getTrips();
    const per = BANDS.map((b) => trips.filter((d) => d.t >= b.lo && d.t < b.hi));
    const cells = per.map((tr) => binCells(tr.flatMap((d) => d.s)));
    cells.forEach((cs) => cs.forEach((c) => { c.km = c.n * SAMPLE_KM; }));
    const br = classBreaks(cells.flatMap((cs) => cs.map((c) => c.km)));
    const cls = (km) => (km > br[3] ? 4 : km > br[2] ? 3 : km > br[1] ? 2 : km > br[0] ? 1 : 0);
    const kms = per.map((tr) => tr.reduce((a, d) => a + d.s.length, 0) * SAMPLE_KM);
    const totKm = kms.reduce((a, b) => a + b, 0) || 1;
    BANDS.forEach((b, i) => {
      const data = cells[i].map((c) => ({ pos: hexCenter(c.q, c.r, INS_R), km: c.km, cls: cls(c.km) }));
      insPanes[i].setProps({
        layers: [new deck.ColumnLayer({
          id: 'ins-' + b.id, data, pickable: true, extruded: false, diskResolution: 6, radius: INS_R * 0.98,
          getPosition: (d) => d.pos, getFillColor: (d) => [...INS_RGB[d.cls], 235], updateTriggers: { getFillColor: [br.join()] },
        })],
      });
      $('ins-stats-' + i).textContent = `${fmt(per[i].length)} trayectorias · ≈ ${fmt(Math.round(kms[i]))} km · ${pct(kms[i] / totKm)}`;
    });
    const box = $('ins-classes');
    if (box) {
      const lab = [`≤ ${fkm(br[0])} km`, `${fkm(br[0])} – ${fkm(br[1])} km`, `${fkm(br[1])} – ${fkm(br[2])} km`, `${fkm(br[2])} – ${fkm(br[3])} km`, `> ${fkm(br[3])} km`];
      box.innerHTML = lab.map((t, k) => `<div class="cls"><span class="swatch" style="background:${INS_RAMP[k]}"></span><span>${t}${k === 0 ? ' <span class="muted">(poco)</span>' : k === 4 ? ' <span class="muted">(mucho)</span>' : ''}</span></div>`).join('');
    }
  }
  // Estadísticas de una franja con todos los datos (para el texto del recorrido guiado)
  function bandStat(b) {
    const tr = T.filter((d) => d.t >= b.lo && d.t < b.hi);
    const pts = tr.flatMap((d) => d.s);
    const cells = new Map();
    pts.forEach(([x, y]) => { const k = Math.floor(x / 0.0013) + '|' + Math.floor(y / 0.0009); cells.set(k, (cells.get(k) || 0) + 1); });
    const v = [...cells.values()].sort((a, c) => c - a);
    const top = v.slice(0, Math.max(1, Math.floor(v.length / 10))).reduce((a, c) => a + c, 0);
    return { n: tr.length, km: pts.length * SAMPLE_KM, topShare: top / (pts.length || 1) };
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
