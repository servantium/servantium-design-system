/**
 * export — renders every template to static HTML in dist/.
 *
 *   npm run build      (syncs Verdant tokens first)
 *
 * dist/
 *   <id>.html                 preview, sample data, images from ./assets
 *   jinja/<id>.html           for Python senders: `{{ placeholders }}` and `{{ asset_base }}`
 *   firebase/password-reset.html   paste into Firebase → Authentication → Templates
 *   banners.html              the banner in every tone and size
 *   index.html                gallery: every email at desktop and phone width
 *   assets/                   logo, Astro and header art, copied from @servantium/brand
 */
import { cpSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { company } from '@servantium/brand';
import { renderEmail, toFirebaseFragment } from '../src/render';
import { templates } from '../src/index';
import { firebasePlaceholders } from '../src/templates/password-reset';
import { Banner, Body, Email } from '../src/components/Layout';
import { Text } from '../src/components/Content';
import { tones, type Tone } from '../src/theme';

const HERE = dirname(fileURLToPath(import.meta.url));
const DIST = join(HERE, '../dist');
const require = createRequire(import.meta.url);
const BRAND = dirname(require.resolve('@servantium/brand/company.json'));

rmSync(DIST, { recursive: true, force: true });
for (const d of ['', 'jinja', 'firebase', 'assets']) mkdirSync(join(DIST, d), { recursive: true });
for (const d of ['logo', 'astro', 'email']) {
  cpSync(join(BRAND, 'assets', d), join(DIST, 'assets', d), {
    recursive: true, filter: (src) => !src.endsWith('.svg'),
  });
}

const kb = (s: string) => `${(Buffer.byteLength(s) / 1024).toFixed(1)} KB`;
const rows: string[] = [];

for (const t of Object.values(templates)) {
  const s = t.build(t.sample as never);
  const html = renderEmail({ subject: s.subject, preheader: s.preheader, children: s.body });
  writeFileSync(join(DIST, `${t.id}.html`), html);
  rows.push(`  ${t.id.padEnd(20)} ${kb(html)}`);

  if (t.placeholders) {
    const j = t.build(t.placeholders as never);
    writeFileSync(join(DIST, 'jinja', `${t.id}.html`), renderEmail({
      subject: j.subject, preheader: j.preheader, children: j.body,
      assets: { base: '{{ asset_base }}', art: true },
    }));
  }
}

// Firebase sends this one itself: absolute logo URL (servantium.com already hosts it), and no
// header art until the art is hosted somewhere Firebase's recipients can reach.
const fb = templates.passwordReset.build(firebasePlaceholders);
writeFileSync(join(DIST, 'firebase', 'password-reset.html'), toFirebaseFragment(renderEmail({
  subject: fb.subject, preheader: fb.preheader, children: fb.body,
  assets: { base: null, art: false, overrides: { 'logo/servantium-logo-white.png': `${company.urls.website}/brand/servantium-logo-white.png` } },
})));

// ── The banner sheet: one banner, every tone and size ───────────────────────────────────────────
const TONE_USES: Record<Tone, string> = {
  brand: 'Welcome, account, security, marketing',
  activity: 'Tasks, mentions, assignments, reviews',
  product: 'Release notes, new features',
  warning: 'Degraded service, action needed soon',
  critical: 'Outages, security alerts',
  notice: 'Legal, regulatory, policy changes',
};
const sheet = renderEmail({
  subject: 'Servantium email banners',
  preheader: 'The banner in every tone and size.',
  children: (
    <>
      {(Object.keys(tones) as Tone[]).map((tone) => (
        <div key={tone} style={{ marginBottom: '20px' }}>
          <Email>
            <Banner tone={tone} size="compact" />
            <Body><Text size="sm" margin="0"><b>{tone}</b> · {TONE_USES[tone]}</Text></Body>
          </Email>
        </div>
      ))}
      <div style={{ marginBottom: '20px' }}>
        <Email>
          <Banner tone="notice" size="standard" label="Service notice" title="Standard: one headline" />
          <Body><Text size="sm" margin="0">For security, notices and one-off transactional mail.</Text></Body>
        </Email>
      </div>
      <Email>
        <Banner tone="brand" size="hero" label="Welcome" title="Hero: headline and Astro" subtitle="For welcome, release notes and marketing." astro="captain" />
        <Body><Text size="sm" margin="0">Astro poses: waving, captain, detective, professor, cowboy.</Text></Body>
      </Email>
    </>
  ),
});
writeFileSync(join(DIST, 'banners.html'), sheet);

// ── Gallery ─────────────────────────────────────────────────────────────────────────────────────
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const cards = Object.values(templates).map((t) => {
  const s = t.build(t.sample as never);
  return `
<section class="tpl">
  <header><div><span class="tier" data-tone="${t.tone}">${t.tone} · ${t.size}</span><h2>${esc(t.name)}</h2></div>
    <a href="${t.id}.html" target="_blank">Open ↗</a></header>
  <dl><dt>Subject</dt><dd>${esc(s.subject)}</dd><dt>Preview</dt><dd class="muted">${esc(s.preheader)}</dd><dt>Sends via</dt><dd>${esc(t.sendsVia)}</dd></dl>
  <div class="frames">
    <figure><iframe src="${t.id}.html" title="${esc(t.name)} desktop" loading="lazy"></iframe><figcaption>Desktop · 640px</figcaption></figure>
    <figure class="phone"><iframe src="${t.id}.html" title="${esc(t.name)} phone" loading="lazy"></iframe><figcaption>Phone · 375px</figcaption></figure>
  </div>
</section>`;
});
writeFileSync(join(DIST, 'index.html'), `<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Verdant Email</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  :root{--bg:#F5F6F7;--card:#fff;--ink:#1a1a1a;--ink2:#3d3d3d;--ink3:#6b6b6b;--rule:#E1E3E6;--link:#037A47;--forest:#023E25}
  *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 'Source Sans 3',system-ui,sans-serif}
  .hero{background:var(--forest) url(assets/email/header-standard.jpg) right top/cover no-repeat;color:#fff;padding:44px 16px 40px}
  .wrap{max-width:1180px;margin:0 auto;padding:0 16px}
  h1,h2{font-family:'Playfair Display',Georgia,serif;font-weight:600} .hero h1{font-size:36px;margin:0 0 8px} .hero p{margin:0;color:#CFEFDD;max-width:720px}
  .tpl,.panel{background:var(--card);border:1px solid var(--rule);border-radius:14px;margin:24px 0;padding:24px}
  .tpl header{display:flex;justify-content:space-between;align-items:flex-start;gap:12px} .tpl h2{font-size:24px;margin:4px 0 0}
  .tpl header a{color:var(--link);font-weight:600;text-decoration:none;white-space:nowrap}
  .tier{font-size:11px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:var(--ink3)}
  dl{display:grid;grid-template-columns:max-content 1fr;gap:4px 16px;margin:16px 0 20px} dt{color:var(--ink3);font-size:13px} dd{margin:0} .muted{color:var(--ink2)}
  .frames{display:flex;gap:20px;align-items:flex-start;overflow-x:auto;padding-bottom:4px} figure{margin:0;flex:none}
  iframe{width:640px;height:1000px;border:1px solid var(--rule);border-radius:10px;background:var(--bg);display:block} .phone iframe{width:375px}
  .banners iframe{width:640px;height:1180px}
  figcaption{font-size:12px;color:var(--ink3);margin-top:6px} .panel h2{font-size:22px;margin:0 0 8px} .panel li{margin:4px 0}
  @media (max-width:720px){.frames{flex-direction:column} iframe,.phone iframe,.banners iframe{width:100%;max-width:375px}.tpl,.panel{padding:16px}}
</style></head><body>
<div class="hero"><div class="wrap"><h1>Verdant Email</h1>
<p>One banner, a handful of components, every Servantium email. Built from @servantium/verdant-email; colours from Verdant, company details and images from @servantium/brand. Sample data is the Halcyon demo org.</p></div></div>
<main class="wrap">
<section class="panel banners"><h2>The banner</h2><p class="muted">The forest sky in every email. Tone changes the rule, the dot and the label; size is set by how often the email is sent.</p>
<div class="frames"><figure><iframe src="banners.html" title="Banner sheet"></iframe></figure><figure class="phone"><iframe src="banners.html" title="Banner sheet phone"></iframe></figure></div></section>
${cards.join('')}
</main></body></html>`);

console.log(`exported to dist/\n${rows.join('\n')}\n  + jinja/, firebase/password-reset.html, banners.html, index.html`);
