/**
 * collect — every email in the package, TSX and MDX, in one shape. The export writes these out and
 * the tests check them, so the two can never disagree about what exists.
 *
 * Node only. MDX is compiled HERE, at build time, and never at send time: compiling MDX evaluates
 * code, which Cloudflare Workers forbid — and product code shouldn't be rendering emails anyway.
 * It sends a Postmark template by alias and supplies the data.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { renderEmail } from '../src/render';
import { templates } from '../src/index';
import { fillPreview, loadMdxEmail } from '../src/mdx';
import type { Stream } from '../src/template';
import type { Tone } from '../src/theme';

const HERE = dirname(fileURLToPath(import.meta.url));
export const EMAILS_DIR = join(HERE, '../src/emails');

/**
 * Where a SENT email's images load from. assets.servantium.com is PROPOSED, not live — see
 * @servantium/brand README → Hosting. Nothing under dist/postmark/ should be pushed until it is.
 */
export const SENT_ASSET_BASE = process.env.ASSET_BASE ?? 'https://assets.servantium.com/brand';

export type Built = {
  /** File name / template id — also the Postmark alias. */
  id: string;
  name: string;
  source: 'tsx' | 'mdx';
  tone: Tone;
  stream: Stream;
  sends: string;
  /** Sample-filled, images relative — for the gallery. */
  preview: { subject: string; preheader: string; html: string };
  /** `{{ fields }}` intact, images absolute — what goes to Postmark. */
  sent: { subject: string; html: string };
  /** The data the sender supplies, with sample values. */
  model: Record<string, string>;
};

const ORDER = ['welcome', 'password-reset', 'task-notification', 'regulatory-notice', 'release-notes', 'incident', 'maintenance', 'incident-resolved'];
const rank = (id: string) => {
  const i = ORDER.findIndex((o) => id === o || id.startsWith(`${o}-2`));
  return i === -1 ? ORDER.length : i;
};

export async function collect(): Promise<Built[]> {
  const out: Built[] = [];

  for (const t of Object.values(templates)) {
    const s = t.build(t.sample as never);
    const p = t.placeholders ? t.build(t.placeholders as never) : s;
    const model: Record<string, string> = {};
    for (const [k, tag] of Object.entries((t.placeholders ?? {}) as Record<string, string>)) {
      const name = /\{\{\s*([\w.]+)\s*\}\}/.exec(tag)?.[1];
      if (name) model[name] = String((t.sample as Record<string, unknown>)[k]);
    }
    out.push({
      id: t.id, name: t.name, source: 'tsx', tone: t.tone, stream: t.stream, sends: t.sendsVia,
      preview: { subject: s.subject, preheader: s.preheader, html: renderEmail({ subject: s.subject, preheader: s.preheader, children: s.body }) },
      sent: {
        subject: p.subject,
        html: renderEmail({ subject: p.subject, preheader: p.preheader, children: p.body, assets: { base: SENT_ASSET_BASE, art: true } }),
      },
      model,
    });
  }

  for (const file of readdirSync(EMAILS_DIR).filter((f) => f.endsWith('.mdx'))) {
    const id = file.replace(/\.mdx$/, '');
    const e = await loadMdxEmail(readFileSync(join(EMAILS_DIR, file), 'utf8'), `src/emails/${file}`);
    const fm = e.frontmatter;
    const preview = e.preview;
    out.push({
      id, name: fm.name ?? id, source: 'mdx', tone: fm.tone, stream: fm.stream,
      sends: fm.sends ?? `Postmark template \`${id}\`, ${fm.stream} stream`,
      preview: {
        subject: fillPreview(fm.subject, fm.preview, false),
        preheader: fillPreview(fm.preheader, fm.preview, false),
        html: preview(renderEmail({ subject: fm.subject, preheader: fm.preheader, children: e.body })),
      },
      sent: {
        subject: fm.subject,
        html: renderEmail({ subject: fm.subject, preheader: fm.preheader, children: e.body, assets: { base: SENT_ASSET_BASE, art: true } }),
      },
      model: fm.preview ?? {},
    });
  }

  return out.sort((a, b) => rank(a.id) - rank(b.id));
}
