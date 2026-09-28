/**
 * Layout — the frame every Servantium email shares: Email → Banner → Body → Footer.
 *
 * ── ONE BANNER (design decision, 2026-09-24) ──────────────────────────────────────────────────
 * The first cut had three sizes and six tones — eighteen combinations and a taxonomy to learn. Now
 * there is ONE banner: the forest night sky, the logo, a dot and a label, and a headline. It takes
 * one of three tones and, sometimes, Astro. Every email has a headline in the banner, so the body
 * always starts with content rather than with a second title.
 *
 * ── WHEN ASTRO APPEARS ────────────────────────────────────────────────────────────────────────
 * Astro appears when the email is GOOD NEWS and NOT URGENT: a welcome, a milestone, a product
 * announcement, marketing. He never appears on:
 *   · security mail — a reset or sign-in alert is the email most often forged; plain is safer
 *   · attention or urgent mail — a smiling mascot on an outage reads as not taking it seriously
 *   · legal, billing or money — formality is the point
 *   · frequent notifications — novelty on every task becomes noise
 * The first rule is enforced here in code: `astro` only type-checks with the default tone, and the
 * component throws if it's forced. The rest is judgement, written down in the style sheet.
 *
 * ── OUTLOOK DESKTOP ───────────────────────────────────────────────────────────────────────────
 * Word's renderer ignores CSS background images, so Outlook desktop shows the banner as flat
 * forest — the `bgcolor` fallback. The text is designed to read on flat forest first.
 */
import type { ReactNode } from 'react';
import { addressLine, company, footerLinks, type AstroPose } from '@servantium/brand';
import { useAsset } from '../render';
import { color, fonts, tones, type Tone } from '../theme';

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
type BannerBase = {
  /** What kind of email this is, top-right: "Welcome", "Task", "Service alert". */
  label: string;
  /** The headline. Every email has one. */
  title: string;
  /** One line under the headline. Optional. */
  subtitle?: string;
};

/** Astro only type-checks alongside the default tone — see the header. */
export type BannerProps =
  | (BannerBase & { tone?: 'default'; astro?: AstroPose })
  | (BannerBase & { tone: Exclude<Tone, 'default'>; astro?: never });

export function Banner(props: BannerProps) {
  const { label, title, subtitle } = props;
  const tone: Tone = props.tone ?? 'default';
  const astro = props.astro;
  if (astro && tone !== 'default') {
    throw new Error(`Astro can't appear on a "${tone}" email. He's for good news only — see the style sheet.`);
  }
  const { url, art } = useAsset();
  const t = tones[tone];
  const bg = url(astro ? 'email/header-hero.jpg' : 'email/header-standard.jpg');

  const topRow = (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0}>
      <tbody><tr>
        <td valign="middle">
          <img src={url('logo/servantium-logo-white.png')} width={132} height={31} alt="Servantium"
            style={{ display: 'block', width: '132px', height: '31px', border: '0', outline: 'none',
              fontFamily: fonts.body, fontSize: '20px', fontWeight: 700, color: color.onBanner }} />
        </td>
        {/* Not nowrap: a long label ("Scheduled maintenance") must wrap on a phone rather than push
            the banner wider than the screen. */}
        <td className="ve-label" valign="middle" align="right" style={{ paddingLeft: '12px', fontFamily: fonts.body, fontSize: '11px',
          lineHeight: '16px', fontWeight: 700, letterSpacing: '1.6px', textTransform: 'uppercase', color: t.onBanner }}>
          <span style={{ color: t.accent, fontSize: '10px' }}>&#9679;</span>&nbsp;&nbsp;{label}
        </td>
      </tr></tbody>
    </table>
  );

  const heading = (
    <h1 className={astro ? 've-hero-title' : 've-title'} style={{ margin: '26px 0 0', fontFamily: fonts.display,
      fontSize: astro ? '34px' : '30px', lineHeight: astro ? '42px' : '38px', fontWeight: 600, color: color.onBanner }}>
      {title}
    </h1>
  );
  const sub = subtitle && (
    <p style={{ margin: '10px 0 0', fontFamily: fonts.body, fontSize: '16px', lineHeight: '24px', color: color.onBannerMuted }}>
      {subtitle}
    </p>
  );

  return (
    <>
      <tr>
        <td className="ve-px" bgcolor={color.banner} {...(art ? { background: bg } : {})}
          style={{ padding: '28px 40px 32px', backgroundColor: color.banner, borderRadius: '14px 14px 0 0',
            ...(art ? { backgroundImage: `url(${bg})`, backgroundPosition: 'right top', backgroundSize: 'cover', backgroundRepeat: 'no-repeat' } : {}) }}>
          {topRow}
          {astro ? (
            <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0}>
              <tbody><tr>
                <td valign="bottom">{heading}{sub}</td>
                <td className="ve-astro-cell" width={132} valign="bottom" align="right" style={{ paddingTop: '18px' }}>
                  <img className="ve-astro" src={url(`astro/astro-${astro}.png`)} width={120} height={120} alt=""
                    style={{ display: 'block', width: '120px', height: '120px', border: '0' }} />
                </td>
              </tr></tbody>
            </table>
          ) : (<>{heading}{sub}</>)}
        </td>
      </tr>
      {/* THE TONE RULE — the only place the tone runs full width. A table row, so it survives
          Outlook, image blocking and forced dark mode alike. */}
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
        <p style={small}>Questions? Reply to this email or write to <a href={`mailto:${company.email.help}`} style={a}>{company.email.help}</a>.</p>
        {unsubscribeHref && (
          <p style={small}><a href={unsubscribeHref} style={a}>Unsubscribe</a> from these emails.</p>
        )}
        <p style={{ ...small, margin: '0' }}>{addressLine()}</p>
      </td>
    </tr>
  );
}
