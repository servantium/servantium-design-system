/**
 * @servantium/verdant-email — Verdant for email.
 *
 * The masters are MDX files in src/emails/ — one per email, named for its Postmark template alias,
 * with the data it needs declared in its frontmatter. `npm run build` compiles them into Postmark
 * templates (dist/postmark/) and a field contract (dist/contract.json). Product code never
 * renders email: it sends a Postmark template by alias with the data. See README.
 */
export { renderEmail, toFirebaseFragment, useAsset, type AssetOptions } from './render';
export { Email, Banner, Body, Footer, type BannerProps, type FooterProps } from './components/Layout';
export {
  Heading, Text, Eyebrow, Link, Button, DataTable, Callout, Chip, Items, Spacer, Divider, LinkFallback,
  List, ListItem, CodeBlock, Merge, type Tint,
} from './components/Content';
export { color, fonts, tones, neutral, type Tone } from './theme';
export { type Stream } from './template';
export {
  loadMdxEmail, mdxBody, validate, splitFrontmatter, protectMergeFields, fillPreview, mdxComponents,
  checkFields, checkSections, usedFields, examples, If, Editable,
  FrontmatterError, POSTMARK_UNSUBSCRIBE, type Frontmatter, type Field, type MdxEmail,
} from './mdx';
export { htmlToText } from './text';
