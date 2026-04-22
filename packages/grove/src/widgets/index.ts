/**
 * @servantium/grove/widgets — sidebar widget primitives + registry.
 *
 * Usage (component import):
 *   import { StillStuckWidget, ChangelogWidget } from '@servantium/grove/widgets';
 *
 * Usage (frontmatter-driven — consumer registers widgets with names):
 *   import { createWidgetRegistry } from '@servantium/grove/widgets';
 *   const registry = createWidgetRegistry();
 *   // Then resolve from frontmatter: registry['still-stuck']
 */
export { default as Widget } from './Widget.astro';
export { default as StillStuckWidget } from './StillStuckWidget.astro';
export { default as ChangelogWidget } from './ChangelogWidget.astro';
export { default as ContactWidget } from './ContactWidget.astro';
export { default as RelatedWidget } from './RelatedWidget.astro';
export { default as ShareWidget } from './ShareWidget.astro';
export { default as CopyForAIWidget } from './CopyForAIWidget.astro';
export { default as SubscribeWidget } from './SubscribeWidget.astro';

export type WidgetName =
  | 'still-stuck'
  | 'changelog'
  | 'contact'
  | 'related'
  | 'share'
  | 'copy-for-ai'
  | 'subscribe';

/**
 * Registry mapping frontmatter widget names to their component imports.
 * Consumers can import the map and dynamically render widgets based on
 * `sidebarWidgets` frontmatter in their MDX files.
 *
 * Registry entries are references to the component modules; consumers
 * resolve the default export themselves for rendering.
 */
export async function createWidgetRegistry() {
  const [
    StillStuck,
    Changelog,
    Contact,
    Related,
    Share,
    CopyForAI,
    Subscribe,
  ] = await Promise.all([
    import('./StillStuckWidget.astro'),
    import('./ChangelogWidget.astro'),
    import('./ContactWidget.astro'),
    import('./RelatedWidget.astro'),
    import('./ShareWidget.astro'),
    import('./CopyForAIWidget.astro'),
    import('./SubscribeWidget.astro'),
  ]);
  return {
    'still-stuck': StillStuck.default,
    'changelog': Changelog.default,
    'contact': Contact.default,
    'related': Related.default,
    'share': Share.default,
    'copy-for-ai': CopyForAI.default,
    'subscribe': Subscribe.default,
  } as const;
}
