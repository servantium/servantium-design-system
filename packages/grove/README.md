# @servantium/grove

Grove is the documentation component library used by the Servantium marketing site and help site. Astro-only.

## Install

```bash
npm install @servantium/grove @servantium/verdant astro
```

## Usage

```astro
---
import DocsLayout from '@servantium/grove/DocsLayout';
import { Aside, Steps, Tabs } from '@servantium/grove/components';
---

<DocsLayout title="Quick start">
  <Aside type="tip">Welcome.</Aside>
</DocsLayout>
```

## Components

| Component | Purpose |
|---|---|
| `DocsLayout` | 3-column shell: sidebar, content, TOC |
| `DocsSidebar` | Collapsible tree nav |
| `DocsSearch` | Pagefind-powered search with filter tabs |
| `TableOfContents` | Scroll-spy TOC |
| `DocsAside` | Callout (tip/note/caution/danger) |
| `DocsSteps` | Numbered step wizard |
| `DocsTabs` | Tab switcher |
| `DocsPagination` | Prev/next nav |
| `ReleaseTimeline` | Vertical timeline for release notes |

## Design tokens

Grove styles consume tokens from `@servantium/verdant`. Make sure `tokens.css` is imported at the app root before any Grove component renders.
