'use strict';

const CART_STORAGE_KEY = 'ipfstock-license-cart-v1';
const MAILTO_SAFE_LENGTH = 1800;

class LicenseCart {
  constructor(storageKey = CART_STORAGE_KEY) {
    this.storageKey = storageKey;
    this.items = [];
    this.listeners = new Set();
    this.load();
  }

  load() {
    try {
      const raw = localStorage.getItem(this.storageKey);
      const parsed = raw ? JSON.parse(raw) : [];
      this.items = Array.isArray(parsed) ? parsed.filter((item) => item?.slug) : [];
    } catch (err) {
      console.warn('Could not load shot list cart', err);
      this.items = [];
    }
  }

  save() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.items));
    } catch (err) {
      console.warn('Could not save shot list cart', err);
    }
  }

  onChange(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify() {
    this.listeners.forEach((listener) => listener(this.items));
  }

  has(slug) {
    return this.items.some((item) => item.slug === slug);
  }

  add(item) {
    if (!item?.slug || this.has(item.slug)) return false;
    this.items.push({ ...item, addedAt: Date.now() });
    this.save();
    this.notify();
    return true;
  }

  remove(slug) {
    const before = this.items.length;
    this.items = this.items.filter((item) => item.slug !== slug);
    if (this.items.length === before) return false;
    this.save();
    this.notify();
    return true;
  }

  clear() {
    if (this.items.length === 0) return;
    this.items = [];
    this.save();
    this.notify();
  }

  count() {
    return this.items.length;
  }
}

function buildCartLicenseMailto(items, recipient) {
  const count = items.length;
  const subject = count === 1
    ? `License Request — ${items[0].reelId}`
    : `License Request — ${count} clips (Cart)`;

  const clipBlocks = items.map((item, index) => {
    const lines = [
      `${index + 1}. Reel ID: ${item.reelId}`,
      `   Title: ${item.title}`,
      `   License: ${item.licenseLabel} | Tier: ${item.tierLabel}`,
    ];
    if (item.duration) lines.push(`   Duration: ${item.duration}`);
    if (item.region) lines.push(`   Location: ${item.region}`);
    return lines.join('\n');
  });

  const body = [
    'Hello Indo Pacific Stock Licensing,',
    '',
    `I would like to request license terms and master raw files for the following clip${count === 1 ? '' : 's'}:`,
    '',
    ...clipBlocks,
    '',
    'Please advise on rates and delivery of low-resolution time-coded review files.',
    '',
    '—',
    '(Sent via Indo Pacific Stock catalog cart)',
  ].join('\n');

  const mailto = `mailto:${recipient}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;

  return {
    mailto,
    subject,
    body,
    tooLong: mailto.length > MAILTO_SAFE_LENGTH,
  };
}

function buildFallbackMailto(recipient, count) {
  const subject = `License Request — ${count} clips (Cart)`;
  const body = [
    'Hello Indo Pacific Stock Licensing,',
    '',
    'I would like to request license terms and master raw files for the clips in my cart.',
    'The full cart details are pasted below from my clipboard.',
    '',
    'Please advise on rates and delivery of low-resolution time-coded review files.',
    '',
    '—',
    '(Sent via Indo Pacific Stock catalog cart)',
  ].join('\n');

  return `mailto:${recipient}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

window.IPFStockCart = {
  LicenseCart,
  CART_STORAGE_KEY,
  MAILTO_SAFE_LENGTH,
  buildCartLicenseMailto,
  buildFallbackMailto,
};
