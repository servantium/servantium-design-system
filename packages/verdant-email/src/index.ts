/**
 * @servantium/verdant-email — Verdant for email.
 *
 * Two ways to write an email, one output:
 *
 *   TSX   product emails whose words are fixed and whose data comes from the product.
 *         import { renderEmail, templates } from '@servantium/verdant-email';
 *         const { subject, preheader, body } = templates.welcome.build(props);
 *         const html = renderEmail({ subject, preheader, children: body });
 *
 *   MDX   emails a person writes — release notes, incident and maintenance notices, marketing.
 *         const email = await loadMdxEmail(readFileSync('src/emails/incident.mdx', 'utf8'));
 *         const html = renderEmail({ subject: email.subject, preheader: email.preheader, children: email.body });
 *
 * Either way the export turns them into Postmark templates. See README and dist/stylesheet.html.
 */
export { renderEmail, toFirebaseFragment, useAsset, type AssetOptions } from './render';
export { Email, Banner, Body, Footer, type BannerProps, type FooterProps } from './components/Layout';
export {
  Heading, Text, Eyebrow, Link, Button, DataTable, Callout, Chip, Items, Spacer, Divider, LinkFallback,
  List, ListItem, CodeBlock, Merge, type Tint,
} from './components/Content';
export { color, fonts, tones, neutral, type Tone } from './theme';
export { defineTemplate, type EmailTemplate, type Stream } from './template';
export {
  loadMdxEmail, mdxBody, validate, splitFrontmatter, protectMergeFields, fillPreview, mdxComponents,
  FrontmatterError, POSTMARK_UNSUBSCRIBE, type Frontmatter, type MdxEmail,
} from './mdx';
export { htmlToText } from './text';

import welcome from './templates/welcome';
import passwordReset from './templates/password-reset';
import taskNotification from './templates/task-notification';
import regulatoryNotice from './templates/regulatory-notice';

/** The TSX templates. MDX emails live in src/emails/ and are loaded with loadMdxEmail. */
export const templates = { welcome, passwordReset, taskNotification, regulatoryNotice } as const;
