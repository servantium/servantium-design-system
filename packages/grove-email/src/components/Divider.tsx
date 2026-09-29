/**
 * Divider — a hairline between two unrelated parts. Markdown `---` becomes one. Rarely needed:
 * a heading usually does the job.
 */
import { color } from '../theme';

export function Divider({ margin = '28px 0' }: { margin?: string }) {
  return (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0} style={{ margin }}>
      <tbody><tr><td height={1} style={{ height: '1px', lineHeight: '1px', fontSize: '0', borderTop: `1px solid ${color.rule}` }}>&nbsp;</td></tr></tbody>
    </table>
  );
}
