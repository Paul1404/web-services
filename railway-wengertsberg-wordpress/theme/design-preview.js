(() => {
  'use strict';
  if (!document.body.classList.contains('design-preview')) return;
  // Keep section navigation inside this review view. Legal/direct contact and
  // the explicitly labelled original-view link retain their real destinations.
  const current = new URL(location.href);
  document.querySelectorAll('a[href]').forEach(link => {
    if (link.hasAttribute('data-original-view')) return;
    const next = new URL(link.href, current);
    if (next.origin === current.origin && next.pathname === current.pathname && (next.hash || link.classList.contains('brand'))) {
      next.searchParams.set('entwurf', '2');
      link.href = next.href;
    }
  });
  [['[data-preview-notes]', '#preview-notes'], ['[data-preview-consent]', '#preview-consent']].forEach(([selector, id]) => {
    const trigger = document.querySelector(selector);
    const dialog = document.querySelector(id);
    if (!trigger || !dialog) return;
    trigger.addEventListener('click', () => dialog.showModal());
    dialog.querySelector('[data-close-preview]')?.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener('close', () => trigger.focus());
  });
})();
