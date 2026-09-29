/**
 * mdx — author an email as MDX with frontmatter, the way the help site writes a page.
 *
 *   ---
 *   subject: What's new in Servantium — June 2026
 *   preheader: Search that respects your access rules, and contact workspaces.
 *   label: Release notes
 *   title: What's new in Servantium
 *   astro: professor
 *   stream: broadcast
 *   footer:
 *     reason: You're receiving product updates because you're a Servantium user.
 *   fields:
 *     first_name: { example: Jules, note: The recipient's first name }
 *   ---
 *   Hi {{ first_name }},
 *
 *   ## Highlights
 *   <Items items={[...]} />
 *   <Button href="https://help.servantium.com/release-notes">Read the full release notes</Button>
 *
 * FRONTMATTER builds the frame — banner, footer, stream — and declares the FIELDS: the data the
 * sender must supply. That list is the contract with engineering; the build fails if the email
 * uses a field it doesn't declare, or declares one it never uses. The BODY is Markdown
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
import { ASTRO_POSES, company, type AstroPose } from '@servantium/brand';
import { Banner, Body, Email, Footer } from './components/Layout';
import {
  Button, Callout, Chip, CodeBlock, DataTable, Divider, Eyebrow, Heading, Items, Link, LinkFallback,
  List, ListItem, Paragraphs, Spacer, Steps, Text, Thread, Updates,
} from './components/Content';
import { renderEmail, type AssetOptions } from './render';
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
  tone: Tone;
  astro?: AstroPose;
  stream: Stream;
  footer: { reason: string; settings?: string };
  /**
   * The data the sender supplies — the contract with engineering. Each field has an example (the
   * gallery shows it; it is never sent), an optional note for whoever wires it, and `optional: true`
   * when the email reads fine without it (see <If>).
   */
  fields: Record<string, Field>;
};

/** A field is text, or a list of items (each item a map of text fields) that the email repeats. */
export type Item = Record<string, string>;
export type Field = { example: string | Item[]; note?: string; optional?: boolean };
export const isList = (f: Field): f is Field & { example: Item[] } => Array.isArray(f.example);
const itemKeys = (f: Field) => [...new Set((f.example as Item[]).flatMap((i) => Object.keys(i)))];

const TONES = Object.keys(tones) as Tone[];

export class FrontmatterError extends Error {}

export function validate(raw: unknown, where = 'email'): Frontmatter {
  const fm = (raw ?? {}) as Record<string, unknown>;
  const problems: string[] = [];
  const need = (k: string) => { if (typeof fm[k] !== 'string' || !(fm[k] as string).trim()) problems.push(`\`${k}\` is required`); };
  ['subject', 'preheader', 'label', 'title', 'stream'].forEach(need);

  if (fm.subtitle !== undefined) problems.push('`subtitle` is gone: the banner carries one line. Put the detail in the body.');
  if (typeof fm.title === 'string') {
    if (fm.title.includes('{{')) problems.push('`title` can\'t contain fields: the banner line is the same on every send, so it always fits on one line');
    if (fm.title.length > 24) problems.push(`\`title\` is ${fm.title.length} characters; the banner fits 24 on one line`);
  }
  if (typeof fm.label === 'string' && !fm.label.includes('{{') && fm.label.length > 16) problems.push(`\`label\` is ${fm.label.length} characters; 16 at most`);

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
  } else if (footer.reason.length > 90) {
    problems.push(`\`footer.reason\` is ${footer.reason.length} characters; keep it to one short sentence (90 at most)`);
  }
  const fields: Record<string, Field> = {};
  const rawFields = (fm.fields ?? {}) as Record<string, unknown>;
  if (typeof rawFields !== 'object' || Array.isArray(rawFields)) problems.push('`fields` must be a map of field name → example');
  for (const [name, v] of Object.entries(rawFields)) {
    if (!/^[a-z][a-z0-9_]*$/.test(name)) problems.push(`field \`${name}\` must be snake_case`);
    if (typeof v === 'string' || typeof v === 'number') fields[name] = { example: String(v) };
    else if (v && typeof v === 'object' && 'example' in v) {
      const o = v as Record<string, unknown>;
      const ex = Array.isArray(o.example)
        ? (o.example as Record<string, unknown>[]).map((i) => Object.fromEntries(Object.entries(i).map(([k, x]) => [k, String(x)])))
        : String(o.example);
      if (Array.isArray(ex) && !ex.length) problems.push(`list field \`${name}\` needs at least one example item`);
      fields[name] = { example: ex, note: o.note as string | undefined, optional: o.optional === true };
    } else problems.push(`field \`${name}\` needs an example`);
  }
  if (problems.length) throw new FrontmatterError(`${where}:\n  · ${problems.join('\n  · ')}`);

  return {
    name: fm.name as string | undefined,
    sends: fm.sends as string | undefined,
    subject: fm.subject as string,
    preheader: fm.preheader as string,
    label: fm.label as string,
    title: fm.title as string,
    tone,
    astro: fm.astro as AstroPose | undefined,
    stream: fm.stream as Stream,
    footer: { reason: footer.reason as string, settings: footer.settings as string | undefined },
    fields,
  };
}

/**
 * The contract check, run on the COMPILED email (subject, preheader, banner, body and footer are all
 * in it). Postmark scopes sections and loops, so the rules follow Postmark:
 *   · outside any section, every {{ field }} must be a declared text field;
 *   · inside {{#each list}}, only that list's item fields;
 *   · inside {{#field}} or {{^field}} (from <If> and <Editable>), only {{ . }};
 *   · every declared field must be used somewhere.
 */
export function checkContract(fm: Frontmatter, html: string, where = 'email') {
  const problems: string[] = [];
  const used = new Set<string>();
  let rest = html;

  rest = rest.replace(/\{\{#each (\w+)\}\}([\s\S]*?)\{\{\/each\}\}/g, (_, name: string, inner: string) => {
    used.add(name);
    const f = fm.fields[name];
    if (!f) problems.push(`repeats \`${name}\` but doesn't declare it under \`fields\``);
    else if (!isList(f)) problems.push(`repeats \`${name}\`, but its example isn't a list of items`);
    const keys = f && isList(f) ? itemKeys(f) : [];
    for (const m of inner.matchAll(/\{\{\s*([\w.]+)\s*\}\}/g)) {
      if (!keys.includes(m[1])) problems.push(`\`{{ ${m[1]} }}\` inside the \`${name}\` list isn't one of its item fields (${keys.join(', ')})`);
    }
    return '';
  });
  rest = rest.replace(/\{\{([#^])(\w+)\}\}([\s\S]*?)\{\{\/\2\}\}/g, (_, _k: string, name: string, inner: string) => {
    used.add(name);
    if (!fm.fields[name]) problems.push(`shows content only when \`${name}\` is set, but doesn't declare it under \`fields\``);
    for (const m of inner.matchAll(/\{\{\s*([\w.]+)\s*\}\}/g)) {
      if (m[1] !== '.') problems.push(`\`{{ ${m[1]} }}\` inside the \`${name}\` section — only the section's own value ({{ . }}) is allowed there`);
    }
    return '';
  });
  for (const m of rest.matchAll(/\{\{\s*([\w.]+)\s*\}\}/g)) {
    const name = m[1];
    used.add(name);
    const f = fm.fields[name];
    if (!f) problems.push(`uses \`{{ ${name} }}\` but doesn't declare it under \`fields\``);
    else if (isList(f)) problems.push(`uses the list \`${name}\` as text — repeat it with a list component instead`);
  }
  for (const name of Object.keys(fm.fields)) if (!used.has(name)) problems.push(`declares \`${name}\` under \`fields\` but never uses it`);
  if (problems.length) throw new FrontmatterError(`${where}:\n  · ${[...new Set(problems)].join('\n  · ')}`);
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
      if (c === ']' && src[i + 1] === '(') {
        // A Markdown link's URL is literal — `[plan]({{ plan_url }})` must stay as written.
        const close = src.indexOf(')', i + 2);
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

/**
 * Fill fields with their examples — for the gallery, never for a send. Handles sections the way
 * Postmark does: {{#f}}…{{/f}} shows when f has a value (with {{ . }} as that value), {{^f}}…{{/f}}
 * when it doesn't.
 */
export type Values = Record<string, string | Item[]>;
export const fillPreview = (html: string, values: Values = {}, escape = true): string => {
  const v = (name: string) => (escape ? escHtml(String(values[name])) : String(values[name]));
  const present = (name: string) => (Array.isArray(values[name]) ? (values[name] as Item[]).length > 0 : Boolean(values[name]));
  return html
    .replace(/\{\{#each (\w+)\}\}([\s\S]*?)\{\{\/each\}\}/g, (_, name: string, inner: string) =>
      (Array.isArray(values[name]) ? (values[name] as Item[]).map((item) => fillPreview(inner, item, escape)).join('') : ''))
    .replace(/\{\{#(\w+)\}\}([\s\S]*?)\{\{\/\1\}\}/g, (_, name: string, inner: string) => (present(name) ? inner.replace(/\{\{\s*\.\s*\}\}/g, v(name)) : ''))
    .replace(/\{\{\^(\w+)\}\}([\s\S]*?)\{\{\/\1\}\}/g, (_, name: string, inner: string) => (present(name) ? '' : inner))
    .replace(MERGE, (tag, name: string) => (name in values ? v(name) : tag));
};

// ── Postmark-native building blocks ─────────────────────────────────────────────────────────────
/** Shows its content only when the sender supplies `field`. Inside, {{ . }} is that value. */
export function If({ field, children }: { field: string; children?: ReactNode }) {
  return <>{`{{#${field}}}`}{children}{`{{/${field}}}`}</>;
}

/**
 * Copy an admin can override later WITHOUT a template change: the sender passes `field` to replace
 * the default; leave it out and the default shows. Postmark does this natively, so admin-editable
 * emails need data, not a new rendering system.
 */
export function Editable({ field, children }: { field: string; children?: ReactNode }) {
  return <>{`{{#${field}}}`}<Text>{'{{ . }}'}</Text>{`{{/${field}}}{{^${field}}}`}<Text>{children}</Text>{`{{/${field}}}`}</>;
}

type UrlKey = keyof typeof company.urls;
/** A link to a Servantium address from company.json — so body links move when the address does. */
function CompanyLink({ to, children }: { to: UrlKey; children?: ReactNode }) {
  return <Link href={company.urls[to]}>{children ?? company.urls[to].replace(/^https:\/\//, '').replace(/\/$/, '')}</Link>;
}
/** Button that also accepts `to="trust"` for a company.json address. */
function MdxButton({ to, href, ...rest }: { to?: UrlKey; href?: string; children: string; variant?: 'primary' | 'secondary'; width?: number }) {
  return <Button href={to ? company.urls[to] : (href ?? '#')} {...rest} />;
}

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
  Button: MdxButton, Callout, Chip, DataTable, Divider, Eyebrow, Items, LinkFallback, Spacer, Text, Heading, Link, CodeBlock,
  CompanyLink, If, Editable, Updates, Steps, Paragraphs, Thread,
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

export const examples = (fm: Frontmatter): Values =>
  Object.fromEntries(Object.entries(fm.fields).map(([k, f]) => [k, f.example]));

export type MdxEmail = {
  frontmatter: Frontmatter;
  subject: string;
  preheader: string;
  body: ReactElement;
  /** `{{ fields }}` filled with the declared examples. For the gallery only. */
  preview: (html: string) => string;
  /** Field name → example, for tests and previews. */
  examples: Values;
};

export async function loadMdxEmail(source: string, where = 'email', opts: LoadOptions = {}): Promise<MdxEmail> {
  const { data, body } = splitFrontmatter(source);
  const fm = validate(data, where);

  const content = await mdxBody(body);

  const unsubscribe = fm.stream === 'broadcast' ? (opts.unsubscribeHref ?? POSTMARK_UNSUBSCRIBE) : undefined;
  const banner = fm.tone === 'default'
    ? <Banner label={fm.label} title={fm.title} astro={fm.astro} />
    : <Banner tone={fm.tone} label={fm.label} title={fm.title} />;

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
    preview: (html) => fillPreview(html, examples(fm)),
    examples: examples(fm),
  };
}

/** Load, render and contract-check a master in one step — what the build and the tests use. */
export async function compileMdxEmail(source: string, where = 'email', assets?: AssetOptions) {
  const email = await loadMdxEmail(source, where);
  const html = renderEmail({ subject: email.subject, preheader: email.preheader, children: email.body, assets });
  checkContract(email.frontmatter, html, where);
  return { email, html };
}
