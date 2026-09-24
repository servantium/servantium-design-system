/**
 * Release notes — the hero banner with Astro, the `product` tone, and the one email in the set that
 * carries an unsubscribe link: product updates are optional reading, so they must be opt-out-able.
 *
 * SAMPLE CONTENT with receipts: each item is written from one of engineering's two most recent
 * commits on Servantium master (SER-563, SER-564, 2026-09-24). The wording is our reading of the
 * commit titles — confirm it with engineering before this is sent to anyone.
 */
import { company } from '@servantium/brand';
import { Banner, Body, Email, Footer } from '../components/Layout';
import { Button, Items, Spacer, Text } from '../components/Content';
import { defineTemplate } from '../template';

type Props = { firstName: string; month: string; unsubscribeUrl: string };

export default defineTemplate<Props>({
  id: 'release-notes',
  name: 'Release notes',
  tone: 'product',
  size: 'hero',
  sendsVia: 'A sender, to users subscribed to product updates',
  sample: { firstName: 'Jules', month: 'September 2026', unsubscribeUrl: `${company.urls.app}/profile#email` },
  build: (p) => ({
    subject: `What's new in Servantium — ${p.month}`,
    preheader: 'Document templates that repeat correctly, better snippet navigation, and live values in variables.',
    body: (
      <Email>
        <Banner tone="product" size="hero" label="Release notes" title="What's new in Servantium"
          subtitle={p.month} astro="professor" />
        <Body>
          <Text>Hi {p.firstName},</Text>
          <Text margin="0 0 28px">Here's what changed this month. Most of it is in documents.</Text>
          <Items items={[
            {
              chip: { tone: 'product', label: 'Improved' },
              title: 'Repeating sections in document templates',
              body: 'A table that repeats for every quote line or phase now fills in the right values on every row, so templates with line-item tables come out complete the first time.',
            },
            {
              chip: { tone: 'product', label: 'Improved' },
              title: 'Snippet navigation in documents',
              body: 'Moving from a document to the snippet behind it now takes you to the right place.',
            },
            {
              chip: { tone: 'brand', label: 'New' },
              title: 'Live values in document variables',
              body: 'Variables show the current value from the engagement or quote, rather than a copy from when the document was made.',
            },
            {
              chip: { tone: 'notice', label: 'Fixed' },
              title: 'No more duplicate variables',
              body: 'The variables panel no longer lists the same variable twice.',
            },
          ]} />
          <Spacer size={8} />
          <Button href={company.urls.releaseNotes} width={250}>Read the full release notes</Button>
        </Body>
        <Footer reason="You're receiving product updates because you're a Servantium user." unsubscribeHref={p.unsubscribeUrl} />
      </Email>
    ),
  }),
});
