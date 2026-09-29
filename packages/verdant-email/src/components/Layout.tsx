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
import { addressLine, company, footerLinks, social, type AstroPose } from '@servantium/brand';
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
  /** What kind of email this is, top-right: "Welcome", "Task", "Service status". 16 characters at most. */
  label: string;
  /** The headline: one line, 24 characters at most, the same on every send. Details go in the body. */
  title: string;
};

/** Astro only type-checks alongside the default tone — see the header. */
export type BannerProps =
  | (BannerBase & { tone?: 'default'; astro?: AstroPose })
  | (BannerBase & { tone: Exclude<Tone, 'default'>; astro?: never });

export function Banner(props: BannerProps) {
  const { label, title } = props;
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
        {/* Labels are 16 characters at most, so they sit on one line beside the logo, even on a phone. */}
        <td className="ve-label" valign="middle" align="right" style={{ paddingLeft: '12px', fontFamily: fonts.body, fontSize: '11px',
          lineHeight: '16px', fontWeight: 700, letterSpacing: '1.6px', textTransform: 'uppercase', color: t.onBanner, whiteSpace: 'nowrap' }}>
          <span style={{ color: t.accent, fontSize: '10px' }}>&#9679;</span>&nbsp;&nbsp;{label}
        </td>
      </tr></tbody>
    </table>
  );

  // ONE LINE, ALWAYS: 28px on desktop, 22px on a phone, and never more than 24 characters (the build
  // refuses longer), so it fits a 600px email and a 375px phone in the web font or its Georgia fallback.
  const heading = (
    <h1 className="ve-title" style={{ margin: '24px 0 0', fontFamily: fonts.display, fontSize: '28px', lineHeight: '34px',
      fontWeight: 600, color: color.onBanner, whiteSpace: 'nowrap' }}>
      {title}
    </h1>
  );

  return (
    <>
      <tr>
        <td className="ve-px" bgcolor={color.banner} {...(art ? { background: bg } : {})}
          style={{ padding: '28px 40px 30px', backgroundColor: color.banner, borderRadius: '14px 14px 0 0',
            ...(art ? { backgroundImage: `url(${bg})`, backgroundPosition: 'right top', backgroundSize: 'cover', backgroundRepeat: 'no-repeat' } : {}) }}>
          {topRow}
          {astro ? (
            <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0}>
              <tbody><tr>
                <td valign="bottom">{heading}</td>
                <td className="ve-astro-cell" width={132} valign="bottom" align="right" style={{ paddingTop: '18px' }}>
                  <img className="ve-astro" src={url(`astro/astro-${astro}.png`)} width={120} height={120} alt=""
                    style={{ display: 'block', width: '120px', height: '120px', border: '0' }} />
                </td>
              </tr></tbody>
            </table>
          ) : heading}
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
/**
 * The white card, closed by THE BOOKEND: a thin strip of the banner's night sky along the bottom,
 * so every email opens and closes on the same brand art. With images off it's a plain forest bar.
 */
export function Body({ children }: { children: ReactNode }) {
  const { url, art } = useAsset();
  const bar = url('email/footer-bar.jpg');
  return (
    <>
      <tr>
        <td className="ve-px" bgcolor={color.surface} style={{ padding: '36px 40px 40px', backgroundColor: color.surface,
          border: `1px solid ${color.rule}`, borderTop: '0', borderBottom: '0' }}>
          {children}
        </td>
      </tr>
      <tr>
        <td height={12} bgcolor={color.banner} {...(art ? { background: bar } : {})}
          style={{ height: '12px', lineHeight: '12px', fontSize: '0', backgroundColor: color.banner, borderRadius: '0 0 14px 14px',
            ...(art ? { backgroundImage: `url(${bar})`, backgroundSize: 'cover', backgroundPosition: 'center', backgroundRepeat: 'no-repeat' } : {}) }}>&nbsp;</td>
      </tr>
    </>
  );
}

// ── Footer ─────────────────────────────────────────────────────────────────────────────────────
export type FooterProps = {
  /** Why this person received this email, in one short sentence. Required on every email. */
  reason: string;
  /** Notification emails link to their settings. */
  settingsHref?: string;
  /** Broadcast mail ONLY. Transactional and legal mail must not offer it. */
  unsubscribeHref?: string;
};

/**
 * Three lines, every email:
 *   1. the links (Help Center, Trust Center, Privacy, Terms — and Status once it's live);
 *   2. why they got it, and where to ask a question (plus Unsubscribe on broadcast mail);
 *   3. the company address, with LinkedIn beside it.
 * Links, address, help@ and LinkedIn come from @servantium/brand's company.json — never typed
 * here — so each changes in one place for every email.
 */
export function Footer({ reason, settingsHref, unsubscribeHref }: FooterProps) {
  const { url } = useAsset();
  const small = { margin: '0 0 10px', fontFamily: fonts.body, fontSize: '12px', lineHeight: '18px', color: color.inkMuted };
  const a = { color: color.link, fontWeight: 600, textDecoration: 'underline' };
  const links = [
    ...(settingsHref ? [{ label: 'Notification settings', href: settingsHref }] : []),
    ...footerLinks(),
  ];
  return (
    <tr>
      <td className="ve-px" style={{ padding: '22px 40px 0' }}>
        <p style={{ ...small, fontSize: '13px', lineHeight: '20px', margin: '0 0 10px' }}>
          {links.map((l, i) => (
            <span key={l.href}>
              {i > 0 && <span style={{ color: color.rule }}>&nbsp;&nbsp;|&nbsp;&nbsp;</span>}
              <a href={l.href} style={a}>{l.label}</a>
            </span>
          ))}
        </p>
        <p style={small}>
          {reason} Questions? <a href={`mailto:${company.email.help}`} style={a}>{company.email.help}</a>
          {unsubscribeHref && <>&nbsp;·&nbsp;<a href={unsubscribeHref} style={a}>Unsubscribe</a></>}
        </p>
        <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0}>
          <tbody><tr>
            <td valign="middle" style={{ ...small, margin: 0 }}>{addressLine()}</td>
            <td valign="middle" align="right" width={36} style={{ paddingLeft: '12px' }}>
              <a href={social.linkedin} style={{ display: 'inline-block', lineHeight: 0 }}>
                <img src={url('social/linkedin.png')} width={24} height={24} alt="Servantium on LinkedIn"
                  style={{ display: 'block', width: '24px', height: '24px', border: '0' }} />
              </a>
            </td>
          </tr></tbody>
        </table>
      </td>
    </tr>
  );
}
