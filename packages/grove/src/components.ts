/**
 * Grove component re-exports.
 * This module provides the same named exports as @astrojs/starlight/components
 * so existing MDX files can switch imports without content changes.
 *
 * Usage in MDX:
 *   import { Aside, Steps, Tabs, TabItem } from '@/theme/grove/components';
 */
export { default as Aside } from './DocsAside.astro';
export { default as Steps } from './DocsSteps.astro';
export { default as Tabs } from './DocsTabs.astro';
// TabItem is handled within DocsTabs via slots
