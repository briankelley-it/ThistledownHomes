'use strict';

// Shared on every page: mobile menu, footer year, and cookie/storage consent.
// Consent model (US state privacy laws): essential storage always runs; anything else waits for a choice.
// A browser Global Privacy Control signal is treated as an opt-out and cannot be overridden by the banner.
(() => {
  // Read from the footer link so it works when the site is served from a sub-path.
  const privacyUrl = document.querySelector('.legal-links a[href$="/privacy/"]')?.getAttribute('href') || '/privacy/';
  const $ = selector => document.querySelector(selector);
  const KEY = 'tdh-consent';
  const VERSION = 1;
  const gpc = navigator.globalPrivacyControl === true;

  function readConsent() {
    try { const c = JSON.parse(localStorage.getItem(KEY) || 'null'); return c && c.v === VERSION ? c : null; } catch { return null; }
  }
  let consent = readConsent();
  if (consent && gpc) consent.analytics = false;

  // Other scripts check window.tdhConsent.allows('preferences' | 'analytics') and listen for 'tdh:consent'.
  // Add any future analytics or marketing tag inside an tdh:consent listener so it never loads without consent.
  window.tdhConsent = {
    allows: category => category === 'essential' || Boolean(consent && consent[category]),
    gpc,
    open: () => openPreferences()
  };

  function save(preferences, analytics) {
    consent = {v: VERSION, preferences, analytics: gpc ? false : analytics, date: new Date().toISOString()};
    try { localStorage.setItem(KEY, JSON.stringify(consent)); } catch { /* Choice still applies for this visit. */ }
    if (!preferences) { try { localStorage.removeItem('tdh-saved'); } catch {} }
    banner?.remove();
    document.dispatchEvent(new CustomEvent('tdh:consent', {detail: consent}));
  }

  let banner;
  function showBanner() {
    banner = document.createElement('section');
    banner.className = 'consent-banner';
    banner.setAttribute('aria-label', 'Cookie and storage choices');
    banner.innerHTML = `<div><h2>Your privacy choices</h2><p>We use essential browser storage to run this site. With your permission we also remember the homes you save. We do not sell your personal information or use advertising trackers.${gpc ? ' <strong>Your browser’s Global Privacy Control signal is on, and we honor it.</strong>' : ''} <a href="${privacyUrl}#cookies">Learn more</a></p></div><div class="consent-actions"><button class="button" data-consent="all">Accept all</button><button class="button secondary" data-consent="essential">Essential only</button><button class="text-link" data-consent="customize">Customize</button></div>`;
    document.body.append(banner);
  }

  function openPreferences() {
    let dialog = $('#consent-dialog');
    if (!dialog) {
      dialog = document.createElement('dialog');
      dialog.id = 'consent-dialog';
      dialog.innerHTML = `<button class="close-dialog" aria-label="Close privacy choices">×</button><div class="modal-inner"><p class="eyebrow">COOKIES AND STORAGE</p><h2>Privacy <span class="serif">choices.</span></h2><form id="consent-form"><label class="consent-row"><input type="checkbox" checked disabled><span><strong>Essential</strong>Remembers your privacy choices and keeps the site working. Always on.</span></label><label class="consent-row"><input type="checkbox" name="preferences"><span><strong>Preferences</strong>Remembers homes you save with the heart button on this device.</span></label><label class="consent-row"><input type="checkbox" name="analytics"${gpc ? ' disabled' : ''}><span><strong>Analytics</strong>Not currently used. If we add site measurement later, it stays off unless you turn it on.${gpc ? ' Turned off by your Global Privacy Control signal.' : ''}</span></label><p class="form-note">We do not sell or share personal information for targeted advertising. Details are in our <a href="${privacyUrl}">Privacy Policy</a>.</p><button class="button" type="submit">Save my choices <span>↗</span></button></form></div>`;
      document.body.append(dialog);
      dialog.querySelector('.close-dialog').addEventListener('click', () => dialog.close());
      dialog.querySelector('form').addEventListener('submit', e => { e.preventDefault(); const f = e.target; save(f.preferences.checked, f.analytics.checked); dialog.close(); });
    }
    const f = dialog.querySelector('form');
    f.preferences.checked = Boolean(consent?.preferences);
    f.analytics.checked = Boolean(consent?.analytics) && !gpc;
    document.querySelectorAll('dialog[open]').forEach(d => d.close());
    dialog.showModal();
  }

  document.addEventListener('click', e => {
    const choice = e.target.closest('[data-consent]')?.dataset.consent;
    if (choice === 'all') save(true, true);
    else if (choice === 'essential') save(false, false);
    else if (choice === 'customize' || e.target.closest('.privacy-choices')) { e.preventDefault(); openPreferences(); }
  });
  if (!consent) showBanner();

  const menu = $('.menu-toggle'), nav = $('#main-nav');
  if (menu && nav) {
    const close = () => { nav.classList.remove('open'); menu.setAttribute('aria-expanded', 'false'); menu.setAttribute('aria-label', 'Open menu'); };
    menu.addEventListener('click', () => { const open = nav.classList.toggle('open'); menu.setAttribute('aria-expanded', open); menu.setAttribute('aria-label', open ? 'Close menu' : 'Open menu'); });
    nav.addEventListener('click', e => { if (e.target.closest('a')) close(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
  }
  document.querySelectorAll('.year').forEach(el => { el.textContent = new Date().getFullYear(); });
})();
