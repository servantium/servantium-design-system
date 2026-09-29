/**
 * LinkFallback — the button's URL printed in full, under any button whose link carries a one-time
 * code (a reset, an invitation). Some clients mangle buttons; a pasted link always works.
 *
 *   <LinkFallback href="{{ set_password_url }}" />
 */
import { color } from '../theme';
import { Text } from './Text';

export function LinkFallback({ href }: { href: string }) {
  return (
    <Text size="xs" muted margin="0">
      Button not working? Paste this link into your browser:<br />
      <a href={href} style={{ color: color.link, textDecoration: 'underline', wordBreak: 'break-all' }}>{href}</a>
    </Text>
  );
}
