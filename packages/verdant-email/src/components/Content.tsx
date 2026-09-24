/**
 * Content — the pieces that go inside <Body>. Each one is the ONLY way this package draws that
 * thing, so a change here changes every email.
 *
 * ── BANNED, and enforced by test/rules.test.tsx ───────────────────────────────────────────────
 *   · A coloured bar down the left of a section (design decision, 2026-09-24).
 *     Callout carries its tone as a full tint instead. No component here accepts a border-left.
 *   · SVG images — Gmail and Outlook drop them.
 *   · flex / grid — Outlook desktop has no idea what they are.
 */
import type { ReactNode } from 'react';
import { Raw } from '../render';
import { color, fonts, neutral, tones, type Tone } from '../theme';

/** A tone, or `neutral` for panels that aren't a warning or good news — a quoted note, a code sample. */
export type Tint = Tone | 'neutral';
const tint = (t: Tint) => (t === 'neutral' ? neutral : tones[t]);

const escAttr = (s: string) => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
const escText = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// ── Type ───────────────────────────────────────────────────────────────────────────────────────
/** In-body headings. Level 1 is the serif title (for emails whose banner carries no title);
 *  level 2 is the section heading. */
export function Heading({ level = 2, children, margin }: { level?: 1 | 2; children: ReactNode; margin?: string }) {
  if (level === 1) {
    return (
      <h1 className="ve-title" style={{ margin: margin ?? '0 0 20px', fontFamily: fonts.display, fontSize: '28px',
        lineHeight: '36px', fontWeight: 600, color: color.ink }}>{children}</h1>
    );
  }
  return (
    <h2 style={{ margin: margin ?? '28px 0 8px', fontFamily: fonts.body, fontSize: '17px', lineHeight: '24px',
      fontWeight: 700, color: color.ink }}>{children}</h2>
  );
}

const SIZES = { md: ['16px', '26px'], sm: ['14px', '22px'], xs: ['13px', '20px'] } as const;

export function Text({ children, size = 'md', muted, bold, margin }: {
  children: ReactNode; size?: keyof typeof SIZES; muted?: boolean; bold?: boolean; margin?: string;
}) {
  const [fs, lh] = SIZES[size];
  return (
    <p style={{ margin: margin ?? '0 0 16px', fontFamily: fonts.body, fontSize: fs, lineHeight: lh,
      fontWeight: bold ? 700 : 400, color: muted ? color.inkMuted : color.ink }}>{children}</p>
  );
}

/** Small uppercase line above a title — breadcrumbs like "AUR-417 · Phase II". */
export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <p style={{ margin: '0 0 8px', fontFamily: fonts.body, fontSize: '12px', lineHeight: '16px', fontWeight: 700,
      letterSpacing: '1px', textTransform: 'uppercase', color: color.inkMuted }}>{children}</p>
  );
}

export function Link({ href, children }: { href: string; children: ReactNode }) {
  return <a href={href} style={{ color: color.link, fontWeight: 600, textDecoration: 'underline' }}>{children}</a>;
}

// ── Button ─────────────────────────────────────────────────────────────────────────────────────
/**
 * The welcome email's button, made the standard. Outlook desktop gets a VML shape (otherwise it
 * draws a bare link); every other client gets a padded link.
 *
 *   primary    the one action the email exists for. #00C26D with white text (design decision).
 *   secondary  an outline, for a second action or for notices, where a filled green button reads
 *              as a marketing call to action.
 *
 * `width` is Outlook's only — VML can't size to its label, so a long label needs a wider shape.
 */
export function Button({ href, children, variant = 'primary', width = 220 }: {
  href: string; children: string; variant?: 'primary' | 'secondary'; width?: number;
}) {
  const primary = variant === 'primary';
  const fill = primary ? color.brand : color.surface;
  const fg = primary ? '#FFFFFF' : color.banner;
  const border = primary ? color.brand : color.banner;
  const stroke = primary ? 'stroke="f"' : `strokecolor="${border}" strokeweight="1.5px"`;
  const h = escAttr(href);
  const label = escText(children);
  const html =
    `<!--[if mso]><v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="${h}" style="height:48px;v-text-anchor:middle;width:${width}px;" arcsize="17%" ${stroke} fillcolor="${fill}"><w:anchorlock/><center style="color:${fg};font-family:Arial,sans-serif;font-size:16px;font-weight:bold;">${label}</center></v:roundrect><![endif]-->` +
    `<!--[if !mso]><!--><a href="${h}" style="display:inline-block;padding:13px 28px;font-family:${escAttr(fonts.body)};font-size:16px;line-height:22px;font-weight:700;color:${fg};text-decoration:none;border-radius:8px;border:1.5px solid ${border};background-color:${fill};">${label}</a><!--<![endif]-->`;
  return (
    <table role="presentation" className="ve-btn" cellPadding={0} cellSpacing={0} border={0}>
      <tbody><tr><td align="center" bgcolor={fill} style={{ borderRadius: '8px' }}><Raw html={html} /></td></tr></tbody>
    </table>
  );
}

// ── DataTable ──────────────────────────────────────────────────────────────────────────────────
/**
 * The welcome email's detail table, made the standard: label on the left, value on the right,
 * hairlines between rows. `panel` sits on a grey card (details in the flow of a message); `outline`
 * is a white card with a border (a record a reader will refer back to, like a legal summary).
 */
export function DataTable({ rows, title, variant = 'panel', labelWidth = 128 }: {
  rows: [label: string, value: ReactNode][]; title?: ReactNode; variant?: 'panel' | 'outline'; labelWidth?: number;
}) {
  const bg = variant === 'panel' ? color.panel : color.surface;
  return (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0} bgcolor={bg}
      style={{ backgroundColor: bg, borderRadius: '10px', border: `1px solid ${color.rule}` }}>
      <tbody><tr><td style={{ padding: title ? '18px 20px 8px' : '8px 20px' }}>
        {title && (
          <p style={{ margin: '0 0 6px', fontFamily: fonts.body, fontSize: '18px', lineHeight: '26px', fontWeight: 700, color: color.ink }}>
            {title}
          </p>
        )}
        <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0}>
          <tbody>
            {rows.map(([label, value], i) => {
              const top = i ? { borderTop: `1px solid ${color.rule}` } : {};
              return (
                <tr key={label}>
                  <td className="ve-kv-label" width={labelWidth} valign="top" style={{ ...top, padding: '10px 12px 10px 0',
                    fontFamily: fonts.body, fontSize: '13px', lineHeight: '20px', color: color.inkMuted }}>{label}</td>
                  <td valign="top" style={{ ...top, padding: '10px 0', fontFamily: fonts.body, fontSize: '15px',
                    lineHeight: '22px', color: color.ink }}>{value}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </td></tr></tbody>
    </table>
  );
}

// ── Callout ────────────────────────────────────────────────────────────────────────────────────
/**
 * A tinted panel for the one thing a reader must not miss — a security warning, an action
 * required. The tone lives in the WHOLE tint and the title colour. There is no left bar: that is
 * banned, and this component offers no way to draw one.
 */
export function Callout({ tone = 'default', title, children }: { tone?: Tint; title?: string; children: ReactNode }) {
  const t = tint(tone);
  return (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0} bgcolor={t.tint}
      style={{ backgroundColor: t.tint, borderRadius: '10px' }}>
      <tbody><tr><td style={{ padding: '16px 20px', fontFamily: fonts.body, fontSize: '15px', lineHeight: '23px', color: color.ink }}>
        {title && <p style={{ margin: '0 0 4px', fontFamily: fonts.body, fontSize: '15px', lineHeight: '22px', fontWeight: 700, color: t.strong }}>{title}</p>}
        {children}
      </td></tr></tbody>
    </table>
  );
}

// ── Chip ───────────────────────────────────────────────────────────────────────────────────────
/** A small tinted label — "New", "Improved", "Resolved". */
export function Chip({ tone = 'default', children }: { tone?: Tint; children: string }) {
  const t = tint(tone);
  return (
    <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: '999px', backgroundColor: t.tint, color: t.strong,
      fontFamily: fonts.body, fontSize: '11px', lineHeight: '16px', fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase' }}>
      {children}
    </span>
  );
}

// ── Items ──────────────────────────────────────────────────────────────────────────────────────
/** A run of titled items — "Once you're in", release notes, incident updates. */
export function Items({ items }: { items: { title: ReactNode; body: ReactNode; chip?: { tone: Tint; label: string }; meta?: ReactNode }[] }) {
  return (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0}>
      <tbody>
        {items.map((it, i) => (
          <tr key={i}>
            <td style={{ padding: i ? '18px 0 0' : '0', borderTop: i ? `1px solid ${color.rule}` : '0' }}>
              <div>
                {(it.chip || it.meta) && (
                  <p style={{ margin: '0 0 6px', fontFamily: fonts.body, fontSize: '13px', lineHeight: '18px', color: color.inkMuted }}>
                    {it.chip && <Chip tone={it.chip.tone}>{it.chip.label}</Chip>}
                    {it.chip && it.meta && <>&nbsp;&nbsp;</>}
                    {it.meta}
                  </p>
                )}
                <p style={{ margin: '0 0 4px', fontFamily: fonts.body, fontSize: '16px', lineHeight: '24px', fontWeight: 700, color: color.ink }}>{it.title}</p>
                <p style={{ margin: '0 0 18px', fontFamily: fonts.body, fontSize: '15px', lineHeight: '23px', color: color.ink }}>{it.body}</p>
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// ── Spacing & rules ────────────────────────────────────────────────────────────────────────────
export function Spacer({ size = 24 }: { size?: number }) {
  return <div style={{ height: `${size}px`, lineHeight: `${size}px`, fontSize: '0' }}>&nbsp;</div>;
}

export function Divider({ margin = '28px 0' }: { margin?: string }) {
  return (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0} style={{ margin }}>
      <tbody><tr><td height={1} style={{ height: '1px', lineHeight: '1px', fontSize: '0', borderTop: `1px solid ${color.rule}` }}>&nbsp;</td></tr></tbody>
    </table>
  );
}

/** The URL printed in full under a button — some clients mangle buttons; a pasted link always works. */
export function LinkFallback({ href }: { href: string }) {
  return (
    <Text size="xs" muted margin="0">
      Button not working? Paste this link into your browser:<br />
      <a href={href} style={{ color: color.link, textDecoration: 'underline', wordBreak: 'break-all' }}>{href}</a>
    </Text>
  );
}

// ── Bulleted list ──────────────────────────────────────────────────────────────────────────────
/**
 * What a Markdown `-` list becomes. A table, not a <ul>: Outlook desktop indents and spaces <ul>
 * unpredictably, and Gmail strips list padding. A two-column table draws the same bullets everywhere.
 */
export function List({ children }: { children: ReactNode }) {
  return (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0} style={{ margin: '0 0 16px' }}>
      <tbody>{children}</tbody>
    </table>
  );
}

export function ListItem({ children }: { children: ReactNode }) {
  return (
    <tr>
      <td width={20} valign="top" style={{ padding: '0 0 8px', fontFamily: fonts.body, fontSize: '16px', lineHeight: '24px', color: color.link }}>&#8226;</td>
      <td valign="top" style={{ padding: '0 0 8px', fontFamily: fonts.body, fontSize: '16px', lineHeight: '24px', color: color.ink }}>{children}</td>
    </tr>
  );
}

// ── Code ───────────────────────────────────────────────────────────────────────────────────────
/** Monospace block. For the style sheet and internal mail — customers rarely need code. */
export function CodeBlock({ children }: { children: string }) {
  return (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0} bgcolor={neutral.tint}
      style={{ backgroundColor: neutral.tint, borderRadius: '8px', margin: '0 0 16px' }}>
      <tbody><tr><td style={{ padding: '12px 16px', fontFamily: "Menlo, Consolas, 'Courier New', monospace", fontSize: '12px',
        lineHeight: '18px', color: color.ink, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{children}</td></tr></tbody>
    </table>
  );
}

// ── Merge fields ───────────────────────────────────────────────────────────────────────────────
/**
 * Writes `{{ name }}` into the output untouched, for the sender to fill — for TSX templates. (MDX
 * authors just type `{{ name }}`; the loader protects it.) Same syntax as Postmark's Mustachio and
 * Jinja, so one placeholder works with either sender.
 */
export function Merge({ name }: { name: string }) {
  return <>{`{{ ${name} }}`}</>;
}
