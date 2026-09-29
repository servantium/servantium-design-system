/**
 * markdown — what plain Markdown in a master turns into. Each piece becomes an email-safe
 * component, so an author writes Markdown and never thinks about tables.
 *
 *   paragraph → Text      ## → Heading     - list → List      [a](url) → Link
 *   --- → Divider         ``` → CodeBlock  `code` → inline monospace
 */
import type { ReactNode } from 'react';
import { CodeBlock } from './CodeBlock';
import { Divider } from './Divider';
import { Heading } from './Heading';
import { Link } from './Link';
import { List, ListItem } from './List';
import { Text } from './Text';

type Kids = { children?: ReactNode };

const Pre = ({ children }: Kids) => {
  const code = (children as { props?: { children?: string } })?.props?.children ?? '';
  return <CodeBlock>{String(code).replace(/\n$/, '')}</CodeBlock>;
};

export const markdown = {
  p: ({ children }: Kids) => <Text>{children}</Text>,
  h1: ({ children }: Kids) => <Heading level={1}>{children}</Heading>,
  h2: ({ children }: Kids) => <Heading>{children}</Heading>,
  h3: ({ children }: Kids) => <Heading>{children}</Heading>,
  a: ({ href, children }: Kids & { href?: string }) => <Link href={href ?? '#'}>{children}</Link>,
  ul: ({ children }: Kids) => <List>{children}</List>,
  ol: ({ children }: Kids) => <List>{children}</List>,
  li: ({ children }: Kids) => <ListItem>{children}</ListItem>,
  hr: () => <Divider />,
  pre: Pre,
  code: ({ children }: Kids) => (
    <code style={{ fontFamily: "Menlo, Consolas, 'Courier New', monospace", fontSize: '13px', backgroundColor: '#F5F6F7', padding: '1px 4px', borderRadius: '4px' }}>{children}</code>
  ),
};
