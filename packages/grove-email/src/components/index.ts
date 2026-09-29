/**
 * The email components — one file each. docs/components.md is the reference; the style guide
 * (dist/stylesheet.html) shows every one rendered.
 *
 *   Frame      Email · Banner · Body · Footer         placed by the MDX loader from the frontmatter
 *   Writing    Text · Heading · Eyebrow · Link · CompanyLink · List · Divider · CodeBlock
 *   Actions    Button · LinkFallback
 *   Data       DataTable · Items · Steps · Chip
 *   Emphasis   Callout · Spacer
 *   Lists the sender fills    Updates · Paragraphs · Thread
 *   Postmark logic            If · Editable
 */
import { Button } from './Button';
import { Callout } from './Callout';
import { Chip } from './Chip';
import { CodeBlock } from './CodeBlock';
import { CompanyLink } from './CompanyLink';
import { DataTable } from './DataTable';
import { Divider } from './Divider';
import { Editable } from './Editable';
import { Eyebrow } from './Eyebrow';
import { Heading } from './Heading';
import { If } from './If';
import { Items } from './Items';
import { Link } from './Link';
import { LinkFallback } from './LinkFallback';
import { markdown } from './markdown';
import { Paragraphs } from './Paragraphs';
import { Spacer } from './Spacer';
import { Steps } from './Steps';
import { Text } from './Text';
import { Thread } from './Thread';
import { Updates } from './Updates';

export { Email } from './Email';
export { Banner, type BannerProps } from './Banner';
export { Body } from './Body';
export { Footer, type FooterProps } from './Footer';
export { List, ListItem } from './List';
export {
  Button, Callout, Chip, CodeBlock, CompanyLink, DataTable, Divider, Editable, Eyebrow, Heading, If, Items, Link,
  LinkFallback, markdown, Paragraphs, Spacer, Steps, Text, Thread, Updates,
};

/**
 * Every component a master may use, by the name it's written with. Adding a component here makes
 * it available in MDX; the docs test then insists it's documented.
 */
export const mdxComponents = {
  ...markdown,
  Button, Callout, Chip, CodeBlock, CompanyLink, DataTable, Divider, Editable, Eyebrow, Heading, If, Items, Link,
  LinkFallback, Paragraphs, Spacer, Steps, Text, Thread, Updates,
};
