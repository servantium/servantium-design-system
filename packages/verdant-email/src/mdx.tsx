/**
 * mdx — author an email as MDX with frontmatter, the way the help site writes a page.
 *
 *   ---
 *   subject: What's new in Servantium — June 2026
 *   preheader: Search that respects your access rules, and contact workspaces.
 *   label: Release notes
 *   title: What's new in Servantium
 *   subtitle: June 2026
 *   astro: professor
 *   stream: broadcast
 *   footer:
 *     reason: You're receiving product updates because you're a Servantium user.
 *   preview:
 *     first_name: Jules
 *   ---
 *   Hi {{ first_name }},
 *
 *   ## Highlights
 *   <Items items={[...]} />
 *   <Button href="https://help.servantium.com/release-notes">Read the full release notes</Button>
 *
 * FRONTMATTER builds the frame — banner, footer, stream, merge-field previews. The BODY is Markdown
 * plus the components in the style sheet. Markdown maps onto email-safe components: a paragraph is
 * <Text>, `##` is <Heading>, a `-` list is <List>, a link is <Link>, `---` is <Divider>.
 *
 * The frontmatter is VALIDATED, like a content collection schema, and the rules it enforces are the
 * style sheet's rules: Astro only on the default tone, an unsubscribe on broadcast mail and never on
 * transactional mail. A rule broken in the frontmatter fails the build with a sentence, not a stack.
 */
import type { ReactElement, ReactNode } from 'react';
import { evaluate } from '@mdx-js/mdx';
import * as runtime from 'react/jsx-runtime';
import { parse as parseYaml } from 'yaml';
import { ASTRO_POSES, type AstroPose } from '@servantium/brand';
import { Banner, Body, Email, Footer } from './components/Layout';
import {
  Button, Callout, Chip, CodeBlock, DataTable, Divider, Eyebrow, Heading, Items, Link, LinkFallback,
  List, ListItem, Spacer, Text,
} from './components/Content';
import { tones, type Tone } from './theme';
import type { Stream } from './template';

// ── The frontmatter schema ──────────────────────────────────────────────────────────────────────
export type Frontmatter = {
  /** Gallery name. Defaults to the file name. */
  name?: string;
  /** Who sends it and when, in plain words — the gallery prints it. */
  sends?: string;
  subject: string;
  preheader: string;
  label: string;
  title: string;
  subtitle?: string;
  tone: Tone;
  astro?: AstroPose;
  stream: Stream;
  footer: { reason: string; settings?: string };
  /** Merge-field values for the preview only. The sent email keeps `{{ field }}` for the sender. */
  preview?: Record<string, string>;
};

const TONES = Object.keys(tones) as Tone[];

export class FrontmatterError extends Error {}

export function validate(raw: unknown, where = 'email'): Frontmatter {
  const fm = (raw ?? {}) as Record<string, unknown>;
  const problems: string[] = [];
  const need = (k: string) => { if (typeof fm[k] !== 'string' || !(fm[k] as string).trim()) problems.push(`\`${k}\` is required`); };
  ['subject', 'preheader', 'label', 'title', 'stream'].forEach(need);

  const tone = (fm.tone ?? 'default') as Tone;
  if (!TONES.includes(tone)) problems.push(`\`tone\` must be one of ${TONES.join(', ')} — got "${fm.tone}"`);
  if (fm.stream && fm.stream !== 'transactional' && fm.stream !== 'broadcast') {
    problems.push('`stream` must be transactional or broadcast');
  }
  if (fm.astro !== undefined) {
    if (!ASTRO_POSES.includes(fm.astro as AstroPose)) problems.push(`\`astro\` must be one of ${ASTRO_POSES.join(', ')}`);
    if (tone !== 'default') problems.push(`Astro is for good news only — remove \`astro\` or use the default tone (this email is "${tone}")`);
  }
  const footer = (fm.footer ?? {}) as Record<string, unknown>;
  if (typeof footer.reason !== 'string' || !footer.reason.trim()) {
    problems.push('`footer.reason` is required — every email must say why the reader got it');
  }
  if (problems.length) throw new FrontmatterError(`${where}:\n  · ${problems.join('\n  · ')}`);

  return {
    name: fm.name as string | undefined,
    sends: fm.sends as string | undefined,
    subject: fm.subject as string,
    preheader: fm.preheader as string,
    label: fm.label as string,
    title: fm.title as string,
    subtitle: fm.subtitle as string | undefined,
    tone,
    astro: fm.astro as AstroPose | undefined,
    stream: fm.stream as Stream,
    footer: { reason: footer.reason as string, settings: footer.settings as string | undefined },
    preview: fm.preview as Record<string, string> | undefined,
  };
}

export function splitFrontmatter(source: string): { data: unknown; body: string } {
  const m = source.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
  if (!m) return { data: {}, body: source };
  return { data: parseYaml(m[1]), body: m[2] };
}

// ── Merge fields ────────────────────────────────────────────────────────────────────────────────
/**
 * `{{ name }}` is Postmark's (and Jinja's) placeholder, and it goes through to the sent HTML
 * untouched — in body text, in component props, in the banner title. MDX reads `{` as JavaScript,
 * so in Markdown TEXT the tag is wrapped as a string expression, `{'{{ name }}'}`. Inside JSX props,
 * expressions and code it is already literal and is left alone.
 */
export function protectMergeFields(src: string): string {
  let out = '';
  let depth = 0;
  let inTag = false;
  let fence = false;
  for (let i = 0; i < src.length; i++) {
    const c = src[i];
    if ((i === 0 || src[i - 1] === '\n') && src.startsWith('```', i)) {
      fence = !fence;
      const eol = src.indexOf('\n', i);
      const end = eol === -1 ? src.length : eol + 1;
      out += src.slice(i, end);
      i = end - 1;
      continue;
    }
    if (fence) { out += c; continue; }
    if (depth === 0 && !inTag) {
      if (c === '`') {
        const close = src.indexOf('`', i + 1);
        if (close > -1) { out += src.slice(i, close + 1); i = close; continue; }
      }
      const m = /^\{\{\s*[\w.]+\s*\}\}/.exec(src.slice(i, i + 80));
      if (m) {
        // Alone on its line, MDX would treat the expression as a block and skip the paragraph
        // styling, so a whole-line field is wrapped in <Text> explicitly.
        const lineStart = src.lastIndexOf('\n', i - 1) + 1;
        const eol = src.indexOf('\n', i);
        const alone = !src.slice(lineStart, i).trim() && !src.slice(i + m[0].length, eol === -1 ? undefined : eol).trim();
        out += alone ? `<Text>{'${m[0]}'}</Text>` : `{'${m[0]}'}`;
        i += m[0].length - 1;
        continue;
      }
      if (c === '<' && /[A-Za-z/]/.test(src[i + 1] ?? '')) inTag = true;
    }
    if (c === '{') depth++;
    else if (c === '}') depth = Math.max(0, depth - 1);
    else if (c === '>' && inTag && depth === 0) inTag = false;
    out += c;
  }
  return out;
}

const MERGE = /\{\{\s*([\w.]+)\s*\}\}/g;
const escHtml = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/** Fill `{{ name }}` from the frontmatter's `preview` block — for the gallery, never for a send. */
export const fillPreview = (html: string, values: Record<string, string> = {}, escape = true) =>
  html.replace(MERGE, (tag, name: string) => (name in values ? (escape ? escHtml(values[name]) : values[name]) : tag));

// ── Markdown → email components ─────────────────────────────────────────────────────────────────
const Pre = ({ children }: { children?: ReactNode }) => {
  const code = (children as { props?: { children?: string } })?.props?.children ?? '';
  return <CodeBlock>{String(code).replace(/\n$/, '')}</CodeBlock>;
};

const markdown = {
  p: ({ children }: { children?: ReactNode }) => <Text>{children}</Text>,
  h1: ({ children }: { children?: ReactNode }) => <Heading level={1}>{children}</Heading>,
  h2: ({ children }: { children?: ReactNode }) => <Heading>{children}</Heading>,
  h3: ({ children }: { children?: ReactNode }) => <Heading>{children}</Heading>,
  a: ({ href, children }: { href?: string; children?: ReactNode }) => <Link href={href ?? '#'}>{children}</Link>,
  ul: ({ children }: { children?: ReactNode }) => <List>{children}</List>,
  ol: ({ children }: { children?: ReactNode }) => <List>{children}</List>,
  li: ({ children }: { children?: ReactNode }) => <ListItem>{children}</ListItem>,
  hr: () => <Divider />,
  pre: Pre,
  code: ({ children }: { children?: ReactNode }) => (
    <code style={{ fontFamily: "Menlo, Consolas, 'Courier New', monospace", fontSize: '13px', backgroundColor: '#F5F6F7', padding: '1px 4px', borderRadius: '4px' }}>{children}</code>
  ),
};

/** Everything an MDX email may use. The style sheet documents each one. */
export const mdxComponents = {
  ...markdown,
  Button, Callout, Chip, DataTable, Divider, Eyebrow, Items, LinkFallback, Spacer, Text, Heading, Link, CodeBlock,
};

// ── Load ────────────────────────────────────────────────────────────────────────────────────────
export type LoadOptions = {
  /** Broadcast only: the provider's unsubscribe link. Postmark: `{{{ pm:unsubscribe }}}`. */
  unsubscribeHref?: string;
};

export const POSTMARK_UNSUBSCRIBE = '{{{ pm:unsubscribe }}}';

/** Just the body of an MDX email (no frontmatter) — also how the style sheet renders its samples. */
export async function mdxBody(source: string): Promise<ReactElement> {
  const { default: Content } = await evaluate(protectMergeFields(source), { ...runtime, development: false } as never);
  return <Content components={mdxComponents as never} />;
}

export type MdxEmail = {
  frontmatter: Frontmatter;
  subject: string;
  preheader: string;
  body: ReactElement;
  /** `{{ fields }}` filled from the frontmatter's `preview` block. For the gallery only. */
  preview: (html: string) => string;
};

export async function loadMdxEmail(source: string, where = 'email', opts: LoadOptions = {}): Promise<MdxEmail> {
  const { data, body } = splitFrontmatter(source);
  const fm = validate(data, where);

  const content = await mdxBody(body);

  const unsubscribe = fm.stream === 'broadcast' ? (opts.unsubscribeHref ?? POSTMARK_UNSUBSCRIBE) : undefined;
  const banner = fm.tone === 'default'
    ? <Banner label={fm.label} title={fm.title} subtitle={fm.subtitle} astro={fm.astro} />
    : <Banner tone={fm.tone} label={fm.label} title={fm.title} subtitle={fm.subtitle} />;

  return {
    frontmatter: fm,
    subject: fm.subject,
    preheader: fm.preheader,
    body: (
      <Email>
        {banner}
        <Body>{content}</Body>
        <Footer reason={fm.footer.reason} settingsHref={fm.footer.settings} unsubscribeHref={unsubscribe} />
      </Email>
    ),
    preview: (html) => fillPreview(html, fm.preview),
  };
}
