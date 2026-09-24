/**
 * render.mjs — generates every raster brand asset from its source. Run after changing a master.
 *
 *   node packages/brand/scripts/render.mjs
 *
 * Needs Playwright's Chromium (`npx playwright install chromium` once).
 *
 * WHY GENERATED, NOT HAND-EXPORTED
 * Email clients cannot show SVG (Gmail and Outlook both drop it), so Astro and the header art have
 * to exist as PNG. Hand-exported PNGs drift from their masters the first time someone edits one and
 * forgets the other. Here the SVG is the master and every PNG is a build output of it.
 *
 * WHAT IT MAKES
 *   assets/astro/astro-<pose>.png      240×240 — Astro at 2× for a 120px slot
 *   assets/email/header-<size>.svg     the header art master, deterministic (seeded)
 *   assets/email/header-<size>.jpg     the same, rasterised at 2× for email. JPEG, not PNG: this
 *                                      art is all gradient, which PNG stores ~6× larger, and every
 *                                      kilobyte is paid on every open of every email.
 */
import { createRequire } from 'node:module';
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const ASTRO = join(ROOT, 'assets/astro');
const EMAIL = join(ROOT, 'assets/email');
mkdirSync(EMAIL, { recursive: true });

// ── The header art: "forest night sky" ─────────────────────────────────────────────────────────
// Deep forest is the sky. A soft emerald glow in the top-left corner is the login panel's radial
// light. The particles are the trail on the logo's S, spread into a constellation — which is also
// the thing that makes Astro look at home. Everything busy lives on the RIGHT, so a headline on
// the left always sits on calm colour and stays legible.

/** Deterministic PRNG: the same seed draws the same sky, so a re-render is not a redesign. */
function mulberry32(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const T = {
  forest: '#023E25', forestDeep: '#012C1A', forestLift: '#045F37',
  emerald: '#037A47', green: '#00C26D', fresh: '#36D993', jade: '#6FE7B0',
};

function sky({ w, h, seed, count, orbit }) {
  const rand = mulberry32(seed);
  const dots = [];
  for (let i = 0; i < count; i++) {
    // Density rises to the right: x is drawn from a curve that piles up near the far edge.
    const x = w * (0.34 + 0.66 * Math.pow(rand(), 0.55));
    const y = h * rand();
    const near = (x / w - 0.34) / 0.66; // 0 at the calm edge, 1 at the far right
    const r = (1.2 + rand() * 2.6) * (w / 1200);
    const fill = rand() < 0.18 ? '#FFFFFF' : rand() < 0.55 ? T.jade : T.fresh;
    const o = (0.14 + rand() * 0.55) * (0.35 + 0.65 * near);
    dots.push({ x, y, r, fill, o });
  }
  // The network: join near neighbours with hairlines, as in the logo's trail.
  const lines = [];
  const reach = w * 0.085;
  for (let i = 0; i < dots.length; i++) {
    for (let j = i + 1; j < dots.length; j++) {
      const a = dots[i], b = dots[j];
      const d = Math.hypot(a.x - b.x, a.y - b.y);
      if (d < reach && rand() < 0.5) {
        lines.push(`<line x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${b.x.toFixed(1)}" y2="${b.y.toFixed(1)}" stroke="${T.jade}" stroke-width="${(w / 1200).toFixed(2)}" stroke-opacity="${(0.05 + 0.16 * (1 - d / reach)).toFixed(3)}"/>`);
      }
    }
  }
  const orbits = orbit
    ? `<g fill="none" stroke="${T.jade}" stroke-width="${(1.6 * w) / 1200}">
         <ellipse cx="${w * 0.86}" cy="${h * 0.56}" rx="${w * 0.2}" ry="${h * 0.2}" stroke-opacity="0.16" transform="rotate(-14 ${w * 0.86} ${h * 0.56})"/>
         <ellipse cx="${w * 0.86}" cy="${h * 0.56}" rx="${w * 0.29}" ry="${h * 0.31}" stroke-opacity="0.08" transform="rotate(-14 ${w * 0.86} ${h * 0.56})"/>
       </g>`
    : '';
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
  <defs>
    <linearGradient id="depth" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="${T.forestLift}"/>
      <stop offset="0.55" stop-color="${T.forest}"/>
      <stop offset="1" stop-color="${T.forestDeep}"/>
    </linearGradient>
    <radialGradient id="glowA" cx="0.12" cy="-0.15" r="0.75">
      <stop offset="0" stop-color="${T.emerald}" stop-opacity="0.85"/>
      <stop offset="1" stop-color="${T.emerald}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glowB" cx="0.84" cy="0.5" r="0.4">
      <stop offset="0" stop-color="${T.green}" stop-opacity="0.22"/>
      <stop offset="1" stop-color="${T.green}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="${w}" height="${h}" fill="url(#depth)"/>
  <rect width="${w}" height="${h}" fill="url(#glowA)"/>
  <rect width="${w}" height="${h}" fill="url(#glowB)"/>
  ${orbits}
  <g>${lines.join('')}</g>
  <g>${dots.map((d) => `<circle cx="${d.x.toFixed(1)}" cy="${d.y.toFixed(1)}" r="${d.r.toFixed(2)}" fill="${d.fill}" fill-opacity="${d.o.toFixed(3)}"/>`).join('')}</g>
</svg>`;
}

// Two drawings of the one banner: `standard`, and `hero`, which is taller and adds Astro's orbit
// rings. Dimensions are 2× the email slot (600px wide). (A `compact` size existed until the
// banner was simplified to one, 2026-09-24.)
const HEADERS = {
  hero: { w: 1200, h: 480, seed: 417, count: 110, orbit: true },
  standard: { w: 1200, h: 360, seed: 1488, count: 90, orbit: false },
};

const browser = await chromium.launch();
const page = await browser.newPage({ deviceScaleFactor: 1 });

for (const [name, spec] of Object.entries(HEADERS)) {
  const svg = sky(spec);
  writeFileSync(join(EMAIL, `header-${name}.svg`), svg);
  await page.setViewportSize({ width: spec.w, height: spec.h });
  await page.setContent(`<html><body style="margin:0">${svg}</body></html>`);
  await page.screenshot({ path: join(EMAIL, `header-${name}.jpg`), type: 'jpeg', quality: 84, clip: { x: 0, y: 0, width: spec.w, height: spec.h } });
}

// Astro: every pose, 240px square, transparent.
await page.setViewportSize({ width: 240, height: 240 });
for (const file of readdirSync(ASTRO).filter((f) => f.endsWith('.svg'))) {
  const svg = readFileSync(join(ASTRO, file), 'utf8').replace('<svg', '<svg width="240" height="240"');
  await page.setContent(`<html><body style="margin:0;background:transparent">${svg}</body></html>`);
  await page.screenshot({ path: join(ASTRO, file.replace('.svg', '.png')), omitBackground: true, clip: { x: 0, y: 0, width: 240, height: 240 } });
}

await browser.close();
console.log('rendered: header-{hero,standard}.{svg,jpg}, astro-*.png');
