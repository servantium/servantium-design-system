# Servantium Design System

Single source of truth for visual design and documentation components across every Servantium surface. Private monorepo, two packages.

## Packages

| Package | Contents | Consumed by |
|---|---|---|
| **[`@servantium/verdant`](./packages/verdant)** | CSS custom properties (colors, typography, spacing, easing), optional base/reset styles. Pure CSS, framework-agnostic. | servantium-website, servantium-help, servantium-internal (portal) |
| **[`@servantium/grove`](./packages/grove)** | Astro documentation components (`DocsLayout`, `DocsSidebar`, `DocsSearch`, `TableOfContents`, `DocsAside`, `DocsSteps`, `DocsTabs`, `DocsPagination`, `ReleaseTimeline`). | servantium-website, servantium-help |

## Repo layout

```
servantium-design-system/
├── packages/
│   ├── verdant/                  # @servantium/verdant
│   │   ├── tokens.css            # Tailwind v4 @theme block
│   │   ├── base.css              # optional reset + typography defaults
│   │   ├── package.json
│   │   └── README.md
│   └── grove/                    # @servantium/grove
│       ├── src/
│       │   ├── components/       # Individual .astro files + index.ts
│       │   └── index.ts          # Public root (stub — use deep imports)
│       ├── package.json
│       └── README.md
├── .github/workflows/
│   └── publish.yml               # Publishes both packages + notifies consumers on tag push
├── package.json                  # Workspaces root (not published)
└── README.md
```

## How consumers pick up changes

```
  ┌─────────────────────────────┐
  │ design-system: git tag vX.Y │
  └──────────────┬──────────────┘
                 │ push
                 ▼
  ┌──────────────────────────────────────────┐
  │ publish.yml                              │
  │  1. npm publish @servantium/verdant      │
  │  2. npm publish @servantium/grove        │
  │  3. repository_dispatch to consumers     │
  └──────┬────────────────────────┬──────────┘
         │                        │
         ▼                        ▼
  ┌──────────────────┐    ┌──────────────────┐
  │ website          │    │ help             │
  │  update-ds.yml   │    │  update-ds.yml   │
  │  opens PR to     │    │  opens PR to     │
  │  develop w/ new  │    │  develop w/ new  │
  │  .design-system  │    │  .design-system  │
  │  -ref            │    │  -ref            │
  └────────┬─────────┘    └────────┬─────────┘
           │ merge to develop       │
           ▼                        ▼
      test.servantium.com    qa.help.servantium.com
           │ human promotes develop → main
           ▼                        ▼
      servantium.com         help.servantium.com
```

**Each consumer has a `.design-system-ref` file at its root** pinning it to a specific tag or SHA. On tag push here, the `publish.yml` workflow dispatches to both consumers; each consumer's `update-design-system.yml` bumps its pin and opens a PR against `develop`. The PR preview-deploys automatically. A human reviewer merges to promote.

## Release flow

```bash
# 1. Make changes on a feature branch → PR → merge to main
# 2. Bump version (patch|minor|major)
npm version patch --workspaces --include-workspace-root false

# 3. Push tag
git push --follow-tags
```

The publish workflow handles everything after that.

## Local development

```bash
npm install               # install workspaces
```

To consume locally from a sibling checkout during development, have the consumer repo do `npm install` after cloning this repo as `vendor/design-system` in that consumer's working tree. Consumers already do this at build time via their Cloudflare Pages build command.

## Authentication notes

- **Publishing** uses `GITHUB_TOKEN` (automatic in CI). No secrets needed for publish.
- **Consumer dispatch** uses a `DESIGN_SYSTEM_DISPATCH_PAT` secret with `repo` scope on the two consumer repos. Set this in repo settings once, then it just works. (See `CONTRIBUTING.md` if/when added.)
- **Installing from GitHub Packages registry** requires `read:packages` scope. Consumers sidestep this by cloning the repo directly at build time and using `file:` protocol in package.json — simpler than PAT-passing to Cloudflare Pages.

## Contributing

1. Branch from `main`
2. Make changes, add tests if applicable
3. PR with conventional commit-style title (`feat:`, `fix:`, `chore:`)
4. Merge squashes to `main`
5. Cut a version bump + tag when you want it to propagate

## License

All rights reserved. Copyright 2026 Servantium Inc.
