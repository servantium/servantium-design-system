/**
 * Editable — a paragraph an admin can replace later without a template change. The default shows
 * until the sender passes a value for `field`.
 *
 *   <Editable field="welcome_intro">Your team uses Servantium to scope, price and deliver work.</Editable>
 *
 * Mark the field `optional: true`. Only the words can change; the design can't. Postmark does this
 * natively ({{#field}}…{{/field}}{{^field}}default{{/field}}), so admin-editable copy needs data,
 * not a new rendering system.
 */
import type { ReactNode } from 'react';
import { Text } from './Text';

export function Editable({ field, children }: { field: string; children?: ReactNode }) {
  return <>{`{{#${field}}}`}<Text>{'{{ . }}'}</Text>{`{{/${field}}}{{^${field}}}`}<Text>{children}</Text>{`{{/${field}}}`}</>;
}
