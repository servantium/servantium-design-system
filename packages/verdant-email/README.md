# @servantium/verdant-email

Verdant for email. A handful of components that assemble Outlook- and Gmail-safe HTML email, and the Servantium templates built from them. Colours come from `@servantium/verdant`; the logo, Astro, header art, address and links come from `@servantium/brand`. Nothing here defines a brand value of its own.

```bash
npm run build     # sync Verdant tokens, render every template to dist/
npm test          # the rules — see below
open dist/index.html
```

## The banner

Every email opens on the same banner: the forest night sky, the logo top-left, a dot and a label top-right, and a coloured rule along the bottom. A template makes two decisions about it.

**Size** — set by how often the email is sent:

| Size | Use for |
|---|---|
| `compact` | Notifications and anything frequent. A hero on every task would be noise. |
| `standard` | One headline. Security, notices, one-off transactional mail. |
| `hero` | Headline, tagline and Astro. Welcome, release notes, marketing. |

**Tone** — what kind of email it is. The banner itself never changes; tone colours the rule, the dot, the label, and any callout in the body.

| Tone | Rule | Use for |
|---|---|---|
| `brand` | green | Welcome, account, security, marketing |
| `activity` | slate blue | Tasks, mentions, assignments, reviews |
| `product` | teal | Release notes, new features |
| `warning` | amber | Degraded service, action needed soon |
| `critical` | coral | Outages, security alerts |
| `notice` | slate | Legal, regulatory, policy changes |

Outlook desktop ignores background images, so it shows the banner as flat forest. The text is designed to read on flat forest first.

## Components

| Component | What it's for |
|---|---|
| `Email` | The 600px column. Everything goes inside it. |
| `Banner` | The header — `size`, `tone`, `label`, `title`, `subtitle`, `astro`. |
| `Body` | The white card. |
| `Footer` | Links and address from `company.json`, plus a required `reason`. `settingsHref` for notifications; `unsubscribeHref` for marketing only. |
| `Heading` | Level 1 is the serif title (when the banner has none); level 2 is a section heading. |
| `Text`, `Eyebrow`, `Link` | Type. |
| `Button` | `primary` (the one action) or `secondary` (outline). Outlook gets a VML shape. |
| `DataTable` | Label/value rows. `panel` (grey) or `outline` (white with a border). Optional `title`. |
| `Callout` | A tinted panel for the one thing a reader must not miss. Takes a `tone`. |
| `Chip` | Small tinted label — "New", "Resolved". |
| `Items` | A run of titled items, with optional chip and meta line. |
| `Spacer`, `Divider`, `LinkFallback` | Spacing, a hairline, the printed URL under a button. |

### Writing a new email

```tsx
import { defineTemplate, Email, Banner, Body, Footer, Text, Button } from '@servantium/verdant-email';

export default defineTemplate<{ firstName: string; url: string }>({
  id: 'trial-ending', name: 'Trial ending', tone: 'warning', size: 'standard',
  sendsVia: 'Portal (Resend)',
  sample: { firstName: 'Jules', url: 'https://app.servantium.com/billing' },
  build: (p) => ({
    subject: 'Your trial ends in 3 days',
    preheader: 'Add a payment method to keep your workspace.',
    body: (
      <Email>
        <Banner tone="warning" size="standard" title="Your trial ends in 3 days" />
        <Body>
          <Text>Hi {p.firstName},</Text>
          <Button href={p.url}>Add a payment method</Button>
        </Body>
        <Footer reason="You're receiving this because you started a Servantium trial." />
      </Email>
    ),
  }),
});
```

Add it to `templates` in `src/index.ts` and it appears in the gallery and the tests.

## Sending

**From the portal (TypeScript, Resend):**

```ts
import { renderEmail, templates } from '@servantium/verdant-email';
const { subject, preheader, body } = templates.welcome.build(props);
const html = renderEmail({ subject, preheader, children: body, assets: { base: 'https://assets.servantium.com/brand' } });
await resend.emails.send({ from, to, subject, html });
```

**From the triggers (Python):** use `dist/jinja/<id>.html`. It has `{{ placeholders }}` where the values go and `{{ asset_base }}` in front of every image, and renders with the Jinja2 the triggers already use for documents:

```python
html = jinja_env.get_template("welcome.html").render(first_name=..., set_password_url=..., asset_base=ASSET_BASE)
```

**Password reset (Firebase):** paste `dist/firebase/password-reset.html` into Firebase → Authentication → Templates → Password reset → Message. Firebase fills `%LINK%` and `%EMAIL%`. While you're there, change **Sender name** from "Max" to "Servantium".

## The rules

`npm test` fails if any template breaks one:

- **No coloured bar down the left of anything.** Banned (founder, 2026-09-24). `Callout` carries its tone as a full tint.
- Every email opens on the forest banner.
- Footer links and address come from `company.json` — never typed into a template.
- Under 102 KB (Gmail clips longer messages).
- No SVG, no flex, no grid.
- Every image has alt text.
- Every button has an Outlook shape.
- Only optional mail (release notes, marketing) offers an unsubscribe; transactional and legal mail must not.
- Every text colour pairing passes WCAG AA (4.5:1).

One known exception is recorded as a test rather than hidden: **the primary button is white on #00C26D, about 2.3:1**, per the founder ruling. Changing the fill to `#037A47` would pass.

## Still to do before real sends

- **Host the assets** — see `@servantium/brand` → Hosting. Until then images are relative paths.
- **Test in real clients.** Everything here follows the Outlook/Gmail-safe patterns and is checked in a browser at 640 and 375px, but none of it has been through Outlook desktop, Gmail or Apple Mail yet. A Litmus or Email on Acid run is the next step.
- Sample content in the regulatory notice and incident is illustrative. Release notes are written from engineering's commits SER-563 and SER-564 — confirm the wording with them.
