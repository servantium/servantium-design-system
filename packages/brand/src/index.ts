/**
 * @servantium/brand — the one place Servantium's identity lives: logos, the mascot, the email
 * art, icons, and the company facts (legal name, address, public links).
 *
 * TWO WAYS TO CONSUME IT, and which one depends on whether the consumer can bundle files:
 *
 *   BUNDLED  (website, help, portal, prototypes) — import from this package.
 *
 *   BY URL   (email, Firebase templates, decks, OG images, third-party listings) — use the hosted
 *            copy via `hostedUrl()`. Every hosted file has a permanent, fingerprinted address at
 *            assets.servantium.com; see docs/asset-library.md.
 */
import company from '../company.json' with { type: 'json' };
import manifest from '../assets.manifest.json' with { type: 'json' };

export { company };

export type UrlKey = keyof typeof company.urls;

/** The postal address on one line, as it appears in an email footer. */
export const addressLine = (): string => {
  const a = company.address;
  return `${company.legalName} · ${a.line1}, ${a.city}, ${a.region} ${a.postalCode}`;
};

/**
 * Footer links, resolved from their keys so a URL changes in exactly one place. A link marked
 * `live: false` (the status page, until it exists) is left out everywhere until someone flips it.
 */
export const footerLinks = (): { label: string; href: string }[] =>
  company.footerLinks
    .filter((l) => (l as { live?: boolean }).live !== false)
    .map((l) => ({ label: l.label, href: company.urls[l.url as UrlKey] }));

/** Where we are on social media. One place, so a handle change reaches every footer. */
export const social = company.social;

/** Where the library is served from. */
export const ASSET_ORIGIN = manifest.origin;

export type AssetPath = keyof typeof manifest.assets;

/**
 * The permanent public address of an asset, e.g. `logo/servantium-logo-white.png` →
 * `https://assets.servantium.com/logo/servantium-logo-white.3f9a2c1e04.png`. The fingerprint
 * changes whenever the file does, so anything already sent keeps the version it was sent with.
 */
export function hostedUrl(path: string): string {
  const a = (manifest.assets as Record<string, { key: string }>)[path];
  if (!a) throw new Error(`${path} isn't in the asset library — add it under packages/brand/assets and run \`npm run manifest\``);
  return `${manifest.origin}/${a.key}`;
}

/** An asset relative to a local copy of `assets/` — for previews, never for anything sent. */
export const localAssetPath = (path: string): string => `assets/${path}`;

/** Astro's poses, named as the files in assets/astro are. The website's Astronaut component is the original. */
export const ASTRO_POSES = [
  'floating', 'peeking', 'waving', 'searching', 'cowboy', 'detective', 'chef', 'captain', 'professor', 'accountant', 'controller', 'explorer',
] as const;
export type AstroPose = (typeof ASTRO_POSES)[number];
