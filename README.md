# Servantium Design System

How Servantium looks, in one place: the design tokens, the components for the website, help center and email, and the brand assets they share.

## Packages

| Package | What it is | Used by |
|---|---|---|
| **[Verdant](./packages/verdant)** `@servantium/verdant` | Design tokens as CSS custom properties: colour, type, spacing, easing. Framework-agnostic. | Every surface |
| **[Grove](./packages/grove)** `@servantium/grove` | Astro components for the website and help center: layout, navigation, search, docs and API pages. | servantium.com, help.servantium.com |
| **[Grove Email](./packages/grove-email)** `@servantium/grove-email` | Email components on Verdant tokens, every Servantium system email built from them, and the rules they're tested against. Released as Postmark-ready templates with a typed data contract. | Postmark and the Servantium backend |
| **[Brand](./packages/brand)** `@servantium/brand` | Logos, the mascot, email art, icons, social cards and company facts. Published to [assets.servantium.com](https://assets.servantium.com/index.html) at permanent, fingerprinted addresses. | Email, decks, listings; any surface that loads images by URL |

Verdant is the design language. Grove and Grove Email are the components built from it, one for the web and one for email. Brand holds the files both reach for.

## Layout

```
servantium-design-system/
├── packages/
│   ├── verdant/          tokens.css, base.css
│   ├── grove/            one .astro file per component
│   ├── grove-email/      src/emails/ (one .mdx per email), src/components/ (one file per component), docs/
│   └── brand/            assets/, company.json, assets.manifest.json, docs/
├── .github/workflows/
│   ├── publish.yml       publishes Verdant and Grove on v* tags
│   └── grove-email.yml   builds and tests the emails; releases them on email-v* tags
├── AGENTS.md             orientation for AI coding assistants
└── README.md
```

## How the sites use it

The website and help center pin a design-system version in a `.design-system-ref` file at their root, clone this repo at that version when they build, and install Verdant and Grove from the clone. Moving a site to a new version is a one-line pull request in that site's repo.

To release Verdant and Grove:

```bash
npm run version:patch     # or version:minor / version:major
git push --follow-tags    # the v* tag runs publish.yml
```

## Email

Emails are released separately, on `email-v*` tags. Each release publishes the Postmark-ready templates and the field contract as a GitHub release, which engineering pushes into Postmark. Start with the [Grove Email README](./packages/grove-email/README.md). The [engineering handover](./packages/grove-email/docs/engineering-handover.md) covers everything on the Postmark and backend side.

## Brand assets

Every file in `packages/brand/assets/` is published to `assets.servantium.com` under an address that includes a fingerprint of its contents, so an address never changes what it shows. [The asset library](./packages/brand/docs/asset-library.md) explains the scheme, what's in it, and how to add a file.

## Working in this repo

```bash
npm install                                        # all workspaces
npm run build --workspace @servantium/grove-email  # compile the emails into packages/grove-email/dist
npm test --workspace @servantium/grove-email       # the email rules
npm run check --workspace @servantium/brand        # the asset manifest matches the files
```

1. Branch from `main`.
2. Open a pull request with a conventional title (`feat:`, `fix:`, `chore:`). [CODEOWNERS](./.github/CODEOWNERS) requests the right reviewers.
3. Pull requests are squash-merged.

Generated files are committed and checked by the tests: `packages/grove-email/docs/style-guide.md`, `packages/grove-email/docs/templates.md` and `packages/brand/assets.manifest.json`. Change their sources, run the build, and commit the result.

## License

All rights reserved. Copyright 2026 Servantium Inc.
