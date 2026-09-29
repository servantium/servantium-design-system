/**
 * Footer — three lines under every email:
 *   1. the links: Help Center, Trust Center, Privacy, Terms (and Status once it's live);
 *   2. why they got it, and where to ask a question (plus Unsubscribe on broadcast mail);
 *   3. the company address, with LinkedIn beside it.
 *
 * Frame, not content. A master sets `footer.reason` (required) and `footer.settings` (optional) in
 * its frontmatter; the stream decides whether Unsubscribe appears. Links, address, help@ and
 * LinkedIn come from @servantium/brand's company.json — never typed here — so each changes in one
 * place for every email.
 */
import { addressLine, company, footerLinks, social } from '@servantium/brand';
import { useAsset } from '../render';
import { color, fonts } from '../theme';

export type FooterProps = {
  /** Why this person received this email, in one short sentence. Required on every email. */
  reason: string;
  /** Notification emails link to their settings. */
  settingsHref?: string;
  /** Broadcast mail ONLY. Transactional and legal mail must not offer it. */
  unsubscribeHref?: string;
};

export function Footer({ reason, settingsHref, unsubscribeHref }: FooterProps) {
  const { url } = useAsset();
  const small = { margin: '0 0 10px', fontFamily: fonts.body, fontSize: '12px', lineHeight: '18px', color: color.inkMuted };
  const a = { color: color.link, fontWeight: 600, textDecoration: 'underline' };
  const links = [
    ...(settingsHref ? [{ label: 'Notification settings', href: settingsHref }] : []),
    ...footerLinks(),
  ];
  return (
    <tr>
      <td className="ve-px" style={{ padding: '22px 40px 0' }}>
        <p style={{ ...small, fontSize: '13px', lineHeight: '20px', margin: '0 0 10px' }}>
          {links.map((l, i) => (
            <span key={l.href}>
              {i > 0 && <span style={{ color: color.rule }}>&nbsp;&nbsp;|&nbsp;&nbsp;</span>}
              <a href={l.href} style={a}>{l.label}</a>
            </span>
          ))}
        </p>
        <p style={small}>
          {reason} Questions? <a href={`mailto:${company.email.help}`} style={a}>{company.email.help}</a>
          {unsubscribeHref && <>&nbsp;·&nbsp;<a href={unsubscribeHref} style={a}>Unsubscribe</a></>}
        </p>
        <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0}>
          <tbody><tr>
            <td valign="middle" style={{ ...small, margin: 0 }}>{addressLine()}</td>
            <td valign="middle" align="right" width={36} style={{ paddingLeft: '12px' }}>
              <a href={social.linkedin} style={{ display: 'inline-block', lineHeight: 0 }}>
                <img src={url('social/linkedin.png')} width={24} height={24} alt="Servantium on LinkedIn"
                  style={{ display: 'block', width: '24px', height: '24px', border: '0' }} />
              </a>
            </td>
          </tr></tbody>
        </table>
      </td>
    </tr>
  );
}
