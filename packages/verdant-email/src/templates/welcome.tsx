/**
 * Welcome — also the INVITATION, and it has to be.
 *
 * `createUserCallable` (Servantium-Triggers functions/users/common.py) creates the account with no
 * password and sends nothing, so a person an admin adds has no way in. This email is that way in:
 * it carries the set-password link (Admin SDK `generate_password_reset_link`). A welcome without it
 * would greet someone at a locked door.
 */
import { company } from '@servantium/brand';
import { Banner, Body, Email, Footer } from '../components/Layout';
import { Button, DataTable, Heading, Items, Link, LinkFallback, Spacer, Text } from '../components/Content';
import { defineTemplate } from '../template';

type Props = {
  firstName: string;
  inviterName: string;
  workspaceName: string;
  email: string;
  setPasswordUrl: string;
  /** "72 hours" — how long the set-password link lives. */
  expiresIn: string;
};

export default defineTemplate<Props>({
  id: 'welcome',
  name: 'Welcome / invitation',
  tone: 'brand',
  size: 'hero',
  sendsVia: 'A sender — Resend in the portal, or the triggers via the Jinja export',
  sample: {
    firstName: 'Jules',
    inviterName: 'Dana Whitfield',
    workspaceName: 'Halcyon Bioanalytical Services',
    email: 'jules.hart@halcyon.example',
    setPasswordUrl: `${company.urls.app}/__/auth/action?mode=resetPassword&oobCode=Xk2pQ9vLmT7wR4sN8yBc`,
    expiresIn: '72 hours',
  },
  placeholders: {
    firstName: '{{ first_name }}',
    inviterName: '{{ inviter_name }}',
    workspaceName: '{{ workspace_name }}',
    email: '{{ email }}',
    setPasswordUrl: '{{ set_password_url }}',
    expiresIn: '{{ expires_in }}',
  },
  build: (p) => ({
    subject: `${p.inviterName} added you to ${p.workspaceName} on Servantium`,
    preheader: `Set your password to get started. Your link expires in ${p.expiresIn}.`,
    body: (
      <Email>
        <Banner tone="brand" size="hero" label="Welcome" title="Welcome to Servantium."
          subtitle="The operating system for services teams." astro="waving" />
        <Body>
          <Text>Hi {p.firstName},</Text>
          <Text>
            {p.inviterName} has added you to <b>{p.workspaceName}</b> on Servantium, where your team scopes,
            prices, delivers and learns from every project.
          </Text>
          <Text margin="0 0 24px">Set a password to finish setting up your account.</Text>
          <Button href={p.setPasswordUrl} width={220}>Set your password</Button>
          <Spacer size={12} />
          <Text size="xs" muted margin="0 0 28px">This link expires in {p.expiresIn} and can only be used once.</Text>
          <DataTable rows={[
            ['Sign-in email', p.email],
            ['Workspace', p.workspaceName],
            ['Sign in at', <Link href={company.urls.app}>app.servantium.com</Link>],
          ]} />
          <Heading>Once you're in</Heading>
          <Items items={[
            { title: 'Engagements', body: 'The quotes, documents and plans your team is working on.' },
            { title: 'Tasks', body: "Everything assigned to you, with what it depends on and when it's due." },
            { title: 'Capacity', body: "What you're booked on, week by week." },
          ]} />
          <LinkFallback href={p.setPasswordUrl} />
        </Body>
        <Footer reason={`You received this because ${p.inviterName} added you to ${p.workspaceName}. Not expecting it? You can ignore this email. Nothing happens until you set a password.`} />
      </Email>
    ),
  }),
});
