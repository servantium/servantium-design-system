/**
 * contract-py — the field contract as Python types, so the backend can type-check what it sends.
 *
 * One TypedDict per template (optional fields are NotRequired) and one per list item, plus the
 * template table: alias → stream and data type. Generated on every build; never edit the output.
 */
import { company } from '@servantium/brand';
import type { Built } from './collect';

const camel = (s: string) => s.split(/[-_]/).map((w) => w[0].toUpperCase() + w.slice(1)).join('');
const q = (s: string) => JSON.stringify(s);

export function pythonContract(emails: Built[]): string {
  const out: string[] = [
    '"""Servantium email contract. GENERATED from servantium-design-system/packages/grove-email by `npm run build` — do not edit.',
    '',
    'Each template alias has a TypedDict describing the data (TemplateModel) Postmark needs to render it.',
    'Optional fields may be left out: the email reads fine without them. Values are plain text; Postmark',
    'escapes them. Format dates, money and names for the recipient before sending.',
    '"""',
    'from __future__ import annotations',
    '',
    'from typing import Literal, NotRequired, TypedDict',
    '',
    `FROM = ${q(`Servantium <${company.email.from}>`)}`,
    `REPLY_TO = ${q(company.email.help)}`,
    '',
  ];
  const table: string[] = [];
  for (const e of emails) {
    const cls = `${camel(e.id)}Data`;
    const lines: string[] = [];
    for (const [name, f] of Object.entries(e.fields)) {
      if (Array.isArray(f.example)) {
        const item = `${camel(e.id)}${camel(name)}Item`;
        const keys = [...new Set(f.example.flatMap((i) => Object.keys(i)))];
        out.push(`class ${item}(TypedDict):`, ...keys.map((k) => `    ${k}: str`), '', '');
        lines.push(`    ${name}: ${f.optional ? `NotRequired[list[${item}]]` : `list[${item}]`}${f.note ? `  # ${f.note}` : ''}`);
      } else {
        lines.push(`    ${name}: ${f.optional ? 'NotRequired[str]' : 'str'}${f.note ? `  # ${f.note.replace(/\n/g, ' ')}` : ''}`);
      }
    }
    out.push(`class ${cls}(TypedDict):`, `    """${e.name}. ${e.stream} stream."""`, ...lines, '', '');
    table.push(`    ${q(e.id)}: {"message_stream": ${q(e.stream === 'broadcast' ? 'broadcast' : 'outbound')}, "data": ${cls}},`);
  }
  out.push(`Alias = Literal[${emails.map((e) => q(e.id)).join(', ')}]`, '', 'TEMPLATES: dict[str, dict] = {', ...table, '}', '');
  return out.join('\n');
}
