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
  brand: v.colorGreen,            // #00C26D — the primary button's fill (its label is deep forest: white on this green fails AA)
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
 * TONES — three, named by what they MEAN, not by topic (design decision, 2026-09-24): easier to
 * choose between, and colours that work on the banner.
 *
 * The first cut had six topic tones (account, activity, product, warning, critical, notice). Two of
 * them — slate-blue and slate — sat below the 3:1 minimum for a visible mark against the forest
 * banner, which is most of why "the colors" didn't work. And choosing between six topics meant
 * knowing the taxonomy. Three meanings needs no taxonomy — ask one question:
 *
 *   Is something wrong?   no → default   ·   needs action soon → attention   ·   broken → urgent
 *
 * The banner itself never changes. A tone colours the rule along the banner's bottom edge, the dot
 * beside its label, and any callout in the body.
 */
export type Tone = 'default' | 'attention' | 'urgent';

export const tones: Record<Tone, {
  /** The banner's bottom rule and the corner dot — a visible mark, ≥3:1 on forest. */
  accent: string;
  /** The corner label, legible on forest. */
  onBanner: string;
  /** Callout background in the body. */
  tint: string;
  /** Callout title — AA on the tint. */
  strong: string;
}> = {
  default:   { accent: v.colorGreen, onBanner: v.colorJade,             tint: v.colorSoftMint,  strong: v.colorEmerald },
  // Verdant's --color-warning-text-dark (#B87A00) on --color-warning-bg is 3.4:1 and fails AA, so
  // email uses a darker amber. The same pair fails on the website; FLAGGED to Verdant.
  attention: { accent: v.colorAmber, onBanner: '#FFD37A' /* DERIVED */, tint: v.colorWarningBg, strong: '#855500' /* DERIVED */ },
  urgent:    { accent: v.colorCoral, onBanner: '#FF9DA9' /* DERIVED */, tint: v.colorDangerBg,  strong: '#B42336' /* DERIVED */ },
};

/** A neutral panel for things that aren't a callout — a quoted note, a code sample. */
export const neutral = { tint: v.colorMistGrey, strong: v.colorInk1 } as const;

/** What a Callout or Chip can be coloured with: a tone, or `neutral` for a panel that isn't news. */
export type Tint = Tone | 'neutral';
export const tint = (t: Tint) => (t === 'neutral' ? neutral : tones[t]);
