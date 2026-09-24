/**
 * export — renders every email, TSX and MDX, to dist/.
 *
 *   npm run build      (syncs Verdant tokens first)
 *
 * dist/
 *   index.html                gallery: every email at desktop and phone width
 *   stylesheet.html           every component, tone and rule, with the MDX that makes it
 *   banners.html              the one banner, in its three tones and with Astro
 *   <id>.html                 each email with sample data, images from ./assets
 *   postmark/<id>/            content.html + content.txt + meta.json — the layout `postmark templates push` reads
 *   postmark/send.json        per alias: the stream to send on, and the model to send (with sample values)
 *   firebase/password-reset.html   paste into Firebase → Authentication → Templates, until reset moves to Postmark
 *   assets/                   logo, Astro and header art, copied from @servantium/brand
 */
import { cpSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { ReactNode } from 'react';
import { ASTRO_POSES, company } from '@servantium/brand';
import { renderEmail, toFirebaseFragment } from '../src/render';
import { templates } from '../src/index';
import { firebasePlaceholders } from '../src/templates/password-reset';
import { Banner, Body, Email } from '../src/components/Layout';
import { Text } from '../src/components/Content';
import { fillPreview, mdxBody } from '../src/mdx';
import { htmlToText } from '../src/text';
import { color, tones, type Tone } from '../src/theme';
import {
  ASTRO_NEVER, ASTRO_RULE, ASTRO_USE, BANNED, FRONTMATTER, FRONTMATTER_EXAMPLE, SAMPLES, TONE_GUIDE, TONE_QUESTION,
} from '../src/stylesheet';
import { Card } from './card';
import { collect, SENT_ASSET_BASE } from './collect';

const HERE = dirname(fileURLToPath(import.meta.url));
const DIST = join(HERE, '../dist');
const require = createRequire(import.meta.url);
const BRAND = dirname(require.resolve('@servantium/brand/company.json'));

rmSync(DIST, { recursive: true, force: true });
for (const d of ['', 'postmark', 'firebase', 'assets']) mkdirSync(join(DIST, d), { recursive: true });
for (const d of ['logo', 'astro', 'email']) {
  cpSync(join(BRAND, 'assets', d), join(DIST, 'assets', d), { recursive: true, filter: (src) => !src.endsWith('.svg') });
}

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const attr = (s: string) => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;');
const kb = (s: string) => `${(Buffer.byteLength(s) / 1024).toFixed(1)} KB`;

// ── Every email: preview, Postmark template, plain text ─────────────────────────────────────────
const emails = await collect();
const send: Record<string, { stream: string; messageStream: string; model: Record<string, string> }> = {};
const rows: string[] = [];

for (const e of emails) {
  writeFileSync(join(DIST, `${e.id}.html`), e.preview.html);

  const dir = join(DIST, 'postmark', e.id);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, 'content.html'), e.sent.html);
  writeFileSync(join(dir, 'content.txt'), htmlToText(e.sent.html));
  writeFileSync(join(dir, 'meta.json'), `${JSON.stringify({ Name: e.name, Alias: e.id, Subject: e.sent.subject, TemplateType: 'Standard' }, null, 2)}\n`);
  // Postmark's default stream ids: `outbound` (transactional) and `broadcast`.
  send[e.id] = { stream: e.stream, messageStream: e.stream === 'broadcast' ? 'broadcast' : 'outbound', model: e.model };

  rows.push(`  ${e.id.padEnd(24)} ${e.source}  ${e.tone.padEnd(9)} ${e.stream.padEnd(13)} ${kb(e.preview.html)}`);
}
writeFileSync(join(DIST, 'postmark', 'send.json'), `${JSON.stringify(send, null, 2)}\n`);

// Firebase sends this one itself: absolute logo URL (servantium.com already hosts it), and no
// header art until the art is hosted somewhere Firebase's recipients can reach.
const fb = templates.passwordReset.build(firebasePlaceholders);
writeFileSync(join(DIST, 'firebase', 'password-reset.html'), toFirebaseFragment(renderEmail({
  subject: fb.subject, preheader: fb.preheader, children: fb.body,
  assets: { base: null, art: false, overrides: { 'logo/servantium-logo-white.png': `${company.urls.website}/brand/servantium-logo-white.png` } },
})));

// ── Small renders for the style sheet ───────────────────────────────────────────────────────────
const frame = (children: ReactNode) =>
  renderEmail({ subject: 'Sample', preheader: '', children }).replace('padding:32px 12px 40px;', 'padding:12px;');

const BANNERS: { key: string; tone: Tone; astro?: (typeof ASTRO_POSES)[number]; label: string; title: string; note: string }[] = [
  { key: 'default', tone: 'default', label: 'Task', title: 'Jules Hart assigned you a task', note: 'default — nothing is wrong' },
  { key: 'astro', tone: 'default', astro: 'professor', label: 'Release notes', title: "What's new in Servantium", note: 'default + Astro — good news, not urgent' },
  { key: 'attention', tone: 'attention', label: 'Scheduled maintenance', title: 'Planned maintenance on Saturday', note: 'attention — act or plan soon' },
  { key: 'urgent', tone: 'urgent', label: 'Service disruption', title: "Quotes aren't loading", note: 'urgent — broken now' },
];
const bannerDoc = (b: (typeof BANNERS)[number], body?: ReactNode) => frame(
  <Email>
    {b.tone === 'default'
      ? <Banner label={b.label} title={b.title} astro={b.astro} />
      : <Banner tone={b.tone} label={b.label} title={b.title} />}
    {body && <Body>{body}</Body>}
  </Email>,
);

writeFileSync(join(DIST, 'banners.html'), renderEmail({
  subject: 'Servantium email banner',
  preheader: 'One banner, three tones, and Astro for good news.',
  children: (
    <>
      {BANNERS.map((b) => (
        <div key={b.key} style={{ marginBottom: '20px' }}>
          <Email>
            {b.tone === 'default'
              ? <Banner label={b.label} title={b.title} astro={b.astro} />
              : <Banner tone={b.tone} label={b.label} title={b.title} />}
            <Body><Text size="sm" margin="0"><b>{b.note}</b></Text></Body>
          </Email>
        </div>
      ))}
    </>
  ),
}));

// ── Shared page chrome ──────────────────────────────────────────────────────────────────────────
const PAGE_CSS = `
  :root{--bg:#F5F6F7;--card:#fff;--ink:#1a1a1a;--ink2:#3d3d3d;--ink3:#6b6b6b;--rule:#E1E3E6;--link:#037A47;--forest:#023E25;--mint:#E6F9EF;--code:#F5F6F7}
  *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 'Source Sans 3',system-ui,sans-serif}
  a{color:var(--link)} code{font:13px/1.5 Menlo,Consolas,monospace;background:var(--code);padding:1px 5px;border-radius:4px}
  pre{margin:0;background:#0f2a1c;color:#E6F9EF;border-radius:10px;padding:14px 16px;overflow-x:auto;font:12.5px/1.6 Menlo,Consolas,monospace}
  pre code{background:none;padding:0;color:inherit;font:inherit}
  .hero{background:var(--forest) url(assets/email/header-standard.jpg) right top/cover no-repeat;color:#fff;padding:44px 0 40px}
  .wrap{max-width:1180px;margin:0 auto;padding:0 16px}
  h1,h2,h3{font-family:'Playfair Display',Georgia,serif;font-weight:600} .hero h1{font-size:36px;margin:0 0 8px}
  .hero p{margin:0;color:#CFEFDD;max-width:760px} .hero nav{margin-top:18px;display:flex;flex-wrap:wrap;gap:6px 18px}
  .hero nav a{color:#fff;font-weight:600;text-decoration:none;border-bottom:1px solid #56ffa1}
  .panel,.tpl{background:var(--card);border:1px solid var(--rule);border-radius:14px;margin:24px 0;padding:24px}
  .panel>h2{font-size:26px;margin:0 0 6px} .lead{color:var(--ink2);margin:0 0 18px;max-width:780px}
  .tpl header{display:flex;justify-content:space-between;align-items:flex-start;gap:12px} .tpl h2{font-size:24px;margin:4px 0 0}
  .tpl header a{font-weight:600;text-decoration:none;white-space:nowrap}
  .tier{font-size:11px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:var(--ink3)}
  .tier i{font-style:normal;display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;vertical-align:1px}
  dl{display:grid;grid-template-columns:max-content 1fr;gap:4px 16px;margin:16px 0 20px} dt{color:var(--ink3);font-size:13px} dd{margin:0}
  .frames{display:flex;gap:20px;align-items:flex-start;overflow-x:auto;padding-bottom:4px} figure{margin:0;flex:none}
  iframe{border:1px solid var(--rule);border-radius:10px;background:var(--bg);display:block}
  .frames iframe{width:640px;height:1000px} .frames .phone iframe{width:375px}
  figcaption{font-size:12px;color:var(--ink3);margin-top:6px}
  table.ref{border-collapse:collapse;width:100%;font-size:14px} .ref th,.ref td{text-align:left;padding:9px 10px;border-top:1px solid var(--rule);vertical-align:top}
  .ref th{font-size:12px;letter-spacing:.8px;text-transform:uppercase;color:var(--ink3);border-top:0}
  .req{font-size:11px;font-weight:700;color:#037A47;background:var(--mint);border-radius:999px;padding:1px 8px;white-space:nowrap}
  .opt{font-size:11px;color:var(--ink3);white-space:nowrap}
  .sample{display:grid;grid-template-columns:minmax(0,1fr) 640px;gap:24px;padding:22px 0;border-top:1px solid var(--rule)}
  .sample pre,.cols pre{white-space:pre-wrap;word-break:break-word}
  .sample:first-of-type{border-top:0} .sample h3{font-size:19px;margin:0 0 6px}
  .sample p{margin:0 0 8px} .sample .avoid{color:#855500} .sample .props{color:var(--ink3);font-size:13px}
  .sample pre{margin-top:12px} .sample iframe{width:100%;height:120px}
  body.phone .sample{grid-template-columns:minmax(0,1fr) 375px}
  .ref td{overflow-wrap:anywhere}
  .group{margin:28px 0 4px;font-size:22px} .group+.lead{margin-bottom:6px}
  .tones{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(360px,100%),1fr));gap:18px}
  .tones iframe{width:100%;height:220px} .tone h3{font:700 13px 'Source Sans 3',sans-serif;margin:10px 0 4px} .tone p{margin:0 0 4px;font-size:14px}
  .astro-row{display:flex;flex-wrap:wrap;gap:14px;margin:8px 0 18px} .astro-row figure{text-align:center}
  .astro-row img{width:84px;height:84px;background:var(--forest);border-radius:12px;padding:6px}
  .cols{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:24px} .cols h3{font-size:18px;margin:0 0 8px}
  ul.clean{margin:0;padding-left:18px} ul.clean li{margin:4px 0}
  .no{color:#B42336;font-weight:700} .yes{color:#037A47;font-weight:700}
  .toggle{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--rule);padding:10px 0;display:flex;gap:8px;align-items:center;font-size:13px;color:var(--ink3)}
  .toggle button{font:600 13px 'Source Sans 3',sans-serif;border:1px solid var(--rule);background:#fff;border-radius:999px;padding:5px 14px;cursor:pointer;color:var(--ink2)}
  .toggle button[aria-pressed=true]{background:var(--forest);color:#fff;border-color:var(--forest)}
  @media (max-width:1040px){.sample,body.phone .sample{grid-template-columns:minmax(0,1fr)}.sample iframe{max-width:640px}}
  .astro-banner{max-width:640px;margin-top:22px}
  .astro-banner iframe{width:100%;height:260px}
  @media (max-width:720px){.frames{flex-direction:column}.frames iframe,.frames .phone iframe{width:100%;max-width:375px}
    .panel,.tpl{padding:16px}.cols{grid-template-columns:minmax(0,1fr)}.hero h1{font-size:30px}.ref{font-size:13px}}
`;
const page = (title: string, intro: string, nav: [string, string][], main: string, script = '') => `<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
<style>${PAGE_CSS}</style></head><body>
<div class="hero"><div class="wrap"><h1>${esc(title)}</h1><p>${intro}</p>
<nav>${nav.map(([href, label]) => `<a href="${href}">${label}</a>`).join('')}</nav></div></div>
<main class="wrap">${main}</main>${script}</body></html>`;

const TONE_DOT: Record<Tone, string> = { default: tones.default.accent, attention: tones.attention.accent, urgent: tones.urgent.accent };

// ── Style sheet ─────────────────────────────────────────────────────────────────────────────────
const fit = `<script>
  function fit(f){try{f.style.height=f.contentDocument.documentElement.scrollHeight+'px'}catch(e){}}
  function view(v){document.body.classList.toggle('phone',v==='phone');
    document.querySelectorAll('.toggle button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.v===v)));
    requestAnimationFrame(()=>document.querySelectorAll('iframe[data-fit]').forEach(fit))}
  window.addEventListener('resize',()=>document.querySelectorAll('iframe[data-fit]').forEach(fit));
</script>`;
const srcdoc = (html: string, title: string, cls = '') =>
  `<iframe data-fit class="${cls}" title="${attr(title)}" srcdoc="${attr(html)}" onload="fit(this)"></iframe>`;

const sampleHtml = await Promise.all(SAMPLES.map(async (g) => {
  const items = await Promise.all(g.items.map(async (s) => {
    const html = fillPreview(frame(<Card>{await mdxBody(s.mdx)}</Card>), s.preview);
    return `
<div class="sample">
  <div>
    <h3>${esc(s.name)}</h3>
    <p>${esc(s.use).replace(/`([^`]+)`/g, '<code>$1</code>')}</p>
    ${s.avoid ? `<p class="avoid">Not for: ${esc(s.avoid).replace(/`([^`]+)`/g, '<code>$1</code>')}</p>` : ''}
    ${s.props ? `<p class="props">${esc(s.props)}</p>` : ''}
    <pre><code>${esc(s.mdx)}</code></pre>
  </div>
  ${srcdoc(html, s.name)}
</div>`;
  }));
  return `<h2 class="group" id="c-${g.group.toLowerCase().replace(/\W+/g, '-')}">${esc(g.group)}</h2><p class="lead">${esc(g.intro).replace(/`([^`]+)`/g, '<code>$1</code>')}</p>${items.join('')}`;
}));

const stylesheet = page(
  'Email style sheet',
  'Everything a Servantium email can contain. Write an email as MDX: frontmatter builds the banner and footer, the body is Markdown plus these components. Every sample on this page is rendered by the same code that renders a real email.',
  [['#frontmatter', 'Frontmatter'], ['#tones', 'Tones'], ['#astro', 'Astro'], ['#components', 'Components'], ['#banned', 'Banned'], ['#streams', 'Streams'], ['index.html', 'All emails →']],
  `
<section class="panel" id="frontmatter"><h2>Frontmatter</h2>
<p class="lead">The top of every MDX email, between the <code>---</code> lines. It is checked like a schema: a missing field or a broken rule fails the build and says which.</p>
<div class="cols"><div><pre><code>${esc(FRONTMATTER_EXAMPLE)}</code></pre></div>
<div><table class="ref"><thead><tr><th>Field</th><th></th><th>Values</th></tr></thead><tbody>
${FRONTMATTER.map((f) => `<tr><td><code>${esc(f.field)}</code></td><td>${f.required ? '<span class="req">required</span>' : '<span class="opt">optional</span>'}</td><td>${esc(f.values)}<br><span style="color:var(--ink3)">${esc(f.note)}</span></td></tr>`).join('')}
</tbody></table></div></div></section>

<section class="panel" id="tones"><h2>Tones</h2>
<p class="lead">There is one banner. A tone only changes the rule along its bottom edge, the dot beside the label, and any callout in the body. To pick one, ask a single question: <b>${esc(TONE_QUESTION)}</b></p>
<div class="tones">${(Object.keys(TONE_GUIDE) as Tone[]).map((t) => {
    const b = BANNERS.find((x) => x.key === t)!;
    return `<div class="tone">${srcdoc(bannerDoc(b), `${t} banner`)}<h3><span class="tier"><i style="background:${TONE_DOT[t]}"></i>${t}</span></h3>
<p><b>${esc(TONE_GUIDE[t].answer)}.</b> ${esc(TONE_GUIDE[t].use)}</p><p style="color:var(--ink3)">${esc(TONE_GUIDE[t].examples)}</p></div>`;
  }).join('')}</div></section>

<section class="panel" id="astro"><h2>Astro</h2>
<p class="lead"><b>${esc(ASTRO_RULE)}</b> He sits in the banner's right corner, and the banner grows a little to fit him. Five poses:</p>
<div class="astro-row">${ASTRO_POSES.map((p) => `<figure><img src="assets/astro/astro-${p}.png" alt="Astro, ${p}"><figcaption><code>${p}</code></figcaption></figure>`).join('')}</div>
<div class="cols"><div><h3><span class="yes">Use him on</span></h3><ul class="clean">${ASTRO_USE.map((u) => `<li>${esc(u)}</li>`).join('')}</ul></div>
<div><h3><span class="no">Never on</span></h3><ul class="clean">${ASTRO_NEVER.map(([w, why]) => `<li><b>${esc(w)}</b> — ${esc(why)}</li>`).join('')}</ul></div></div>
<div class="astro-banner">${srcdoc(bannerDoc(BANNERS[1]), 'Banner with Astro')}</div></section>

<section class="panel" id="components"><h2>Components</h2>
<p class="lead">MDX on the left, the email it makes on the right. Components need no import. Anything not on this page isn't available — ask before adding one, so it's added here, once, for every email.</p>
<div class="toggle">Preview at <button data-v="desktop" aria-pressed="true" onclick="view('desktop')">Desktop 640</button><button data-v="phone" aria-pressed="false" onclick="view('phone')">Phone 375</button></div>
${sampleHtml.join('')}</section>

<section class="panel" id="banned"><h2>Banned</h2>
<p class="lead">Rules marked <span class="req">enforced</span> fail <code>npm test</code> or the build. The others are for reviewers.</p>
<table class="ref"><thead><tr><th>Never</th><th></th><th>Why</th></tr></thead><tbody>
${BANNED.map((b) => `<tr><td><b>${esc(b.rule)}</b></td><td>${b.enforced ? '<span class="req">enforced</span>' : '<span class="opt">review</span>'}</td><td>${esc(b.why)}</td></tr>`).join('')}
</tbody></table></section>

<section class="panel" id="streams"><h2>Streams</h2>
<p class="lead">Every email names the Postmark stream that sends it. The stream decides the unsubscribe link, and keeps optional mail from hurting the delivery of mail people need.</p>
<table class="ref"><thead><tr><th>Stream</th><th>For</th><th>Unsubscribe</th></tr></thead><tbody>
<tr><td><code>transactional</code></td><td>About this person's account or something they did: welcome, reset, tasks, incidents, maintenance, required notices.</td><td>Never. It must always arrive. The footer says why they got it.</td></tr>
<tr><td><code>broadcast</code></td><td>Optional reading sent to many: release notes, newsletters, marketing.</td><td>Always. Added automatically: Postmark's <code>{{{ pm:unsubscribe }}}</code>.</td></tr>
</tbody></table></section>
`,
  fit,
);
writeFileSync(join(DIST, 'stylesheet.html'), stylesheet);

// ── Gallery ─────────────────────────────────────────────────────────────────────────────────────
const cards = emails.map((e) => `
<section class="tpl">
  <header><div><span class="tier"><i style="background:${TONE_DOT[e.tone]}"></i>${e.tone} · ${e.stream} · ${e.source}</span><h2>${esc(e.name)}</h2></div>
    <a href="${e.id}.html" target="_blank">Open ↗</a></header>
  <dl><dt>Subject</dt><dd>${esc(e.preview.subject)}</dd><dt>Preview</dt><dd style="color:var(--ink2)">${esc(e.preview.preheader)}</dd>
    <dt>Sends via</dt><dd>${esc(e.sends).replace(/`([^`]+)`/g, '<code>$1</code>')}</dd>
    <dt>Postmark</dt><dd><a href="postmark/${e.id}/content.html">content.html</a> · <a href="postmark/${e.id}/content.txt">content.txt</a> · <a href="postmark/${e.id}/meta.json">meta.json</a></dd></dl>
  <div class="frames">
    <figure><iframe src="${e.id}.html" title="${attr(e.name)} desktop" loading="lazy"></iframe><figcaption>Desktop · 640px</figcaption></figure>
    <figure class="phone"><iframe src="${e.id}.html" title="${attr(e.name)} phone" loading="lazy"></iframe><figcaption>Phone · 375px</figcaption></figure>
  </div>
</section>`);

writeFileSync(join(DIST, 'index.html'), page(
  'Verdant Email',
  'One banner, a handful of components, every Servantium email. Colours from Verdant; company details and images from @servantium/brand. Sample data is the Halcyon demo org; incident and maintenance values are illustrative.',
  [['stylesheet.html', 'Style sheet →'], ['banners.html', 'Banners']],
  `<section class="panel"><h2>How to read this</h2><p class="lead" style="margin:0">Each card is one email. The tag line says its <b>tone</b>, the Postmark <b>stream</b> that sends it, and whether it's written in <b>TSX</b> (fixed words, product data) or <b>MDX</b> (a person writes it). The <a href="stylesheet.html">style sheet</a> shows every component and rule.</p></section>
${cards.join('')}`,
));

console.log(`exported to dist/  (sent images: ${SENT_ASSET_BASE})\n${rows.join('\n')}\n  + stylesheet.html, banners.html, index.html, postmark/, firebase/password-reset.html`);
