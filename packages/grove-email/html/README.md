# Email templates (HTML)

Every Servantium system email as a ready-to-use template: `<alias>.html` and its plain-text `<alias>.txt`. The file name is the Postmark template alias.

**Generated. Don't edit these files.** Each one is built from its MDX source in [`../src/emails/`](../src/emails/) by `npm run build`, and CI fails if they drift. To change an email, change its MDX.

- **Placeholders:** `{{ field }}` is filled by Postmark at send time. A few templates also use `{{#field}}…{{/field}}` (shown only when set) and `{{#each list}}…{{/each}}` (repeated per item).
- **Subject, sender and fields:** [`contract.json`](./contract.json) gives each template's subject, stream, from, reply-to, and every field with an example and a note. [docs/templates.md](../docs/templates.md) is the same in prose.
- **Images** load from `assets.servantium.com`. Nothing to upload.

The handover for engineering is [HANDOVER.md](../HANDOVER.md).
