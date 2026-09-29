/**
 * If — content that appears only when the sender supplies `field`. Inside, {{ . }} is that value.
 *
 *   <If field="message">
 *     <Callout tone="neutral" title="What they wrote">“{{ . }}”</Callout>
 *   </If>
 *
 * Mark the field `optional: true` in the frontmatter. This compiles to a Postmark section,
 * {{#message}}…{{/message}}, and Postmark SCOPES sections: inside one, only {{ . }} is visible.
 * Refer to any other field and the build fails, because Postmark would quietly print nothing.
 */
import type { ReactNode } from 'react';

export function If({ field, children }: { field: string; children?: ReactNode }) {
  return <>{`{{#${field}}}`}{children}{`{{/${field}}}`}</>;
}
