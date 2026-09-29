/**
 * text — the plain-text part of an email, derived from its HTML.
 *
 * Every send should carry a text part as well as HTML: some people read mail as text, and spam
 * filters score an HTML-only message worse. Deriving it means nobody maintains a second copy.
 * Buttons become "Label (url)", table rows become "Label: value", images and the Outlook-only
 * markup disappear.
 */
const ENTITIES: Record<string, string> = {
  amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', ldquo: '“', rdquo: '”', lsquo: '‘', rsquo: '’',
  mdash: '—', ndash: '–', hellip: '…', middot: '·', bull: '•', rarr: '→',
};

const decode = (s: string) =>
  s.replace(/&(#x[0-9a-f]+|#\d+|\w+);/gi, (m, e: string) => {
    if (e[0] === '#') {
      const n = e[1] === 'x' || e[1] === 'X' ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10);
      return String.fromCodePoint(n);
    }
    return ENTITIES[e.toLowerCase()] ?? m;
  });

/** Zero-width and figure spaces — the preheader padding. */
const INVISIBLE = /[ ​-‍﻿͏­]/g;

export function htmlToText(html: string): string {
  let s = html.slice(html.indexOf('<body'), html.lastIndexOf('</body>'));
  s = s
    .replace(/<div style="display:none[\s\S]*?<\/div>/, '')          // the preheader
    .replace(/<!--[\s\S]*?-->/g, '')                                  // Outlook-only markup, incl. VML buttons
    .replace(/<a\s[^>]*href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/gi, (_, href: string, inner: string) => {
      // An image-only link (the LinkedIn icon) reads as its alt text.
      const alt = /<img[^>]*\salt="([^"]+)"/i.exec(inner)?.[1];
      const label = (alt ?? inner.replace(/<[^>]+>/g, '')).trim();
      const target = href.replace(/^mailto:/i, '');
      return !label || decode(label) === decode(target) ? target : `${label} (${target})`;
    })
    .replace(/<img[^>]*>/gi, '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(p|h1|h2|h3|table)>/gi, '\n\n')
    .replace(/<\/(tr|div)>/gi, '\n')
    .replace(/<\/td>/gi, '\t')
    .replace(/<[^>]+>/g, '');
  return decode(s)
    .replace(INVISIBLE, '')
    .replace(/●\s*/g, '')                                        // the banner's tone dot
    .split('\n')
    .map((line) => {
      // A row of cells: a short label and its value read as "Label: Value" (data tables); a bullet
      // keeps its space; anything else (the address beside LinkedIn) goes on separate lines.
      const cells = line.split('\t').map((c) => c.replace(/[ \u00A0]+/g, ' ').trim()).filter(Boolean);
      if (cells.length === 2 && cells[0] === '\u2022') return cells.join(' ');
      if (cells.length === 2 && cells[0].length <= 30) return `${cells[0]}: ${cells[1]}`;
      return cells.join('\n');
    })
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim() + '\n';
}
