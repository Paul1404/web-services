'use strict';
document.documentElement.classList.add('js');
const toggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('.site-nav');
if (toggle && nav) {
  toggle.hidden = false;
  const closeMenu = () => {
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Menü öffnen');
    nav.classList.remove('is-open');
  };
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Menü schließen' : 'Menü öffnen');
    nav.classList.toggle('is-open', open);
  });
  document.querySelector('.mobile-contact')?.addEventListener('click', closeMenu);
  nav.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && nav.classList.contains('is-open')) {
      closeMenu();
      toggle.focus();
    }
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('.site-header')) closeMenu();
  });
}


// Keep the editor's original content and desktop heading. Only mobile gains
// a native, keyboard-accessible disclosure; no-JavaScript readers see it all.
const mobileLayout = window.matchMedia('(max-width: 800px)');
const qualificationsHeading = document.querySelector('.about-copy > h3');
const qualificationsText = qualificationsHeading?.nextElementSibling;
if (qualificationsHeading && qualificationsText?.tagName === 'P') {
  const disclosure = document.createElement('details');
  disclosure.className = 'mobile-qualifications';
  const summary = document.createElement('summary');
  summary.textContent = 'Qualifikationen ansehen';
  disclosure.append(summary);
  const updateQualifications = () => {
    if (mobileLayout.matches && !disclosure.isConnected) {
      qualificationsHeading.before(disclosure);
      disclosure.append(qualificationsHeading, qualificationsText);
      disclosure.open = false;
    } else if (!mobileLayout.matches && disclosure.isConnected) {
      disclosure.before(qualificationsHeading, qualificationsText);
      disclosure.remove();
    }
  };
  mobileLayout.addEventListener('change', updateQualifications);
  updateQualifications();
}

document.querySelectorAll('.contact-form').forEach(form => {
  const button = form.querySelector('button[type="submit"]');
  const status = form.querySelector('.contact-status');
  let token = '';
  let sending = false;
  const showStatus = (message, error = false) => {
    status.textContent = message;
    status.classList.toggle('is-error', error);
  };
  const prepare = async () => {
    button.disabled = true;
    try {
      const response = await fetch(form.dataset.tokenUrl, { cache: 'no-store', credentials: 'same-origin' });
      const data = await response.json();
      if (!response.ok || typeof data.token !== 'string') throw new Error('token');
      token = data.token;
      await new Promise(resolve => setTimeout(resolve, 2000));
      button.disabled = false;
    } catch {
      showStatus('Das Formular konnte nicht geladen werden. Bitte laden Sie die Seite neu oder schreiben Sie direkt per E-Mail.', true);
    }
  };
  form.hidden = false;
  prepare();
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (sending || !token || !form.reportValidity()) return;
    sending = true;
    button.disabled = true;
    button.textContent = 'Wird gesendet...';
    showStatus('');
    const fields = new FormData(form);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 20000);
    let refresh = false;
    try {
      const response = await fetch(form.dataset.sendUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        signal: controller.signal,
        body: JSON.stringify({
          name: fields.get('name'), email: fields.get('email'), message: fields.get('message'),
          contact_company_fax: fields.get('contact_company_fax'), token,
        }),
      });
      const result = await response.json();
      if (!response.ok || !result.ok) {
        showStatus(result.message || 'Ihre Nachricht konnte nicht versendet werden. Bitte versuchen Sie es erneut oder schreiben Sie direkt per E-Mail.', true);
        refresh = response.status === 419;
      } else {
        form.reset();
        showStatus(result.message);
        status.focus();
        refresh = true;
      }
    } catch {
      showStatus('Es gab ein Verbindungsproblem. Bitte versuchen Sie es noch einmal oder schreiben Sie direkt per E-Mail.', true);
    } finally {
      clearTimeout(timer);
      sending = false;
      button.textContent = 'Nachricht senden';
      if (refresh) {
        token = '';
        await prepare();
      } else {
        button.disabled = false;
      }
    }
  });
});
