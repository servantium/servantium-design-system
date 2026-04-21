# Servantium Design System

Private monorepo hosting the two foundational packages that every Servantium surface consumes.

| Package | Purpose | Consumed by |
|---|---|---|
| [`@servantium/verdant`](./packages/verdant) | CSS tokens (colors, typography, spacing, easing) + base styles | website, help, internal portal |
| [`@servantium/grove`](./packages/grove) | Astro components for documentation layouts (DocsLayout, DocsSidebar, DocsSearch, TOC, Aside, Steps, Tabs) | website, help |

## Installation

Both packages are published to GitHub Packages under the `@servantium` scope. Consumers need a `.npmrc` with:

```
@servantium:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}
```

Then:

```bash
npm install @servantium/verdant @servantium/grove
```

## Release flow

Versioning is coordinated across packages. To cut a release:

```bash
npm run version:patch   # or :minor / :major
git push --follow-tags
```

GitHub Actions publishes to GitHub Packages on tag push.

## Architecture

- **Verdant** is pure CSS. No JavaScript, no framework dependency. Exposes tokens as CSS custom properties under `@theme`.
- **Grove** is Astro-only today. A React-equivalent (`@servantium/grove-react`) can be added later when the portal needs in-app docs.

Updating a token in Verdant cascades to every consumer on their next install/rebuild.

## Development

```bash
npm install           # install workspaces
npm run build         # build all packages
```

Local consumers can link via file: protocol during development:

```json
"dependencies": {
  "@servantium/grove": "file:../servantium-design-system/packages/grove"
}
```
