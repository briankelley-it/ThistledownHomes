/* Loaded only in the static export (python manage.py export_static), where there is no server.
   Forms show a notice instead of sending, and the homes filters run in the browser. */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  // Capture phase runs before the page's own submit handlers, so nothing is posted.
  document.addEventListener('submit', e => {
    const form = e.target;
    if (form.id === 'filters') { e.preventDefault(); return; }
    if (form.method !== 'post') return;  // e.g. the cookie choices form, which runs in the browser
    e.preventDefault();
    e.stopPropagation();
    let note = $('.static-note', form);
    if (!note) {
      note = document.createElement('p');
      note.className = 'flash static-note';
      note.setAttribute('role', 'status');
      form.append(note);
    }
    note.textContent = 'This is a static demo of a fictional company, so forms are turned off. Nothing was sent.';
  }, true);

  const filters = $('#filters');
  if (!filters) return;
  const savedOnly = $('#saved-only');
  const count = $('#result-count');
  const savedEmpty = $('#saved-empty');
  const cards = $$('#property-grid .property-card');
  const noMatch = document.createElement('div');
  noMatch.className = 'empty';
  noMatch.hidden = true;
  noMatch.innerHTML = '<h3>No homes match those filters.</h3><p>Try widening your price or location.</p>';
  $('#property-grid').after(noMatch);

  const apply = () => {
    const v = name => filters.elements[name]?.value || '';
    const price = v('price'), beds = v('beds'), loc = v('location'), status = v('status');
    let shown = 0;
    cards.forEach(c => {
      const d = c.dataset;
      const show = (!price || +d.price <= +price) && (!beds || +d.beds >= +beds)
        && (!loc || d.location === loc) && (!status || d.status === status)
        && (!savedOnly.checked || $('[data-save]', c)?.getAttribute('aria-pressed') === 'true');
      c.hidden = !show;
      if (show) shown++;
    });
    savedEmpty.hidden = !(savedOnly.checked && shown === 0);
    noMatch.hidden = shown > 0 || savedOnly.checked;
    count.textContent = `Showing ${shown} of ${cards.length} homes`;
  };
  // Stop the selects from submitting to a server that is not there.
  filters.addEventListener('change', e => { e.stopPropagation(); apply(); }, true);
  document.addEventListener('tdh:saved', apply);
})();
