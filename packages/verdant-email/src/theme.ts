/**
 * theme — Verdant's tokens, mapped to the roles an email needs.
 *
 * Every literal colour here comes from tokens.generated.ts (Verdant) EXCEPT the few marked DERIVED,
 * which exist because email needs a light tint or a dark text shade that the web palette never had
 * to name. No contrast figures are written in comments — they rot. test/rules.test.tsx computes
 * every text pairing and fails below WCAG AA (4.5:1).
 */
import { verdant as v } from './tokens.generated';

/** Fallback stacks. Web fonts load in Apple Mail and iOS; Gmail and Outlook never load them, so
 *  the tail of each stack is what most recipients actually see. */
export const fonts = {
  display: `${v.fontDisplay.replace(/,\s*serif$/, '')}, 'Times New Roman', serif`,
  body: `${v.fontBody.replace(/,\s*sans-serif$/, '')}, 'Segoe UI', Helvetica, Arial, sans-serif`,
} as const;

export const color = {
  brand: v.colorGreen,            // #00C26D — primary button (founder ruling: white text)
  link: v.colorEmerald,           // #037A47 — body links are this, not brand (brand fails AA as text)
  banner: v.colorDeepForest,      // #023E25 — the header, and its fallback when images are off
  ink: v.colorInk1,               // #1a1a1a
  inkMuted: v.colorInk3,          // #6b6b6b — the smallest text we set
  onBanner: '#FFFFFF',
  onBannerMuted: '#CFEFDD',       // DERIVED — secondary text on the forest banner
  canvas: v.colorMistGrey,        // #F5F6F7
  surface: v.colorWhite,
  panel: v.colorMist2,            // #FAFAFB — the grey data-table panel
  rule: v.colorCloudGrey,         // #E1E3E6
} as const;

/**
 * TONES — how an email says what KIND of email it is without changing the banner.
 *
 * The banner is always the forest sky: that is the brand, and it never changes. A tone adds three
 * small things: the rule along the banner's bottom edge, the dot and label in its corner, and the
 * tint of any callout in the body. Enough to tell an outage from a release note at a glance; not
 * enough to make them look like two companies.
 */
export type Tone = 'brand' | 'activity' | 'product' | 'warning' | 'critical' | 'notice';

export const tones: Record<Tone, {
  label: string;
  /** The banner's bottom rule and the corner dot. */
  accent: string;
  /** The corner label, legible on forest. */
  onBanner: string;
  /** Callout background in the body. */
  tint: string;
  /** Callout title — dark enough to pass AA on the tint. */
  strong: string;
}> = {
  brand:    { label: 'Account',  accent: v.colorGreen,     onBanner: v.colorJade,  tint: v.colorSoftMint,  strong: v.colorEmerald },
  activity: { label: 'Activity', accent: v.colorSlateBlue, onBanner: '#A9C8DE' /* DERIVED */, tint: v.colorNoteBg, strong: '#2F5F80' /* DERIVED */ },
  product:  { label: 'Product',  accent: v.colorDeepTeal,  onBanner: '#8FE3D8' /* DERIVED */, tint: '#EAF7F5' /* DERIVED */, strong: '#16706A' /* DERIVED */ },
  // Verdant's --color-warning-text-dark (#B87A00) on --color-warning-bg is 3.4:1 and fails AA, so
  // email uses a darker amber. The same pair fails on the website; FLAGGED to Verdant.
  warning:  { label: 'Heads up', accent: v.colorAmber,     onBanner: '#FFD37A' /* DERIVED */, tint: v.colorWarningBg, strong: '#855500' /* DERIVED */ },
  critical: { label: 'Alert',    accent: v.colorCoral,     onBanner: '#FF9DA9' /* DERIVED */, tint: v.colorDangerBg, strong: '#B42336' /* DERIVED */ },
  notice:   { label: 'Notice',   accent: v.colorSlate,     onBanner: '#C3CCD8' /* DERIVED */, tint: v.colorMistGrey, strong: v.colorInk1 },
};
