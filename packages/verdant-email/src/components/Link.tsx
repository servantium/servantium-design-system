/**
 * Link — an underlined emerald link. Markdown links become one.
 *
 *   [View the full project plan]({{ plan_url }})
 *
 *   <Link href="{{ . }}">View the full project plan</Link>
 *
 * Link text says where it goes. Never "here" or "click here".
 */
import type { ReactNode } from 'react';
import { color } from '../theme';

export function Link({ href, children }: { href: string; children: ReactNode }) {
  return <a href={href} style={{ color: color.link, fontWeight: 600, textDecoration: 'underline' }}>{children}</a>;
}
