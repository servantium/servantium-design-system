/**
 * The rules, as tests. Everything the founder ruled and everything a mail client punishes, checked
 * against every template's real output — so a rule can't be broken by a new template, only by
 * editing this file.
 *
 *   npm test
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { addressLine, company, footerLinks } from '@servantium/brand';
import { renderEmail, toFirebaseFragment } from '../src/render';
import { templates } from '../src/index';
import { firebasePlaceholders } from '../src/templates/password-reset';
import { color, tones } from '../src/theme';

const rendered = Object.values(templates).map((t) => {
  const s = t.build(t.sample as never);
  return { id: t.id, html: renderEmail({ subject: s.subject, preheader: s.preheader, children: s.body }) };
});

// ── Founder rulings ─────────────────────────────────────────────────────────────────────────────
test('no coloured bar down the left of anything (banned 2026-09-24)', () => {
  for (const { id, html } of rendered) assert.doesNotMatch(html, /border-left/i, `${id} draws a left bar`);
});

test('every email opens on the shared forest banner', () => {
  for (const { id, html } of rendered) assert.match(html, new RegExp(`bgcolor="${color.banner}"`, 'i'), `${id} has no banner`);
});

test('footer links and address come from company.json, in every email', () => {
  for (const { id, html } of rendered) {
    assert.ok(html.includes(addressLine()), `${id} is missing the company address`);
    for (const l of footerLinks()) assert.ok(html.includes(`href="${l.href}"`), `${id} is missing ${l.label}`);
  }
});

// ── What mail clients punish ────────────────────────────────────────────────────────────────────
test('under 102 KB, where Gmail clips the message', () => {
  for (const { id, html } of rendered) assert.ok(Buffer.byteLength(html) < 102 * 1024, `${id} will be clipped by Gmail`);
});

test('no SVG, no flex, no grid', () => {
  for (const { id, html } of rendered) {
    assert.doesNotMatch(html, /<svg/i, `${id}: Gmail and Outlook drop SVG`);
    assert.doesNotMatch(html, /display:\s*(flex|grid)/i, `${id}: Outlook desktop has no flex or grid`);
  }
});

test('every image has alt text', () => {
  for (const { id, html } of rendered) {
    for (const img of html.match(/<img[^>]*>/g) ?? []) assert.match(img, /\salt="/, `${id}: ${img.slice(0, 60)}…`);
  }
});

test('every button has an Outlook shape', () => {
  for (const { id, html } of rendered) {
    const links = (html.match(/<!--\[if !mso\]><!--><a /g) ?? []).length;
    const shapes = (html.match(/<v:roundrect/g) ?? []).length;
    assert.equal(shapes, links, `${id}: a button without VML shows as a bare link in Outlook`);
  }
});

// ── Unsubscribe: required on marketing, forbidden on transactional ──────────────────────────────
test('only optional mail offers an unsubscribe', () => {
  for (const { id, html } of rendered) {
    const has = />Unsubscribe</.test(html);
    assert.equal(has, id === 'release-notes', `${id} ${has ? 'must not offer' : 'must offer'} an unsubscribe`);
  }
});

// ── Contrast: WCAG AA (4.5:1) for every text pairing ────────────────────────────────────────────
const lum = (hex: string) => {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
};
const ratio = (a: string, b: string) => {
  const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
};
const aa = (fg: string, bg: string, what: string) =>
  assert.ok(ratio(fg, bg) >= 4.5, `${what}: ${fg} on ${bg} is ${ratio(fg, bg).toFixed(1)}:1, below 4.5`);

test('body text, links and muted text pass AA', () => {
  aa(color.ink, color.surface, 'body text');
  aa(color.link, color.surface, 'links');
  aa(color.inkMuted, color.surface, 'muted text');
  aa(color.inkMuted, color.panel, 'muted text on the data-table panel');
  aa(color.inkMuted, color.canvas, 'footer text on the canvas');
  aa(color.onBannerMuted, color.banner, 'subtitle on the banner');
});

test('every tone passes AA on the banner and in its callout', () => {
  for (const [name, t] of Object.entries(tones)) {
    aa(t.onBanner, color.banner, `${name} banner label`);
    aa(t.strong, t.tint, `${name} callout title`);
  }
});

test('KNOWN: the primary button is below AA — the founder ruling, recorded not hidden', () => {
  // White on #00C26D is ~2.3:1. The ruling is "#00C26D with white text"; this test exists so the
  // number is on record and the day someone changes the button, this fails and says why.
  assert.ok(ratio('#FFFFFF', color.brand) < 3, 'the button changed — update this test and the README');
});

// ── Firebase ────────────────────────────────────────────────────────────────────────────────────
test('the Firebase export is a body fragment with Firebase placeholders', () => {
  const s = templates.passwordReset.build(firebasePlaceholders);
  const frag = toFirebaseFragment(renderEmail({
    subject: s.subject, preheader: s.preheader, children: s.body,
    assets: { base: null, art: false, overrides: { 'logo/servantium-logo-white.png': `${company.urls.website}/brand/servantium-logo-white.png` } },
  }));
  assert.doesNotMatch(frag, /<head|<style|<html/i, 'Firebase drops the head; the fragment must not rely on it');
  assert.match(frag, /%LINK%/);
  assert.match(frag, /%EMAIL%/);
  assert.match(frag, /src="https:\/\//, 'Firebase sends it — every image must be an absolute URL');
  assert.doesNotMatch(frag, /header-\w+\.jpg/, 'the header art is not hosted yet');
});
