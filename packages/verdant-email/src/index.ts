/**
 * @servantium/verdant-email — Verdant for email.
 *
 *   import { renderEmail, templates } from '@servantium/verdant-email';
 *   const t = templates.welcome;
 *   const { subject, preheader, body } = t.build({ ...props });
 *   const html = renderEmail({ subject, preheader, children: body, assets: { base: ASSET_BASE } });
 *
 * Or assemble a new email from the components — see README.
 */
export { renderEmail, toFirebaseFragment, useAsset, type AssetOptions } from './render';
export { Email, Banner, Body, Footer, type BannerProps, type BannerSize, type FooterProps } from './components/Layout';
export { Heading, Text, Eyebrow, Link, Button, DataTable, Callout, Chip, Items, Spacer, Divider, LinkFallback } from './components/Content';
export { color, fonts, tones, type Tone } from './theme';
export { defineTemplate, type EmailTemplate } from './template';

import welcome from './templates/welcome';
import passwordReset from './templates/password-reset';
import taskNotification from './templates/task-notification';
import regulatoryNotice from './templates/regulatory-notice';
import releaseNotes from './templates/release-notes';
import incident from './templates/incident';

export const templates = { welcome, passwordReset, taskNotification, regulatoryNotice, releaseNotes, incident } as const;
