/**
 * Incident — an outage or degraded service. The `critical` tone puts coral on the banner rule and
 * the status chip, and nothing else changes: an outage email should look like Servantium having a
 * bad day, not like a different company.
 *
 * The status table answers the questions in the order people ask them: is it broken, since when,
 * what's affected, what ISN'T, when will I hear more. There's no "check status" button because
 * Servantium has no public status page yet — linking to one that doesn't exist is worse than none.
 *
 * SAMPLE CONTENT: a hypothetical incident.
 */
import { Banner, Body, Email, Footer } from '../components/Layout';
import { Callout, Chip, DataTable, Heading, Items, Text } from '../components/Content';
import { defineTemplate } from '../template';

type Props = { workspaceName: string };

export default defineTemplate<Props>({
  id: 'incident',
  name: 'Service incident',
  tone: 'critical',
  size: 'standard',
  sendsVia: 'A sender, to workspace administrators',
  sample: { workspaceName: 'Halcyon Bioanalytical Services' },
  build: (p) => ({
    subject: 'Service alert: document generation is delayed',
    preheader: "Documents are queued and will complete when the service recovers. You don't need to regenerate them.",
    body: (
      <Email>
        <Banner tone="critical" size="standard" label="Service alert" title="Document generation is delayed" />
        <Body>
          <DataTable variant="outline" labelWidth={120} rows={[
            ['Status', <Chip tone="critical">Investigating</Chip>],
            ['Started', 'Sep 24, 2026 · 2:10 PM ET'],
            ['Affected', 'Generating and regenerating documents'],
            ['Working normally', 'Quotes, engagements, resource plans and project plans'],
            ['Next update', 'By 3:30 PM ET'],
          ]} />
          <Heading>What this means for you</Heading>
          <Text margin="0 0 20px">
            Documents you generate are being queued and will complete once the service recovers. Everything else in
            Servantium is working normally.
          </Text>
          <Callout tone="critical" title="Please don't regenerate">
            Regenerating a delayed document adds a second copy to the queue rather than speeding up the first.
          </Callout>
          <Heading>Updates</Heading>
          <Items items={[
            { chip: { tone: 'warning', label: 'Identified' }, meta: '2:24 PM ET', title: 'We found the cause',
              body: 'A backlog in the rendering service is slowing new documents. We are clearing it now.' },
            { chip: { tone: 'critical', label: 'Investigating' }, meta: '2:10 PM ET', title: 'Documents are taking longer to generate',
              body: "We're looking into delays when generating documents." },
          ]} />
          <Text size="sm" muted margin="0">We'll email you again when this is resolved.</Text>
        </Body>
        <Footer reason={`You're receiving this because you're an administrator of ${p.workspaceName} and this affects your workspace.`} />
      </Email>
    ),
  }),
});
