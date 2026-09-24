/**
 * Password reset — sent by FIREBASE, not by us.
 *
 * It is Firebase's built-in template (console → Authentication → Templates → Password reset). The
 * export writes `firebase/password-reset.html`: paste it into that template's message box. Firebase
 * fills `%EMAIL%` and `%LINK%` itself and exposes nothing else, which is why there is no "requested
 * from Chrome on macOS" line — Firebase does not give its templates the request details.
 *
 * The plainest email in the set, and no Astro. A reset is the email most often forged: the fewer
 * decorative elements it carries, the easier a real one is to tell from a fake.
 */
import { company } from '@servantium/brand';
import { Banner, Body, Email, Footer } from '../components/Layout';
import { Button, Callout, Link, LinkFallback, Spacer, Text } from '../components/Content';
import { defineTemplate } from '../template';

type Props = { email: string; resetUrl: string };

export const firebasePlaceholders: Props = { email: '%EMAIL%', resetUrl: '%LINK%' };

export default defineTemplate<Props>({
  id: 'password-reset',
  name: 'Password reset',
  tone: 'default',
  stream: 'transactional',
  sendsVia: 'Firebase today (paste firebase/password-reset.html). Better: Postmark template `password-reset` — see README',
  sample: {
    email: 'jules.hart@halcyon.example',
    resetUrl: `${company.urls.app}/__/auth/action?mode=resetPassword&oobCode=Rt5nW2qZc8LmK3vP9xYh`,
  },
  placeholders: { email: '{{ email }}', resetUrl: '{{ reset_url }}' },
  build: (p) => ({
    subject: 'Reset your Servantium password',
    preheader: "This link expires in 1 hour. If you didn't ask for it, you can ignore this email.",
    body: (
      <Email>
        <Banner label="Security" title="Reset your password." />
        <Body>
          <Text>Hello,</Text>
          <Text margin="0 0 24px">We received a request to reset the password for the Servantium account <b>{p.email}</b>.</Text>
          <Button href={p.resetUrl} width={250}>Choose a new password</Button>
          <Spacer size={12} />
          <Text size="xs" muted margin="0 0 28px">For your security, this link expires in 1 hour and works once.</Text>
          <Callout title="Didn't request this?">
            You can safely ignore this email. Your password won't change unless you use the link above. If you keep
            receiving these, contact your workspace administrator.
          </Callout>
          <Spacer size={24} />
          <Text margin="0 0 28px">
            Once you've chosen a new password, sign in at <Link href={company.urls.app}>app.servantium.com</Link>.
          </Text>
          <LinkFallback href={p.resetUrl} />
        </Body>
        <Footer reason="You received this because someone asked to reset the password for this address on Servantium." />
      </Email>
    ),
  }),
});
