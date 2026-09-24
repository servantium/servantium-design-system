/**
 * @servantium/brand — the one place Servantium's identity lives: the logo, Astro the Astronaut,
 * the email header art, and the company facts (legal name, address, public links).
 *
 * TWO WAYS TO CONSUME IT, and which one depends on whether the consumer can bundle files:
 *
 *   BUNDLED  (website, help, portal, prototypes) — import from this package. A design-system
 *            release opens a PR in each consumer, exactly as it already does for Verdant tokens.
 *
 *   BY URL   (email, Firebase templates, OG images, decks, third-party listings) — reference the
 *            HOSTED copy via `assetUrl()`. These can't bundle anything; an email is HTML that
 *            loads its images from the internet every time it is opened. See README → Hosting.
 */
import company from '../company.json' with { type: 'json' };

export { company };

export type UrlKey = keyof typeof company.urls;

/** The postal address on one line, as it appears in an email footer. */
export const addressLine = (): string => {
  const a = company.address;
  return `${company.legalName} · ${a.line1}, ${a.city}, ${a.region} ${a.postalCode}`;
};

/** Footer links, resolved from their keys so a URL changes in exactly one place. */
export const footerLinks = (): { label: string; href: string }[] =>
  company.footerLinks.map((l) => ({ label: l.label, href: company.urls[l.url as UrlKey] }));

/**
 * The public origin that brand assets are served from. `null` until the hosting in the README is
 * set up — callers then fall back to a relative path, which is right for previews and wrong for a
 * real send. Kept as data, not a constant buried in a template, so it flips in one place.
 */
export const DEFAULT_ASSET_BASE: string | null = null;

/** Resolve a brand asset (e.g. `astro/astro-waving.png`) against a base URL or relative root. */
export const assetUrl = (path: string, base: string | null = DEFAULT_ASSET_BASE): string =>
  base ? `${base.replace(/\/$/, '')}/${path}` : `assets/${path}`;

/** Astro's poses, named as the files are. */
export const ASTRO_POSES = ['waving', 'captain', 'detective', 'professor', 'cowboy'] as const;
export type AstroPose = (typeof ASTRO_POSES)[number];
