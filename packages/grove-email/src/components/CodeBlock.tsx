/**
 * CodeBlock — a monospace block. A Markdown ``` fence becomes one. For internal and technical
 * mail; customers rarely need it.
 */
import { color, neutral } from '../theme';

export function CodeBlock({ children }: { children: string }) {
  return (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0} bgcolor={neutral.tint}
      style={{ backgroundColor: neutral.tint, borderRadius: '8px', margin: '0 0 16px' }}>
      <tbody><tr><td style={{ padding: '12px 16px', fontFamily: "Menlo, Consolas, 'Courier New', monospace", fontSize: '12px',
        lineHeight: '18px', color: color.ink, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{children}</td></tr></tbody>
    </table>
  );
}
