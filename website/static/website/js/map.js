'use strict';
/* Homes map (MapLibre GL + OpenFreeMap): custom price pins, synced with the list beside the map,
   status filters, and a light/dark map style that follows the site theme. */
(() => {
  const el = document.getElementById('map');
  const data = document.getElementById('map-pins');
  if (!el || !data || !window.maplibregl) return;

  const pins = JSON.parse(data.textContent);
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const money = n => '$' + n.toLocaleString('en-US');
  const short = n => '$' + Math.round(n / 1000) + 'K';
  const esc = v => String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const styleFor = () => document.documentElement.dataset.theme === 'dark' ? el.dataset.styleDark : el.dataset.styleLight;

  const map = new maplibregl.Map({
    container: el,
    style: styleFor(),
    center: [-98.5, 30.3],
    zoom: 6,
    attributionControl: { compact: true },
    cooperativeGestures: false,
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
  map.scrollZoom.setWheelZoomRate(1 / 300);

  const markers = new Map();
  const items = new Map([...document.querySelectorAll('.map-item')].map(li => [li.dataset.slug, li]));

  const popupHtml = p => `
    <div class="pin-card">
      ${p.photo ? `<img src="${esc(p.photo)}" alt="" width="800" height="560">` : ''}
      <div class="pin-card-body">
        <span class="pin-card-status map-status map-status-${esc(p.status)}">${esc(p.status_label)}</span>
        <p class="pin-card-price">${money(p.price)}${p.savings ? ` <small>${short(p.savings)} under nearby</small>` : ''}</p>
        <p class="pin-card-addr">${esc(p.address)}</p>
        <p class="pin-card-meta">${esc(p.location)} · ${p.beds} bd · ${p.baths} ba · ${p.sqft.toLocaleString('en-US')} sq ft</p>
        <a class="btn btn-small btn-block" href="${esc(p.url)}">View home <span aria-hidden="true">→</span></a>
      </div>
    </div>`;

  const setActive = (slug, on) => {
    markers.get(slug)?.getElement().classList.toggle('is-active', on);
    items.get(slug)?.classList.toggle('is-active', on);
  };
  const select = slug => {
    document.querySelectorAll('.map-item.is-selected').forEach(li => li.classList.remove('is-selected'));
    const li = items.get(slug);
    if (li) { li.classList.add('is-selected'); li.scrollIntoView({ block: 'nearest', behavior: reduceMotion ? 'auto' : 'smooth' }); }
  };

  pins.forEach(p => {
    const node = document.createElement('button');
    node.type = 'button';
    node.className = `pin pin-${p.status}`;
    node.setAttribute('aria-label', `${p.address}, ${money(p.price)}`);
    node.innerHTML = `<span>${short(p.price)}</span>`;
    const popup = new maplibregl.Popup({ offset: 30, className: 'pin-popup', maxWidth: '280px', focusAfterOpen: false })
      .setHTML(popupHtml(p));
    popup.on('open', () => select(p.slug));
    const marker = new maplibregl.Marker({ element: node, anchor: 'bottom' })
      .setLngLat([p.lng, p.lat]).setPopup(popup).addTo(map);
    node.addEventListener('mouseenter', () => setActive(p.slug, true));
    node.addEventListener('mouseleave', () => setActive(p.slug, false));
    markers.set(p.slug, marker);
  });

  // List -> map.
  const openHome = slug => {
    const m = markers.get(slug); if (!m) return;
    const show = () => { if (!m.getPopup().isOpen()) m.togglePopup(); };
    if (reduceMotion) { map.jumpTo({ center: m.getLngLat(), zoom: 13 }); show(); }
    else { map.flyTo({ center: m.getLngLat(), zoom: 13, duration: 900 }); map.once('moveend', show); }
  };
  items.forEach((li, slug) => {
    li.addEventListener('mouseenter', () => setActive(slug, true));
    li.addEventListener('mouseleave', () => setActive(slug, false));
    li.querySelector('[data-fly]')?.addEventListener('click', () => openHome(slug));
  });

  // Status filters.
  const shown = new Set([...document.querySelectorAll('.map-chip')].map(c => c.dataset.status));
  const count = document.getElementById('map-count');
  const fit = () => {
    const visible = pins.filter(p => shown.has(p.status));
    if (!visible.length) return map.jumpTo({ center: [-98.5, 30.3], zoom: 5 });
    const b = new maplibregl.LngLatBounds();
    visible.forEach(p => b.extend([p.lng, p.lat]));
    map.fitBounds(b, { padding: 70, maxZoom: 12, animate: !reduceMotion, duration: 600 });
  };
  const apply = () => {
    let n = 0;
    pins.forEach(p => {
      const on = shown.has(p.status), m = markers.get(p.slug);
      if (on) { m.addTo(map); n++; } else { m.getPopup().remove(); m.remove(); }
      const li = items.get(p.slug); if (li) li.hidden = !on;
    });
    count.textContent = `${n} ${n === 1 ? 'home' : 'homes'}`;
    fit();
  };
  document.querySelectorAll('.map-chip').forEach(chip => chip.addEventListener('click', () => {
    const s = chip.dataset.status, on = chip.getAttribute('aria-pressed') !== 'true';
    chip.setAttribute('aria-pressed', on);
    on ? shown.add(s) : shown.delete(s);
    apply();
  }));

  // Follow the site's light/dark switch.
  new MutationObserver(() => map.setStyle(styleFor())).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  // Re-measure whenever the map's box changes size; fit the first time it has a real size.
  let fitted = false;
  const ready = () => el.clientWidth > 0 && el.clientHeight > 0;
  map.on('load', () => {
    apply();
    fitted = ready();
    const target = decodeURIComponent(location.hash.slice(1));
    if (markers.has(target)) openHome(target);
  });
  new ResizeObserver(() => {
    map.resize();
    if (!fitted && ready() && map.loaded()) { fitted = true; fit(); }
  }).observe(el);
})();
