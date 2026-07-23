/**
 * site-config.ts — shared source for cross-site chrome content (nav + footer).
 *
 * Lives in @servantium/grove so consumers get it via the design-system they
 * already install, instead of cloning another site's repo. Consumed by
 * servantium-help via `@servantium/grove/site-config`; adopted on the usual
 * design-system ref bump. (servantium-website still keeps a local copy while
 * it is pinned to an older grove; it converges here on its next grove upgrade.)
 *
 * Rules for this file:
 *   - Keep it dependency-free beyond type-only imports from grove. Plain data
 *     + helper functions only, no Astro components or React.
 *   - The `origin` param on the helpers lets a consumer absolute-link
 *     marketing URLs back to https://servantium.com (help sets it; the
 *     marketing site leaves it blank for relative URLs).
 */

import type { NavLink, NavCta } from '@servantium/grove/SiteNav';
import type { FooterColumn, FooterFounder } from '@servantium/grove/SiteFooter';

interface BuildOptions {
  /**
   * When set (e.g. "https://servantium.com"), marketing links are prefixed
   * with this origin. Help sets it so its nav links jump cross-site to the
   * marketing home. Website leaves it blank (relative URLs).
   */
  origin?: string;
}

const HELP_ORIGIN = 'https://help.servantium.com';

export function buildNavLinks({ origin = '' }: BuildOptions = {}): NavLink[] {
  return [
    { href: `${origin}/`, label: 'Home', id: 'home' },
    { href: `${origin}/platform/`, label: 'Platform', id: 'platform' },
    {
      href: `${origin}/resources/`,
      label: 'Resources',
      id: 'resources',
      dropdown: [
        {
          heading: 'Build',
          items: [
            { href: `${origin}/resources/templates/`, label: 'Templates', description: 'SOWs, dashboards, rate cards, and checklists', icon: 'template' },
            { href: `${origin}/resources/guides/`, label: 'Guides & Playbooks', description: 'Long-form field guides for services operators', icon: 'playbook' },
            { href: `${origin}/compare/`, label: 'Comparisons', description: 'How Servantium fits next to other categories', icon: 'comparison' },
          ],
        },
        {
          heading: 'Learn',
          items: [
            { href: `${origin}/blog/`, label: 'Blog', description: 'Strategy essays and operator op-eds', icon: 'blog' },
            { href: `${HELP_ORIGIN}/release-notes/`, label: 'Release Notes', description: 'What shipped, when, and why', icon: 'releases' },
          ],
        },
        {
          heading: 'Help',
          items: [
            { href: `${HELP_ORIGIN}/`, label: 'Help Center', description: 'Product documentation and support guides', icon: 'help' },
            { href: `${HELP_ORIGIN}/glossary/`, label: 'Glossary', description: 'Key terms and definitions for services leaders', icon: 'glossary' },
          ],
        },
      ],
      megaFooter: {
        label: 'The Resources Hub',
        description: 'Browse every template, playbook, and story in one place.',
        href: `${origin}/resources/`,
      },
    },
    { href: `${origin}/about`, label: 'About', id: 'about' },
  ];
}

export function buildFooterColumns({ origin = '' }: BuildOptions = {}): FooterColumn[] {
  return [
    {
      heading: 'Product',
      items: [
        { href: `${origin}/platform`, label: 'Platform' },
        { href: `${HELP_ORIGIN}/`, label: 'Help Center' },
        { href: `${HELP_ORIGIN}/release-notes/`, label: 'Release Notes' },
        { href: `${HELP_ORIGIN}/glossary/`, label: 'Glossary' },
      ],
    },
    {
      heading: 'Learn',
      items: [
        { href: `${origin}/blog/`, label: 'Blog' },
        { href: `${HELP_ORIGIN}/`, label: 'Guides' },
        { href: `${HELP_ORIGIN}/videos/`, label: 'Videos' },
      ],
    },
    {
      heading: 'Company',
      items: [
        { href: `${origin}/about`, label: 'About' },
        { href: `${origin}/#contact`, label: 'Contact' },
        { href: `${origin}/privacy`, label: 'Privacy' },
        { href: `${origin}/terms`, label: 'Terms' },
      ],
    },
  ];
}

export const brand = {
  name: 'Servantium',
  tagline: 'The Professional Services OS.',
  logoSrc: '/logo.png',
  logoAlt: 'Servantium',
  logoHref: 'https://servantium.com/',
};

export const contactEmail = 'hello@servantium.com';

export const social = {
  linkedin: 'https://www.linkedin.com/company/servantium',
};

export const founders: FooterFounder[] = [
  { name: 'Christopher Veale', href: 'https://www.linkedin.com/in/christopher-veale' },
  { name: 'Maxwell Friel', href: 'https://www.linkedin.com/in/maxwell-friel-2bb02b30' },
];

// Cal.com booking details — used by the "Book a Demo" CTA in the nav.
export const calBooking = {
  link: 'christopher-veale/servantium-introduction?duration=15',
  namespace: 'servantium-introduction',
  config: '{"layout":"month_view"}',
};

export function buildNavCtas(): NavCta[] {
  return [
    {
      kind: 'secondary',
      label: 'Book a Demo',
      calLink: calBooking.link,
      calNamespace: calBooking.namespace,
      calConfig: calBooking.config,
    },
    {
      kind: 'primary',
      label: 'Log In',
      href: 'https://app.servantium.com',
      rel: 'noopener',
    },
  ];
}

// UI strings (absorbed from the former src/data/strings.ts).
// Organized for future i18n swap.
export const strings = {
  nav: {
    bookDemo: 'Book a Demo',
    logIn: 'Log In',
  },
  footer: {
    tagline: brand.tagline,
  },
};
