'use strict';

const CART_STORAGE_KEY = 'ipfstock-license-cart-v1';
const LICENSING_EMAIL = 'licensingips@gmail.com';
const FORMSUBMIT_URL = `https://formsubmit.co/ajax/${LICENSING_EMAIL}`;

function $(id) {
  return document.getElementById(id);
}

function clipsFromCart() {
  try {
    const parsed = JSON.parse(localStorage.getItem(CART_STORAGE_KEY) || '[]');
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item) => item?.slug);
  } catch (err) {
    return [];
  }
}

function formatClipLines(items) {
  return items.map((item, index) => {
    const lines = [
      `${index + 1}. Reel ID: ${item.reelId || item.slug}`,
      `   Title: ${item.title || 'Untitled'}`,
    ];
    if (item.licenseLabel || item.tierLabel) {
      lines.push(`   License: ${item.licenseLabel || ''} | Tier: ${item.tierLabel || ''}`.trim());
    }
    if (item.duration) lines.push(`   Duration: ${item.duration}`);
    if (item.region) lines.push(`   Location: ${item.region}`);
    if (item.slug) lines.push(`   Page: https://indopacificstock.com/clip/${item.slug}/`);
    return lines.join('\n');
  }).join('\n\n');
}

function applyQueryPrefill() {
  const params = new URLSearchParams(window.location.search);
  const intent = params.get('intent') || '';
  const fromCart = params.get('from') === 'cart';
  const clip = params.get('clip') || '';
  const title = params.get('title') || '';
  const id = params.get('id') || '';

  const kicker = $('inquire-kicker');
  const heading = $('inquire-title');
  const lead = $('inquire-lead');
  const clipsField = $('clips');
  const messageField = $('message');

  if (fromCart) {
    const items = clipsFromCart();
    if (kicker) kicker.textContent = 'Shot list';
    if (heading) heading.textContent = items.length
      ? `License request · ${items.length} clip${items.length === 1 ? '' : 's'}`
      : 'License request';
    if (lead) {
      lead.textContent = items.length
        ? 'Your cart is listed below. Add usage, territory, and term so we can quote without a follow-up email.'
        : 'Your cart is empty. Paste reel IDs below, or add clips from the archive first.';
    }
    if (clipsField && items.length) clipsField.value = formatClipLines(items);
    return;
  }

  if (clip) {
    const page = `https://indopacificstock.com/clip/${clip}/`;
    if (kicker) kicker.textContent = 'Single clip';
    if (heading) heading.textContent = title ? `License request · ${title}` : 'License request';
    if (lead) {
      lead.textContent = 'Tell us how you plan to use this clip. We reply with proxy files, rates, and a quote.';
    }
    if (clipsField) {
      clipsField.value = [
        `1. Reel ID: ${id || clip}`,
        title ? `   Title: ${title}` : '',
        `   Page: ${page}`,
      ].filter(Boolean).join('\n');
    }
    return;
  }

  if (intent === 'shot-list') {
    if (kicker) kicker.textContent = 'Research request';
    if (heading) heading.textContent = 'Submit a shot list';
    if (lead) {
      lead.textContent = 'Describe the sequences you need. We will pull matching clips and send time-coded proxies.';
    }
    if (messageField && !messageField.value) {
      messageField.placeholder = 'Species, behaviour, location, and any must-have shots…';
    }
    return;
  }

  if (intent === 'assignment') {
    if (kicker) kicker.textContent = 'Assignment hire';
    if (heading) heading.textContent = 'Assignment inquiry';
    if (lead) {
      lead.textContent = 'Tell us the destination, dates, and shots you cannot find in the archive. We shoot RED cinema and aerials on assignment.';
    }
    if (messageField && !messageField.value) {
      messageField.placeholder = 'Location, dates, shot list, and delivery format…';
    }
  }
}

function setStatus(type, text) {
  const el = $('form-status');
  if (!el) return;
  el.hidden = !text;
  el.textContent = text || '';
  el.className = `form-status${type ? ` form-status--${type}` : ''}`;
}

function setBusy(busy) {
  const btn = $('inquire-submit');
  if (!btn) return;
  btn.disabled = busy;
  btn.textContent = busy ? 'Sending…' : 'Send license request';
}

function showSuccess() {
  const form = $('inquire-form');
  const success = $('inquire-success');
  if (form) form.hidden = true;
  if (success) success.hidden = false;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function submitForm(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const honey = form.querySelector('[name="website"]');
  if (honey && honey.value) return;

  const name = $('name').value.trim();
  const email = $('email').value.trim();
  if (!name || !email) {
    setStatus('error', 'Name and email are required.');
    return;
  }

  const payload = {
    _subject: `License request — ${name}`,
    _template: 'table',
    _captcha: 'false',
    _replyto: email,
    name,
    email,
    production: $('production').value.trim(),
    project: $('project').value.trim(),
    usage: $('usage').value,
    territory: $('territory').value,
    term: $('term').value,
    proxies: $('proxies').checked ? 'Yes — send time-coded proxies' : 'No',
    clips: $('clips').value.trim(),
    message: $('message').value.trim(),
    page: window.location.href,
  };

  setBusy(true);
  setStatus('info', 'Sending your request…');

  try {
    const response = await fetch(FORMSUBMIT_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok || result.success === 'false' || result.success === false) {
      throw new Error(result.message || 'Send failed');
    }
    showSuccess();
  } catch (err) {
    setStatus(
      'error',
      `Could not send from this browser. Email ${LICENSING_EMAIL} directly, or try again in a moment.`,
    );
    setBusy(false);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  applyQueryPrefill();
  const form = $('inquire-form');
  if (form) form.addEventListener('submit', submitForm);
});
