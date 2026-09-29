/**
 * Banner — the forest night sky at the top of every email: logo, a label, and one line of headline.
 *
 * Frame, not content. A master sets it from its frontmatter — `label`, `title`, `tone` — and never
 * writes <Banner> itself.
 *
 * ── ONE BANNER (design decision, 2026-09-24) ──────────────────────────────────────────────────
 * The first cut had three sizes and six tones — eighteen combinations and a taxonomy to learn. Now
 * there is ONE banner. It takes one of three tones, which colour the dot beside the label and the
 * rule along its bottom edge; the sky itself never changes.
 *
 * ── ONE LINE (design decision, 2026-09-28) ────────────────────────────────────────────────────
 * The title is the same on every send ("Task update", not "Jules assigned you a task") and 24
 * characters at most, so it fits on one line at 600px and on a 375px phone, in Playfair or in its
 * Georgia fallback. The event's details go in the body. The build refuses longer titles, fields in
 * the title, and the old `subtitle`.
 *
 * ── THE MASCOT ────────────────────────────────────────────────────────────────────────────────
 * Off for now: no master sets `astro`. The banner keeps room for one. When it returns, it appears
 * only on good news that isn't urgent, and never on security, legal or frequent mail. The type
 * system and the component both refuse it on an attention or urgent email.
 *
 * ── OUTLOOK DESKTOP ───────────────────────────────────────────────────────────────────────────
 * Word's renderer ignores CSS background images, so Outlook desktop shows the banner as flat
 * forest — the `bgcolor` fallback. The text is designed to read on flat forest first.
 */
import type { AstroPose } from '@servantium/brand';
import { useAsset } from '../render';
import { color, fonts, tones, type Tone } from '../theme';

type BannerBase = {
  /** What kind of email this is, top-right: "Welcome", "Task", "Service status". 16 characters at most. */
  label: string;
  /** The headline: one line, 24 characters at most, the same on every send. Details go in the body. */
  title: string;
};

/** The mascot only type-checks alongside the default tone. */
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

  // ONE LINE, ALWAYS: 28px on desktop, 22px on a phone, and never more than 24 characters.
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
