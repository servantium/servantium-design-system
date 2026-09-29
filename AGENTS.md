# AGENTS.md

Orientation for AI coding assistants working in this repo. People should start with [README.md](./README.md).

## What's here

| Path | What | Read first |
|---|---|---|
| `packages/verdant/` | Design tokens (CSS custom properties) | `packages/verdant/README.md` |
| `packages/grove/` | Astro components for the website and help center | `packages/grove/README.md` |
| `packages/grove-email/` | System email: components, the emails (`src/emails/*.mdx`), rules, docs | `packages/grove-email/README.md`, then `packages/grove-email/docs/` |
| `packages/brand/` | Brand files, company facts, and the asset library at assets.servantium.com | `packages/brand/README.md`, `packages/brand/docs/asset-library.md` |

## Tasks you're likely to be given

| Task | Where the answer is |
|---|---|
| Write or change an email | `packages/grove-email/docs/writing-an-email.md`, a worked example end to end |
| Choose, name or format an email's data | `packages/grove-email/docs/fields.md` |
| Look up a component, a frontmatter key, a tone or a rule | `packages/grove-email/docs/style-guide.md` (generated) |
| Look up a template's fields | `packages/grove-email/docs/templates.md` (generated) |
| Wire Postmark, send an email from the backend, handle support replies | `packages/grove-email/docs/engineering-handover.md` |
| Release emails, retire a template, update release notes | `packages/grove-email/docs/maintaining.md` |
| Add or change a logo, icon or image | `packages/brand/docs/asset-library.md` |
| Change the address, a footer link, help@ or social links | `packages/brand/company.json` |
| Make this repo private, or change how the sites install it | `docs/going-private.md` |

## Commands

```bash
npm install
npm run build --workspace @servantium/grove-email   # emails → packages/grove-email/dist; regenerates docs/style-guide.md and docs/templates.md
npm test --workspace @servantium/grove-email        # must pass before any pull request
npm run manifest --workspace @servantium/brand      # after adding or changing anything in packages/brand/assets
npm run check --workspace @servantium/brand         # the manifest matches the files
```

## Rules

- **Never hand-edit generated files:** `packages/grove-email/dist/`, `packages/grove-email/docs/style-guide.md`, `packages/grove-email/docs/templates.md`, `packages/brand/assets.manifest.json`, `packages/grove-email/src/tokens.generated.ts`. Change the source and rebuild.
- **An email's frontmatter `fields` is a data contract** that the backend sends against. Adding a required field, or renaming or removing one, needs the safe order in `fields.md` and engineering's review.
- **Asset addresses are permanent.** Never overwrite or delete anything on assets.servantium.com. A changed file gets a new fingerprinted address automatically.
- **Other companies' logos are never stored here.** They're hotlinked from Brandfetch, whose terms forbid caching.
- **No secrets in this repo.** It's public. Tokens live in the owning team's secret store.
- **Don't type facts into emails.** Addresses, links, colours and images come from `company.json`, Verdant and the asset library.
- **Postmark and the backend are engineering's.** This repo's workflow stops at a GitHub release. Don't add steps that push to Postmark or call Servantium systems.
