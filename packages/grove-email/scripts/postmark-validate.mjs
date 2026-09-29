/**
 * postmark-validate — asks Postmark itself to render every compiled template before it's pushed.
 *
 *   POSTMARK_SERVER_TOKEN=… node scripts/postmark-validate.mjs
 *
 * For each alias in dist/contract.json it calls Postmark's template validation endpoint twice:
 * once with every field's example, once with the optional fields left out. It fails if Postmark
 * reports a syntax error, if any {{ placeholder }} survives rendering, or if content gated on an
 * optional field still shows without it. The local tests use a standard Mustache engine; this is
 * the check against Postmark's own engine (Mustachio), which scopes sections differently.
 *
 * NOT YET RUN: needs a Postmark server token. Run it once by hand when the account exists.
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const DIST = join(dirname(fileURLToPath(import.meta.url)), '../dist');
const token = process.env.POSTMARK_SERVER_TOKEN;
if (!token) { console.error('POSTMARK_SERVER_TOKEN is not set'); process.exit(1); }

const contract = JSON.parse(readFileSync(join(DIST, 'contract.json'), 'utf8'));
let failed = 0;

async function validate(alias, model) {
  const dir = join(DIST, 'postmark', alias);
  const meta = JSON.parse(readFileSync(join(dir, 'meta.json'), 'utf8'));
  const res = await fetch('https://api.postmarkapp.com/templates/validate', {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'X-Postmark-Server-Token': token },
    body: JSON.stringify({
      Subject: meta.Subject,
      HtmlBody: readFileSync(join(dir, 'content.html'), 'utf8'),
      TextBody: readFileSync(join(dir, 'content.txt'), 'utf8'),
      TestRenderModel: model,
      TemplateType: 'Standard',
    }),
  });
  if (!res.ok) throw new Error(`${alias}: Postmark answered ${res.status} ${await res.text()}`);
  return res.json();
}

for (const [alias, c] of Object.entries(contract)) {
  const full = Object.fromEntries(Object.entries(c.fields).map(([k, f]) => [k, f.example]));
  const optional = Object.entries(c.fields).filter(([, f]) => f.optional).map(([k]) => k);
  const bare = Object.fromEntries(Object.entries(full).filter(([k]) => !optional.includes(k)));

  for (const [label, model] of [['all fields', full], ['required only', bare]]) {
    const r = await validate(alias, model);
    const problems = [];
    if (!r.AllContentIsValid) {
      for (const part of ['Subject', 'HtmlBody', 'TextBody']) {
        for (const err of r[part]?.ValidationErrors ?? []) problems.push(`${part}: ${err.Message} (line ${err.Line})`);
      }
    }
    for (const part of ['Subject', 'HtmlBody', 'TextBody']) {
      const left = (r[part]?.RenderedContent ?? '').match(/\{\{[^}]*\}\}/g) ?? [];
      if (left.length) problems.push(`${part}: unfilled ${left.join(' ')}`);
    }
    if (label === 'required only') {
      for (const k of optional) {
        if ((r.HtmlBody?.RenderedContent ?? '').includes(full[k])) problems.push(`optional \`${k}\` still shows when it's missing`);
      }
    }
    if (problems.length) { failed++; console.error(`✖ ${alias} (${label})\n  ${problems.join('\n  ')}`); }
    else console.log(`✔ ${alias} (${label})`);
  }
}
if (failed) process.exit(1);
