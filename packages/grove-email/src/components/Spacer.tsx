/**
 * Spacer — vertical space between components. Paragraphs space themselves; components don't, so
 * put a Spacer before and after a table, callout or button.
 *
 *   <Spacer size={28} />
 */
export function Spacer({ size = 24 }: { size?: number }) {
  return <div style={{ height: `${size}px`, lineHeight: `${size}px`, fontSize: '0' }}>&nbsp;</div>;
}
