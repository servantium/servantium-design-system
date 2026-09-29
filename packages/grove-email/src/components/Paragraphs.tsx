/**
 * Paragraphs — free text the SENDER supplies, one { text } item per paragraph. A support reply
 * uses it for the message our team wrote.
 *
 *   <Paragraphs field="reply" />
 *
 * The sender splits the text on blank lines. Paragraphs, not line breaks, because Outlook ignores
 * the CSS that would keep newlines — a paragraph renders everywhere. The text is escaped, so a
 * customer's message can't inject HTML.
 */
import { color, fonts } from '../theme';

export function Paragraphs({ field }: { field: string }) {
  return (
    <>
      {`{{#each ${field}}}`}
      <p style={{ margin: '0 0 16px', fontFamily: fonts.body, fontSize: '16px', lineHeight: '26px', color: color.ink }}>{'{{ text }}'}</p>
      {'{{/each}}'}
    </>
  );
}
