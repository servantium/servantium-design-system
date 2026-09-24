/**
 * Layout — the frame every Servantium email shares: Email → Banner → Body → Footer.
 *
 * ── ONE BANNER FOR EVERY EMAIL (founder, 2026-09-24) ──────────────────────────────────────────
 *   > "I want a consistent email header/banner that we can reuse for any type of email… release
 *   > notes, outages, marketing, etc. I like the dark green best… a bit of flare to it."
 *
 * The banner is the forest night sky in every email: the logo top-left, a dot and a label
 * top-right. What varies is only its SIZE (how often the email is sent) and its TONE (what kind of
 * email it is). Size and tone are the only two decisions a template makes about its header.
 *
 *   compact   notifications and anything frequent — a hero on every task would be noise
 *   standard  one headline; security, notices, one-off transactional mail
 *   hero      headline, tagline and Astro; welcome, release notes, marketing
 *
 * ── OUTLOOK DESKTOP ───────────────────────────────────────────────────────────────────────────
 * Word's renderer ignores CSS background images, so Outlook desktop shows the banner as flat
 * forest — the `bgcolor` fallback. That is a deliberate floor, not a bug: the text was written to
 * read on flat forest first and on the sky second.
 */
import type { ReactNode } from 'react';
import { addressLine, footerLinks, type AstroPose } from '@servantium/brand';
import { useAsset } from '../render';
import { color, fonts, tones, type Tone } from '../theme';

const ART_SIZE = { compact: 'header-compact.jpg', standard: 'header-standard.jpg', hero: 'header-hero.jpg' } as const;
export type BannerSize = keyof typeof ART_SIZE;

// ── Email ──────────────────────────────────────────────────────────────────────────────────────
/** The 600px column. `width="600"` is for Outlook; the inline width lets everything else flex. */
export function Email({ children }: { children: ReactNode }) {
  return (
    <table role="presentation" className="ve-container" width="600" cellPadding={0} cellSpacing={0} border={0}
      style={{ width: '100%', maxWidth: '600px' }}>
      <tbody>{children}</tbody>
    </table>
  );
}

// ── Banner ─────────────────────────────────────────────────────────────────────────────────────
export type BannerProps = {
  tone?: Tone;
  size?: BannerSize;
  /** Top-right label. Defaults to the tone's own label ("Account", "Alert"…). */
  label?: string;
  /** Serif headline — standard and hero only. */
  title?: string;
  /** One line under the title — hero only. */
  subtitle?: string;
  /** Astro, beside the title — hero only. */
  astro?: AstroPose;
};

export function Banner({ tone = 'brand', size = 'standard', label, title, subtitle, astro }: BannerProps) {
  const { url, art } = useAsset();
  const t = tones[tone];
  const bg = url(`email/${ART_SIZE[size]}`);
  const pad = size === 'compact' ? '22px 40px' : size === 'hero' ? '28px 40px 34px' : '28px 40px 32px';

  const topRow = (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0}>
      <tbody><tr>
        <td valign="middle">
          <img src={url('logo/servantium-logo-white.png')} width={132} height={31} alt="Servantium"
            style={{ display: 'block', width: '132px', height: '31px', border: '0', outline: 'none',
              fontFamily: fonts.body, fontSize: '20px', fontWeight: 700, color: color.onBanner }} />
        </td>
        <td valign="middle" align="right" style={{ fontFamily: fonts.body, fontSize: '11px', lineHeight: '16px',
          fontWeight: 700, letterSpacing: '1.6px', textTransform: 'uppercase', color: t.onBanner, whiteSpace: 'nowrap' }}>
          <span style={{ color: t.accent, fontSize: '10px' }}>&#9679;</span>&nbsp;&nbsp;{label ?? t.label}
        </td>
      </tr></tbody>
    </table>
  );

  const heading = title && (
    <h1 className={size === 'hero' ? 've-hero-title' : 've-title'} style={{ margin: size === 'hero' ? '30px 0 0' : '26px 0 0',
      fontFamily: fonts.display, fontSize: size === 'hero' ? '34px' : '30px', lineHeight: size === 'hero' ? '42px' : '38px',
      fontWeight: 600, color: color.onBanner }}>{title}</h1>
  );
  const sub = subtitle && (
    <p style={{ margin: '10px 0 0', fontFamily: fonts.body, fontSize: '16px', lineHeight: '24px', color: color.onBannerMuted }}>
      {subtitle}
    </p>
  );

  const content = size === 'hero' && astro ? (
    <>
      {topRow}
      <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0}>
        <tbody><tr>
          <td valign="bottom">{heading}{sub}</td>
          <td className="ve-astro-cell" width={132} valign="bottom" align="right" style={{ paddingTop: '18px' }}>
            <img className="ve-astro" src={url(`astro/astro-${astro}.png`)} width={120} height={120} alt=""
              style={{ display: 'block', width: '120px', height: '120px', border: '0' }} />
          </td>
        </tr></tbody>
      </table>
    </>
  ) : (
    <>{topRow}{size !== 'compact' && heading}{size !== 'compact' && sub}</>
  );

  return (
    <>
      <tr>
        <td className="ve-px" bgcolor={color.banner} {...(art ? { background: bg } : {})}
          style={{ padding: pad, backgroundColor: color.banner, borderRadius: '14px 14px 0 0',
            ...(art ? { backgroundImage: `url(${bg})`, backgroundPosition: 'right top', backgroundSize: 'cover', backgroundRepeat: 'no-repeat' } : {}) }}>
          {content}
        </td>
      </tr>
      {/* THE TONE RULE — the only place the type colour runs full width. A table row, so it
          survives Outlook, image blocking and forced dark mode alike. */}
      <tr>
        <td height={4} bgcolor={t.accent} style={{ height: '4px', lineHeight: '4px', fontSize: '0', backgroundColor: t.accent }}>&nbsp;</td>
      </tr>
    </>
  );
}

// ── Body ───────────────────────────────────────────────────────────────────────────────────────
export function Body({ children }: { children: ReactNode }) {
  return (
    <tr>
      <td className="ve-px" bgcolor={color.surface} style={{ padding: '36px 40px 40px', backgroundColor: color.surface,
        border: `1px solid ${color.rule}`, borderTop: '0', borderRadius: '0 0 14px 14px' }}>
        {children}
      </td>
    </tr>
  );
}

// ── Footer ─────────────────────────────────────────────────────────────────────────────────────
export type FooterProps = {
  /** Why this person received this email. Required: every email must be able to answer it. */
  reason: string;
  /** Notification emails link to their settings. */
  settingsHref?: string;
  /** Marketing ONLY. Transactional and legal mail must not offer it — see README. */
  unsubscribeHref?: string;
};

/**
 * Links and address come from @servantium/brand's company.json — never typed here. Move the help
 * centre and every template follows on the next release.
 */
export function Footer({ reason, settingsHref, unsubscribeHref }: FooterProps) {
  const small = { margin: '0 0 8px', fontFamily: fonts.body, fontSize: '12px', lineHeight: '18px', color: color.inkMuted };
  const a = { color: color.link, fontWeight: 600, textDecoration: 'underline' };
  const links = [
    ...(settingsHref ? [{ label: 'Notification settings', href: settingsHref }] : []),
    ...footerLinks(),
  ];
  return (
    <tr>
      <td className="ve-px" style={{ padding: '24px 40px 0' }}>
        <p style={{ ...small, fontSize: '13px', lineHeight: '20px', margin: '0 0 12px' }}>
          {links.map((l, i) => (
            <span key={l.href}>
              {i > 0 && <span style={{ color: color.rule }}>&nbsp;&nbsp;|&nbsp;&nbsp;</span>}
              <a href={l.href} style={a}>{l.label}</a>
            </span>
          ))}
        </p>
        <p style={small}>{reason}</p>
        {unsubscribeHref && (
          <p style={small}><a href={unsubscribeHref} style={a}>Unsubscribe</a> from these emails.</p>
        )}
        <p style={{ ...small, margin: '0' }}>{addressLine()}</p>
      </td>
    </tr>
  );
}
