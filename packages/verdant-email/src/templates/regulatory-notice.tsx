/**
 * Regulatory notice — a notice we are legally obliged to send. The sample is a sub-processor change
 * under the Data Processing Addendum; the same shape serves policy and terms updates.
 *
 * Formal on purpose: the default tone (nothing is wrong; no action is required), no Astro, a summary
 * table that answers the four
 * questions a legal reader has before reading any prose, and a SECONDARY button — a filled green
 * button on a legal notice reads as a call to action. The footer says why there is no unsubscribe:
 * a required notice isn't marketing and can't be opted out of — which is also why it goes out on
 * Postmark's TRANSACTIONAL stream, one message per admin. Postmark's broadcast stream would add an
 * unsubscribe link to it automatically.
 *
 * SAMPLE CONTENT: the change described is illustrative. Confirm the facts before sending one.
 */
import { company } from '@servantium/brand';
import { Banner, Body, Email, Footer } from '../components/Layout';
import { Button, DataTable, Heading, Spacer, Text } from '../components/Content';
import { defineTemplate } from '../template';

type Props = {
  adminFirstName: string;
  workspaceName: string;
  effectiveDate: string;
  reference: string;
};

export default defineTemplate<Props>({
  id: 'regulatory-notice',
  name: 'Regulatory notice',
  tone: 'default',
  stream: 'transactional',
  sendsVia: 'Postmark template `regulatory-notice`, to each workspace administrator. Set ReplyTo to a monitored inbox — the body invites objections by reply',
  sample: { adminFirstName: 'Dana', workspaceName: 'Halcyon Bioanalytical Services', effectiveDate: 'October 24, 2026', reference: 'SVC-2026-0917' },
  placeholders: { adminFirstName: '{{ admin_first_name }}', workspaceName: '{{ workspace_name }}', effectiveDate: '{{ effective_date }}', reference: '{{ reference }}' },
  build: (p) => ({
    subject: `Notice: changes to Servantium's sub-processors, effective ${p.effectiveDate}`,
    preheader: 'No action is needed. You may object within 30 days under your Data Processing Addendum.',
    body: (
      <Email>
        <Banner label="Service notice" title="Changes to our sub-processors" />
        <Body>
          <Text>Hello {p.adminFirstName},</Text>
          <Text margin="0 0 24px">
            We're writing to tell you about a change to the sub-processors Servantium uses to provide the service
            to <b>{p.workspaceName}</b>. Under our Data Processing Addendum we give you at least 30 days' notice before
            a change like this takes effect.
          </Text>
          <DataTable variant="outline" labelWidth={136} rows={[
            ['Effective date', <b>{p.effectiveDate}</b>],
            ['Applies to', p.workspaceName],
            ['Action required', 'None. You may object before the effective date.'],
            ['Notice reference', p.reference],
          ]} />
          <Heading>What's changing</Heading>
          <Text>
            We're adding a sub-processor to deliver in-app email notifications, such as task assignments and password
            resets. It will process your users' names and email addresses only. It will not process project, quote or
            financial data.
          </Text>
          <Heading>What you need to do</Heading>
          <Text margin="0 0 28px">
            Nothing. If you have a reasonable objection, reply to this email before {p.effectiveDate} and we'll work
            through it with you.
          </Text>
          <Button href={company.urls.trust} variant="secondary" width={270}>View the sub-processor list</Button>
          <Spacer size={28} />
          <Text size="sm" muted margin="0">Servantium Privacy &amp; Security</Text>
        </Body>
        <Footer reason="This is a required service notice about your organization's Servantium account. It is sent to workspace administrators and is not marketing, so it can't be unsubscribed from." />
      </Email>
    ),
  }),
});
