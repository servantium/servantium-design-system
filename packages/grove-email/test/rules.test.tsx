/**
 * The rules, as tests. Every design decision and everything a mail client punishes, checked
 * against every email's real output — TSX templates, MDX emails, and every sample on the style
 * sheet — so a rule can't be broken by a new email, only by editing this file.
 *
 *   npm test
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { renderToStaticMarkup } from 'react-dom/server';
import { addressLine, footerLinks, social } from '@servantium/brand';
import { renderEmail } from '../src/render';
import { Banner, Email, type BannerProps } from '../src/components';
import { Card } from '../scripts/card';
import { compileMdxEmail, FrontmatterError, fillPreview, loadMdxEmail, mdxBody, protectMergeFields } from '../src/mdx';
import { htmlToText } from '../src/text';
import { SAMPLES } from '../src/stylesheet';
import { color, neutral, tones } from '../src/theme';
import { collect, firebaseReset } from '../scripts/collect';
import { MARKDOWN, styleGuideMarkdown } from '../scripts/style-guide-md';
import { templatesMarkdown } from '../scripts/templates-md';
import { mdxComponents } from '../src/components';
import { readFileSync, existsSync } from 'node:fs';
import brandManifest from '@servantium/brand/assets.manifest.json' with { type: 'json' };
// @ts-expect-error — plain JS module
import { buildManifest } from '../../brand/scripts/assets.mjs';

const emails = await collect();
const both = emails.flatMap((e) => [
  { id: e.id, stream: e.stream, html: e.preview.html },
  { id: `${e.id} (sent)`, stream: e.stream, html: e.sent.html },
]);
const samples = await Promise.all(SAMPLES.flatMap((g) => g.items).map(async (s) => ({
  id: `style sheet: ${s.name}`,
  html: renderEmail({ subject: s.name, preheader: '', children: <Card>{await mdxBody(s.mdx)}</Card> }),
})));
const everything = [...both, ...samples];

// ── Design decisions ────────────────────────────────────────────────────────────────────────────
test('no coloured bar down the left of anything (banned 2026-09-24)', () => {
  for (const { id, html } of everything) assert.doesNotMatch(html, /border-left/i, `${id} draws a left bar`);
});

test('every email opens on the shared forest banner', () => {
  for (const { id, html } of both) assert.match(html, new RegExp(`bgcolor="${color.banner}"`, 'i'), `${id} has no banner`);
});

test('footer links and address come from company.json, in every email', () => {
  for (const { id, html } of both) {
    assert.ok(html.includes(addressLine()), `${id} is missing the company address`);
    for (const l of footerLinks()) assert.ok(html.includes(`href="${l.href}"`), `${id} is missing ${l.label}`);
  }
});

test('every footer carries LinkedIn, and hides the status page until it is live', () => {
  for (const { id, html } of both) {
    assert.ok(html.includes(`href="${social.linkedin}"`), `${id} has no LinkedIn link`);
    assert.match(html, /alt="Servantium on LinkedIn"/, `${id}: the LinkedIn icon needs its alt text`);
    assert.doesNotMatch(html, /status\.servantium\.com"[^>]*>Status</, `${id} links to a status page that doesn't exist yet`);
  }
});

test('three tones, and nothing else', () => {
  assert.deepEqual(Object.keys(tones), ['default', 'attention', 'urgent']);
});

// ── The banner is one line ──────────────────────────────────────────────────────────────────────
test('banner titles are one fixed line: no subtitle, no fields, 24 characters at most', async () => {
  const base = 'subject: s\npreheader: p\nlabel: l\nstream: transactional\nfooter:\n  reason: r';
  await assert.rejects(loadMdxEmail(`---\n${base}\ntitle: Welcome\nsubtitle: Dana added you\n---\nx`), /subtitle/);
  await assert.rejects(loadMdxEmail(`---\n${base}\ntitle: "{{ name }} assigned you"\n---\nx`), /can't contain fields/);
  await assert.rejects(loadMdxEmail(`---\n${base}\ntitle: This headline is far too long to fit\n---\nx`), /24 on one line/);
  for (const e of emails) assert.doesNotMatch(e.sent.html, /<h1[^>]*>[^<]*\{\{/, `${e.id}: the banner title has a field in it`);
});

// ── Astro ───────────────────────────────────────────────────────────────────────────────────────
test('Astro never appears on an attention or urgent email', () => {
  for (const e of emails) {
    if (e.tone !== 'default') assert.doesNotMatch(e.preview.html, /astro-\w+\.png/, `${e.id} is ${e.tone} and shows Astro`);
  }
});

test('the Banner refuses Astro with a non-default tone, even when the types are forced', () => {
  const forced = { tone: 'urgent', astro: 'waving', label: 'x', title: 'x' } as unknown as BannerProps;
  assert.throws(() => renderToStaticMarkup(<Email><Banner {...forced} /></Email>), /good news only/);
});

// ── Frontmatter is a schema ─────────────────────────────────────────────────────────────────────
const fm = (lines: string) => `---\n${lines}\n---\nHello.`;
const OK = 'subject: s\npreheader: p\nlabel: l\ntitle: t\nstream: transactional\nfooter:\n  reason: r';

test('frontmatter: a valid email loads', async () => {
  await assert.doesNotReject(loadMdxEmail(fm(OK)));
});

test('frontmatter: Astro on an urgent email fails the build', async () => {
  await assert.rejects(loadMdxEmail(fm(`${OK}\ntone: urgent\nastro: waving`)), FrontmatterError);
});

test('frontmatter: a missing footer reason fails the build', async () => {
  await assert.rejects(loadMdxEmail(fm(OK.replace('footer:\n  reason: r', ''))), /footer\.reason/);
});

test('frontmatter: an unknown tone or stream fails the build', async () => {
  await assert.rejects(loadMdxEmail(fm(`${OK}\ntone: critical`)), /tone/);
  await assert.rejects(loadMdxEmail(fm(OK.replace('transactional', 'marketing'))), /stream/);
});

// ── Unsubscribe follows the stream ──────────────────────────────────────────────────────────────
test('broadcast mail offers an unsubscribe; transactional mail never does', () => {
  for (const { id, stream, html } of both) {
    const has = />Unsubscribe</.test(html);
    assert.equal(has, stream === 'broadcast', `${id} is ${stream} and ${has ? 'must not offer' : 'must offer'} an unsubscribe`);
  }
});

test('broadcast mail uses Postmark\'s unsubscribe tag', () => {
  for (const e of emails.filter((x) => x.stream === 'broadcast')) assert.match(e.sent.html, /\{\{\{ pm:unsubscribe \}\}\}/, e.id);
});

// ── Merge fields ────────────────────────────────────────────────────────────────────────────────
test('merge fields reach the sent HTML untouched, and the preview fills them', () => {
  const incident = emails.find((e) => e.id === 'incident')!;
  for (const f of ['first_name', 'incident_title', 'status', 'status_url']) {
    assert.ok(incident.sent.html.includes(`{{ ${f} }}`), `sent incident lost {{ ${f} }}`);
  }
  assert.ok(incident.sent.subject.includes('{{ incident_title }}'));
  assert.doesNotMatch(incident.preview.html, /\{\{ (first_name|status|incident_title) \}\}/, 'preview left a field unfilled');
});

test('merge-field protection leaves code and JSX alone', () => {
  assert.equal(protectMergeFields('Hi {{ name }}'), "Hi {'{{ name }}'}");
  assert.equal(protectMergeFields('<Button href="{{ url }}">Go</Button>'), '<Button href="{{ url }}">Go</Button>');
  assert.equal(protectMergeFields('`{{ literal }}`'), '`{{ literal }}`');
  assert.equal(protectMergeFields('```\n{{ literal }}\n```'), '```\n{{ literal }}\n```');
  assert.equal(protectMergeFields('Intro.\n\n{{ update }}\n'), "Intro.\n\n<Text>{'{{ update }}'}</Text>\n");
});

test('a paragraph that is only a merge field is still a styled paragraph', () => {
  const incident = emails.find((e) => e.id === 'incident')!;
  assert.match(incident.sent.html, /<p style="[^"]*font-family[^"]*">\{\{ update \}\}<\/p>/, 'the update lost its paragraph styling');
});

test('no MDX escaping leaks into any output', () => {
  for (const { id, html } of everything) assert.doesNotMatch(html, /\{'\{\{/, `${id} shows a protected merge field`);
});

// ── What mail clients punish ────────────────────────────────────────────────────────────────────
test('under 102 KB, where Gmail clips the message', () => {
  for (const { id, html } of both) assert.ok(Buffer.byteLength(html) < 102 * 1024, `${id} will be clipped by Gmail`);
});

test('no SVG, no flex, no grid', () => {
  for (const { id, html } of everything) {
    assert.doesNotMatch(html, /<svg/i, `${id}: Gmail and Outlook drop SVG`);
    assert.doesNotMatch(html, /display:\s*(flex|grid)/i, `${id}: Outlook desktop has no flex or grid`);
  }
});

test('every image has alt text', () => {
  for (const { id, html } of everything) {
    for (const img of html.match(/<img[^>]*>/g) ?? []) assert.match(img, /\salt="/, `${id}: ${img.slice(0, 60)}…`);
  }
});

test('every button has an Outlook shape', () => {
  for (const { id, html } of everything) {
    const links = (html.match(/<!--\[if !mso\]><!--><a /g) ?? []).length;
    const shapes = (html.match(/<v:roundrect/g) ?? []).length;
    assert.equal(shapes, links, `${id}: a button without VML shows as a bare link in Outlook`);
  }
});

test('at most one primary button per email', () => {
  const primary = new RegExp(`<a [^>]*background-color:${color.brand}`, 'gi');
  for (const { id, html } of both) assert.ok((html.match(primary) ?? []).length <= 1, `${id} has more than one primary button`);
});

// ── Images ──────────────────────────────────────────────────────────────────────────────────────
const LIVE_KEYS = new Set(Object.values(brandManifest.assets).map((a) => `${brandManifest.origin}/${a.key}`));
const imageRefs = (html: string) => [
  ...[...html.matchAll(/(?:src|background)="([^"]*)"/g)].map((m) => m[1]),
  ...[...html.matchAll(/url\(([^)]*)\)/g)].map((m) => m[1].replace(/&quot;|['"]/g, '')),
].filter((u) => !u.startsWith('{{'));

test('sent emails load every image from its fingerprinted address in the asset library', () => {
  for (const e of emails) {
    for (const url of imageRefs(e.sent.html)) assert.ok(LIVE_KEYS.has(url), `${e.id}: ${url} isn't a current asset-library address`);
  }
});

test('the brand asset manifest is current (run npm run manifest in packages/brand)', () => {
  assert.deepEqual(buildManifest(), brandManifest, 'packages/brand/assets.manifest.json is stale');
});

// ── Plain text ──────────────────────────────────────────────────────────────────────────────────
test('every email has a readable plain-text part', () => {
  for (const e of emails) {
    const text = htmlToText(e.sent.html);
    assert.doesNotMatch(text, /<[a-z/!]/i, `${e.id}: markup left in the text part`);
    assert.doesNotMatch(text, /v:roundrect|\[if mso/, `${e.id}: Outlook markup left in the text part`);
    assert.ok(text.includes(addressLine()), `${e.id}: text part has no address`);
    for (const href of e.sent.html.match(/<!--\[if !mso\]><!--><a href="([^"]*)"/g) ?? []) {
      const url = href.replace(/.*href="/, '').replace(/"$/, '').replace(/&amp;/g, '&');
      assert.ok(text.includes(url), `${e.id}: text part is missing the button link ${url}`);
    }
  }
});

test('every id is a valid Postmark alias', () => {
  for (const e of emails) assert.match(e.id, /^[a-z][a-z0-9-]*$/, e.id);
  assert.equal(new Set(emails.map((e) => e.id)).size, emails.length, 'two emails share an alias');
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

test('every tone passes AA on the banner and in its callout, and its rule is visible on forest', () => {
  for (const [name, t] of Object.entries(tones)) {
    aa(t.onBanner, color.banner, `${name} banner label`);
    aa(t.strong, t.tint, `${name} callout title`);
    aa(color.ink, t.tint, `${name} callout text`);
    assert.ok(ratio(t.accent, color.banner) >= 3, `${name} rule is ${ratio(t.accent, color.banner).toFixed(1)}:1 on forest, below 3`);
  }
  aa(neutral.strong, neutral.tint, 'neutral callout title');
});

test('button labels pass AA on both button styles', () => {
  aa(color.banner, color.brand, 'primary button label');
  aa(color.banner, color.surface, 'secondary button label');
});

// ── Firebase ────────────────────────────────────────────────────────────────────────────────────
test('the Firebase export is a body fragment with Firebase placeholders', async () => {
  const frag = await firebaseReset();
  assert.doesNotMatch(frag, /<head|<style|<html/i, 'Firebase drops the head; the fragment must not rely on it');
  assert.match(frag, /%LINK%/);
  assert.match(frag, /%EMAIL%/);
  assert.doesNotMatch(frag, /\{\{/, 'a Postmark placeholder leaked into the Firebase copy');
  for (const url of imageRefs(frag)) assert.ok(LIVE_KEYS.has(url), `Firebase template: ${url} isn't a current asset-library address`);
});

// ── The contract with engineering ───────────────────────────────────────────────────────────────
test('every master declares exactly the fields it uses', async () => {
  // collect() already threw if a master broke this; these pin the failure modes.
  const body = 'Hi {{ first_name }}.';
  const base = 'subject: s\npreheader: p\nlabel: l\ntitle: t\nstream: transactional\nfooter:\n  reason: r';
  await assert.rejects(compileMdxEmail(`---\n${base}\n---\n${body}`), /uses `\{\{ first_name \}\}` but doesn't declare it/);
  await assert.rejects(compileMdxEmail(`---\n${base}\nfields:\n  first_name: Jules\n  spare: x\n---\n${body}`), /declares `spare`/);
  await assert.doesNotReject(compileMdxEmail(`---\n${base}\nfields:\n  first_name: Jules\n---\n${body}`));
});

test('every field has an example, so every email can be previewed and tested', () => {
  for (const e of emails) for (const [k, f] of Object.entries(e.fields)) assert.ok(Array.isArray(f.example) ? f.example.length : f.example.trim(), `${e.id}: ${k} has no example`);
});

test('sections and lists follow Postmark scoping', async () => {
  const fm = (fields: string, body: string) =>
    `---\nsubject: s\npreheader: p\nlabel: l\ntitle: t\nstream: transactional\nfooter:\n  reason: r\nfields:\n${fields}\n---\n${body}`;
  await assert.rejects(compileMdxEmail(fm('  note: { example: n, optional: true }\n  who: w', '<If field="note">{{ who }}</If>')), /inside the `note` section/);
  await assert.doesNotReject(compileMdxEmail(fm('  note: { example: n, optional: true }', '<If field="note">“{{ . }}”</If>')));
  await assert.rejects(compileMdxEmail(fm('  items: { example: [{ category: a, time: b, url: c, title: d }] }', '<Updates field="items" />')), /context/);
  await assert.doesNotReject(compileMdxEmail(fm('  items: { example: [{ category: a, time: b, url: c, title: d, context: e }] }', '<Updates field="items" />')));
});

test('optional content disappears cleanly when its field is missing', () => {
  const task = emails.find((e) => e.id === 'task')!;
  const without = fillPreview(task.sent.html, { ...task.model, message: '' });
  assert.doesNotMatch(without, /What they wrote/, "the note panel should vanish without a message");
  assert.match(fillPreview(task.sent.html, task.model), /What they wrote/);
});

test('an Editable block shows the default unless the sender overrides it', async () => {
  const src = '---\nsubject: s\npreheader: p\nlabel: l\ntitle: t\nstream: transactional\nfooter:\n  reason: r\nfields:\n  intro: { example: Custom intro, optional: true }\n---\n<Editable field="intro">Default intro</Editable>';
  const e = await loadMdxEmail(src);
  const html = renderEmail({ subject: 's', preheader: 'p', children: e.body });
  assert.match(fillPreview(html, {}), /Default intro/);
  assert.doesNotMatch(fillPreview(html, { intro: 'Custom intro' }), /Default intro/);
  assert.match(fillPreview(html, { intro: 'Custom intro' }), /Custom intro/);
});

// ── Docs ────────────────────────────────────────────────────────────────────────────────────────
test('docs/style-guide.md is current with the style sheet (run npm run build)', () => {
  const file = new URL('../docs/style-guide.md', import.meta.url);
  assert.ok(existsSync(file), 'docs/style-guide.md is missing — run npm run build');
  assert.equal(readFileSync(file, 'utf8'), styleGuideMarkdown(), 'docs/style-guide.md is stale — run npm run build and commit it');
});

test('docs/templates.md is current with the masters (run npm run build)', () => {
  const file = new URL('../docs/templates.md', import.meta.url);
  assert.ok(existsSync(file), 'docs/templates.md is missing — run npm run build');
  assert.equal(readFileSync(file, 'utf8'), templatesMarkdown(emails), 'docs/templates.md is stale — run npm run build and commit it');
});

test('every component a master can use has a sample in the style guide', () => {
  const markdownOnly = new Set(['p', 'h1', 'h2', 'h3', 'a', 'ul', 'ol', 'li', 'hr', 'pre', 'code']);
  const sampled = SAMPLES.flatMap((g) => g.items.map((s) => s.mdx)).join('\n');
  const viaMarkdown = new Set(Object.values(MARKDOWN));
  for (const name of Object.keys(mdxComponents).filter((n) => !markdownOnly.has(n) && !viaMarkdown.has(n))) {
    assert.match(sampled, new RegExp(`<${name}\\b`), `<${name}> has no style-guide sample — add one to src/stylesheet.ts`);
  }
});
