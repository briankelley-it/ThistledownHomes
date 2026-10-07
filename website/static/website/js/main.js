'use strict';
/* Thistledown Homes page behavior. Content comes from Django; this file only
   adds interactivity, and every page still works without it. */
(() => {
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];

  /* ---------- Saved homes (localStorage, only with Preferences consent; see site.js) ---------- */
  const KEY = 'tdh-saved';
  const canStore = () => window.tdhConsent?.allows('preferences');
  let saved = new Set();
  if (canStore()) { try { const s = JSON.parse(localStorage.getItem(KEY) || '[]'); if (Array.isArray(s)) saved = new Set(s); } catch {} }
  const store = () => { if (canStore()) { try { localStorage.setItem(KEY, JSON.stringify([...saved])); } catch {} } };
  document.addEventListener('tdh:consent', store);

  function paintSaved() {
    $$('[data-save]').forEach(b => { const on = saved.has(b.dataset.save); b.classList.toggle('on', on); b.setAttribute('aria-pressed', on); });
  }
  function toast(html, ms = 5000) {
    const t = $('#toast'); if (!t) return;
    t.innerHTML = html; t.classList.add('show');
    clearTimeout(toast.timer); toast.timer = setTimeout(() => t.classList.remove('show'), ms);
  }

  /* ---------- Homes list: filters apply on change, "Saved only" filters in the browser ---------- */
  const filters = $('#filters');
  if (filters) {
    $$('select', filters).forEach(sel => sel.addEventListener('change', () => filters.submit()));
    const savedOnly = $('#saved-only');
    const applySavedOnly = () => {
      const cards = $$('#property-grid .property-card');
      let shown = 0;
      cards.forEach(c => { const show = !savedOnly.checked || saved.has(c.dataset.home); c.hidden = !show; if (show) shown++; });
      $('#saved-empty').hidden = !(savedOnly.checked && shown === 0);
      if (savedOnly.checked) $('#result-count').textContent = `Showing ${shown} saved ${shown === 1 ? 'home' : 'homes'}`;
    };
    savedOnly.addEventListener('change', applySavedOnly);
    document.addEventListener('tdh:saved', () => { if (savedOnly.checked) applySavedOnly(); });
  }

  /* ---------- Clicks ---------- */
  document.addEventListener('click', e => {
    const save = e.target.closest('[data-save]');
    if (save) {
      const id = save.dataset.save;
      saved.has(id) ? saved.delete(id) : saved.add(id);
      store(); paintSaved();
      document.dispatchEvent(new Event('tdh:saved'));
      if (saved.has(id) && !canStore()) toast('Saved for this visit. <button type="button" class="privacy-choices">Allow saving</button> to keep favorites next time.');
      return;
    }
    const thumb = e.target.closest('[data-photo]');
    if (thumb) {
      const main = $('#detail-main');
      main.src = thumb.dataset.photo; main.alt = thumb.dataset.alt;
      $$('.detail-thumbs button').forEach(b => b.classList.toggle('active', b === thumb));
    }
  });

  /* ---------- Investment numbers tabs (WAI-ARIA tabs pattern) ---------- */
  const tablist = $('.numbers-tabs');
  if (tablist) {
    const tabs = $$('[role="tab"]', tablist);
    const select = tab => {
      tabs.forEach(t => {
        const on = t === tab;
        t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1;
        $('#' + t.getAttribute('aria-controls')).hidden = !on;
      });
    };
    tablist.addEventListener('click', e => { const t = e.target.closest('[role="tab"]'); if (t) select(t); });
    tablist.addEventListener('keydown', e => {
      const i = tabs.indexOf(document.activeElement);
      if (i < 0 || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
      e.preventDefault();
      const next = e.key === 'Home' ? 0 : e.key === 'End' ? tabs.length - 1 : (i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length;
      select(tabs[next]); tabs[next].focus();
    });
  }

  /* ---------- Light / dark theme (light by default; the choice is remembered) ---------- */
  const themeBtn = $('.theme-toggle');
  const applyTheme = theme => {
    document.documentElement.dataset.theme = theme;
    const dark = theme === 'dark';
    themeBtn?.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
    themeBtn?.setAttribute('aria-pressed', dark);
    const meta = $('meta[name="theme-color"]'); if (meta) meta.content = dark ? '#0f1113' : '#ffffff';
  };
  applyTheme(document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light');
  themeBtn?.addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    try { localStorage.setItem('tdh-theme', next); } catch { /* Still switches for this page view. */ }
  });

  /* ---------- Chat bubble (saves a message; replaced by Tawk.to when configured) ---------- */
  const chat = $('#chat');
  if (chat) {
    const launcher = $('.chat-launcher', chat), panel = $('#chat-panel'), form = $('#chat-form'), status = $('.chat-status', form);
    const setOpen = open => {
      panel.hidden = !open;
      chat.classList.toggle('open', open);
      launcher.setAttribute('aria-expanded', open);
      launcher.setAttribute('aria-label', open ? 'Close chat' : 'Open chat');
      if (open) form.elements.tdh_who.focus();
    };
    launcher.addEventListener('click', () => setOpen(panel.hidden));
    $('.chat-close', chat).addEventListener('click', () => { setOpen(false); launcher.focus(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && !panel.hidden) { setOpen(false); launcher.focus(); } });

    /* Browser autofill stays off (fields are read-only until focused and use names Chrome does not
       recognize). Instead, only entries sent from this form before are suggested, and only when
       Preferences storage is allowed. */
    const RECENT = 'tdh-chat-recent';
    const recent = () => { if (!canStore()) return {}; try { return JSON.parse(localStorage.getItem(RECENT) || '{}') || {}; } catch { return {}; } };
    const remember = () => {
      if (!canStore()) return;
      const r = recent();
      $$('[data-recall]', form).forEach(f => {
        const v = f.value.trim(); if (!v) return;
        const list = Array.isArray(r[f.dataset.field]) ? r[f.dataset.field] : [];
        r[f.dataset.field] = [v, ...list.filter(x => x.toLowerCase() !== v.toLowerCase())].slice(0, 5);
      });
      try { localStorage.setItem(RECENT, JSON.stringify(r)); } catch {}
    };
    $$('[data-recall]', form).forEach(input => {
      const unlock = () => input.removeAttribute('readonly');
      input.addEventListener('focus', () => requestAnimationFrame(unlock));
      input.addEventListener('pointerdown', unlock);
      const box = document.createElement('ul');
      box.className = 'recall'; box.id = `recall-${input.dataset.field}`; box.setAttribute('role', 'listbox'); box.hidden = true;
      input.after(box);
      input.setAttribute('role', 'combobox'); input.setAttribute('aria-controls', box.id); input.setAttribute('aria-expanded', 'false');
      let idx = -1;
      const close = () => { box.hidden = true; idx = -1; input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); };
      const pick = v => { input.value = v; close(); };
      const show = () => {
        const q = input.value.trim().toLowerCase();
        const items = (recent()[input.dataset.field] || []).filter(v => typeof v === 'string' && v.toLowerCase().startsWith(q) && v.toLowerCase() !== q);
        box.replaceChildren(...items.map((v, i) => {
          const li = document.createElement('li');
          li.id = `${box.id}-${i}`; li.setAttribute('role', 'option'); li.textContent = v;
          li.addEventListener('mousedown', e => { e.preventDefault(); pick(v); });
          return li;
        }));
        idx = -1; box.hidden = !items.length; input.setAttribute('aria-expanded', String(!!items.length));
      };
      const move = d => {
        const opts = $$('li', box); if (!opts.length) return;
        idx = (idx + d + opts.length) % opts.length;
        opts.forEach((o, i) => o.setAttribute('aria-selected', i === idx));
        input.setAttribute('aria-activedescendant', opts[idx].id);
      };
      input.addEventListener('focus', show);
      input.addEventListener('input', show);
      input.addEventListener('blur', close);
      input.addEventListener('keydown', e => {
        if (box.hidden) { if (e.key === 'ArrowDown') { show(); e.preventDefault(); } return; }
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { move(e.key === 'ArrowDown' ? 1 : -1); e.preventDefault(); }
        else if (e.key === 'Enter' && idx > -1) { pick($$('li', box)[idx].textContent); e.preventDefault(); }
        else if (e.key === 'Escape') { close(); e.stopPropagation(); }
      });
    });

    form.addEventListener('submit', async e => {
      e.preventDefault();
      if (!form.reportValidity()) return;
      const btn = $('button[type="submit"]', form);
      btn.disabled = true; status.className = 'chat-status'; status.textContent = 'Sending...';
      try {
        const body = new FormData(form);
        $$('[data-field]', form).forEach(f => { body.set(f.dataset.field, f.value.trim()); body.delete(f.name); });
        const res = await fetch(form.action, { method: 'POST', body });
        const data = await res.json();
        if (!data.ok) throw new Error(Object.values(data.errors || {}).flat()[0] || 'Please check the form.');
        remember();
        form.reset();
        status.textContent = 'Thanks! Your message was sent. I will reply by email.';
        status.classList.add('ok');
      } catch (err) {
        status.textContent = err instanceof SyntaxError || err.message === 'Failed to fetch' ? 'Could not send right now. Please try the contact page.' : err.message;
        status.classList.add('err');
      } finally { btn.disabled = false; }
    });
  }

  /* ---------- Start-an-offer form: money formatting and fields that depend on answers ---------- */
  const money = $('[data-money]');
  if (money) {
    const compare = $('#offer-compare'), asking = +compare.dataset.asking;
    const fmt = n => '$' + n.toLocaleString('en-US');
    const update = () => {
      const digits = money.value.replace(/\D/g, '').slice(0, 9);
      const n = +digits;
      money.value = digits ? n.toLocaleString('en-US') : '';
      if (!n) { compare.textContent = `Asking price: ${fmt(asking)}`; compare.classList.remove('is-over'); return; }
      const diff = n - asking;
      compare.textContent = diff === 0 ? 'Matches the asking price'
        : `${fmt(Math.abs(diff))} ${diff > 0 ? 'above' : 'below'} the asking price of ${fmt(asking)}`;
      compare.classList.toggle('is-over', diff >= 0);
    };
    money.addEventListener('input', update); update();

    const financing = $('#id_financing'), lender = $('#lender-row');
    const showLender = () => { lender.hidden = !['preapproved', 'mortgage'].includes(financing.value); };
    financing.addEventListener('change', showLender); showLender();
    const hasAgent = $('#id_has_agent'), agent = $('#agent-row');
    const showAgent = () => { agent.hidden = !hasAgent.checked; };
    hasAgent.addEventListener('change', showAgent); showAgent();
  }

  /* ---------- Back-to-top arrow (bottom left, after scrolling down) ---------- */
  const toTop = $('.to-top');
  if (toTop) {
    const showToTop = () => { toTop.hidden = scrollY < 500; };
    addEventListener('scroll', showToTop, { passive: true }); showToTop();
    toTop.addEventListener('click', () => {
      scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
      $('.brand')?.focus({ preventScroll: true, focusVisible: false });
    });
  }

  /* ---------- Hero background video: always autoplay and loop, with a pause button ---------- */
  const video = $('#hero-video');
  if (video) {
    const toggle = $('.video-toggle');
    let userPaused = false;
    video.muted = true; video.loop = true; video.playsInline = true;
    const start = () => { if (!userPaused) video.play().catch(() => {}); };
    const paint = () => {
      const paused = video.paused;
      toggle.classList.toggle('is-paused', paused);
      toggle.setAttribute('aria-pressed', paused);
      toggle.setAttribute('aria-label', paused ? 'Play background video' : 'Pause background video');
    };
    // Start on load, on reload or Back navigation, and whenever the tab becomes visible again.
    start();
    video.addEventListener('canplay', start, { once: true });
    addEventListener('pageshow', start);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) start(); });
    // Safety net: if the video ever stalls at the end, restart it.
    video.addEventListener('ended', () => { video.currentTime = 0; start(); });
    video.addEventListener('play', paint); video.addEventListener('pause', paint);
    toggle.addEventListener('click', () => {
      if (video.paused) { userPaused = false; video.play().catch(() => {}); } else { userPaused = true; video.pause(); }
    });
    paint();
  }

  /* ---------- Hero photo shape morphs toward the mouse ---------- */
  const bubble = $('.profile-bubble');
  const fancyPointer = matchMedia('(hover: hover) and (pointer: fine)').matches && !matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (bubble && fancyPointer) {
    const area = bubble.closest('.hero') || document.body;
    // Resting leaf shape: sharp left point (r1), rounded top (r2), soft right point (r3), rounded bottom (r4).
    const rest = { r1: 0, r2: 50, r3: 24, r4: 50, tx: 0, ty: 0 };
    const now = { ...rest }, goal = { ...rest };
    let frame = 0;
    const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
    const tick = () => {
      let moving = false;
      for (const k in now) {
        const d = goal[k] - now[k];
        if (Math.abs(d) > 0.05) { now[k] += d * 0.09; moving = true; } else now[k] = goal[k];
      }
      bubble.style.setProperty('--r1', now.r1.toFixed(2));
      bubble.style.setProperty('--r2', now.r2.toFixed(2));
      bubble.style.setProperty('--r3', now.r3.toFixed(2));
      bubble.style.setProperty('--r4', now.r4.toFixed(2));
      bubble.style.setProperty('--tx', now.tx.toFixed(2) + 'px');
      bubble.style.setProperty('--ty', now.ty.toFixed(2) + 'px');
      frame = moving ? requestAnimationFrame(tick) : 0;
    };
    const kick = () => { if (!frame) frame = requestAnimationFrame(tick); };
    area.addEventListener('pointermove', e => {
      const r = bubble.getBoundingClientRect();
      // -1..1 position of the mouse relative to the shape's center.
      const nx = clamp((e.clientX - (r.left + r.width / 2)) / (r.width * 1.2), -1, 1);
      const ny = clamp((e.clientY - (r.top + r.height / 2)) / (r.height * 1.2), -1, 1);
      goal.r1 = clamp(-nx * 22, 0, 22);            // left point softens when the mouse is on the left
      goal.r2 = 50 + ny * -14;                      // top swells toward a mouse above
      goal.r3 = clamp(24 + nx * 22, 4, 46);         // right point rounds toward a mouse on the right
      goal.r4 = 50 + ny * 14;                       // bottom swells toward a mouse below
      goal.tx = nx * 14; goal.ty = ny * 14;         // gentle drift toward the cursor
      kick();
    });
    area.addEventListener('pointerleave', () => { Object.assign(goal, rest); kick(); });
  }

  /* ---------- Header shadow and reveal-on-scroll ---------- */
  const header = $('.site-header');
  const onScroll = () => header.classList.toggle('scrolled', scrollY > 10);
  addEventListener('scroll', onScroll, { passive: true }); onScroll();

  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if ('IntersectionObserver' in window && !reduceMotion) {
    document.documentElement.classList.add('motion');
    const io = new IntersectionObserver(entries => entries.forEach(en => {
      if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
    }), { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    $$('.reveal').forEach(el => io.observe(el));
  } else {
    $$('.reveal').forEach(el => el.classList.add('in'));
  }

  paintSaved();
})();
