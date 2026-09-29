/**
 * @servantium/grove-email — Grove for email: components on Verdant tokens, and the emails built from them.
 *
 * The masters are MDX files in src/emails/ — one per email, named for its Postmark template alias,
 * with the data it needs declared in its frontmatter. `npm run build` compiles them into Postmark
 * templates (dist/postmark/) and a field contract (dist/contract.json). Product code never
 * renders email: it sends a Postmark template by alias with the data. See README.
 */
export { renderEmail, toFirebaseFragment, useAsset, type AssetOptions } from './render';
export {
  Email, Banner, Body, Footer, Heading, Text, Eyebrow, Link, CompanyLink, Button, DataTable, Callout, Chip, Items,
  Spacer, Divider, LinkFallback, List, ListItem, CodeBlock, Updates, Steps, Paragraphs, Thread, If, Editable,
  mdxComponents, type BannerProps, type FooterProps,
} from './components';
export { color, fonts, tones, neutral, tint, type Tone, type Tint } from './theme';
export { type Stream } from './template';
export {
  loadMdxEmail, mdxBody, validate, splitFrontmatter, protectMergeFields, fillPreview,
  checkContract, compileMdxEmail, isList, examples,
  FrontmatterError, POSTMARK_UNSUBSCRIBE, type Frontmatter, type Field, type Item, type Values, type MdxEmail,
} from './mdx';
export { htmlToText } from './text';
