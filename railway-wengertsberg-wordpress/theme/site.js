'use strict';
document.documentElement.classList.add('js');
const toggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('.site-nav');
if (toggle && nav) {
  toggle.hidden = false;
  const closeMenu = () => {
    toggle.setAttribute('aria-expanded', 'false');
    nav.classList.remove('is-open');
  };
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
  });
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
      showStatus('Das Formular konnte nicht geladen werden. Bitte lade die Seite neu oder schreibe direkt per E-Mail.', true);
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
        showStatus(result.message || 'Deine Nachricht konnte nicht versendet werden. Bitte versuche es erneut oder schreibe direkt per E-Mail.', true);
        refresh = response.status === 419;
      } else {
        form.reset();
        showStatus(result.message);
        status.focus();
        refresh = true;
      }
    } catch {
      showStatus('Es gab ein Verbindungsproblem. Bitte versuche es noch einmal oder schreibe direkt per E-Mail.', true);
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
