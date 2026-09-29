/**
 * Button — the one action the email exists for.
 *
 *   <Button href="{{ task_url }}" width={180}>Open task</Button>
 *   <Button to="trust" variant="secondary" width={250}>View the trust center</Button>
 *
 *   primary    Servantium green with deep-forest text, which passes WCAG AA (white on this green
 *              does not). At most one per email; the tests count.
 *   secondary  An outline, for a second action, or for notices and incidents, where a filled
 *              green button reads as a sales pitch.
 *
 * Outlook desktop gets a VML shape (otherwise it draws a bare link); every other client gets a
 * padded link. `width` is for Outlook only — VML can't size itself to its label, so widen it for
 * a long label. Labels are a verb and an object, 24 characters at most.
 */
import { company, type UrlKey } from '@servantium/brand';
import { Raw } from '../render';
import { color, fonts } from '../theme';

const escAttr = (s: string) => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
const escText = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

export function Button({ href, to, children, variant = 'primary', width = 220 }: {
  /** Where it goes. Usually a field: href="{{ task_url }}". */
  href?: string;
  /** Or one of Servantium's own addresses from company.json, instead of href. */
  to?: UrlKey;
  children: string;
  variant?: 'primary' | 'secondary';
  /** Outlook's width in px. 220 fits most labels; widen it for long ones. */
  width?: number;
}) {
  const primary = variant === 'primary';
  const fill = primary ? color.brand : color.surface;
  const fg = color.banner;
  const border = primary ? color.brand : color.banner;
  const stroke = primary ? 'stroke="f"' : `strokecolor="${border}" strokeweight="1.5px"`;
  const h = escAttr(to ? company.urls[to] : (href ?? '#'));
  const label = escText(children);
  const html =
    `<!--[if mso]><v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="${h}" style="height:48px;v-text-anchor:middle;width:${width}px;" arcsize="17%" ${stroke} fillcolor="${fill}"><w:anchorlock/><center style="color:${fg};font-family:Arial,sans-serif;font-size:16px;font-weight:bold;">${label}</center></v:roundrect><![endif]-->` +
    `<!--[if !mso]><!--><a href="${h}" style="display:inline-block;padding:13px 28px;font-family:${escAttr(fonts.body)};font-size:16px;line-height:22px;font-weight:700;color:${fg};text-decoration:none;border-radius:8px;border:1.5px solid ${border};background-color:${fill};">${label}</a><!--<![endif]-->`;
  return (
    <table role="presentation" className="ve-btn" cellPadding={0} cellSpacing={0} border={0}>
      <tbody><tr><td align="center" bgcolor={fill} style={{ borderRadius: '8px' }}><Raw html={html} /></td></tr></tbody>
    </table>
  );
}
