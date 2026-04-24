/**
 * Grove prose enhancer — client-side behavior for .grove-prose bodies.
 *
 * Adds:
 *   - Copy buttons to every <pre> code block
 *   - Click-to-copy on every inline <code> token (with toast feedback)
 *   - Heading anchor links for h2/h3
 *
 * Decoupled from DocsLayout so any Astro consumer can opt in. Idempotent:
 * repeat calls or double-imports don't create duplicate buttons.
 *
 * Import pattern (consumer, client-side):
 *   <script>
 *     import { enhanceProse } from '@servantium/grove/prose-enhance';
 *     enhanceProse();
 *   </script>
 * Or include via a <script type="module" src=".../prose-enhance.js">.
 */

function showToast(message: string): void {
  let toast = document.querySelector<HTMLDivElement>('.grove-code-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'grove-code-toast';
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  requestAnimationFrame(() => toast!.classList.add('visible'));
  window.clearTimeout((toast as any).__hideTimer);
  (toast as any).__hideTimer = window.setTimeout(() => {
    toast!.classList.remove('visible');
  }, 1400);
}

async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

function attachCopyButtonsToPre(root: ParentNode): void {
  root.querySelectorAll<HTMLPreElement>('.grove-prose pre').forEach((pre) => {
    if (pre.querySelector('.code-copy-btn')) return;
    if (pre.dataset.groveNoCopy === '1') return;

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'code-copy-btn';
    btn.setAttribute('aria-label', 'Copy code');
    btn.innerHTML = `
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
      </svg>
      <span>Copy</span>
    `;
    btn.addEventListener('click', async () => {
      const code = pre.querySelector('code');
      const text = code ? code.textContent ?? '' : pre.textContent ?? '';
      const ok = await copyText(text);
      if (!ok) return;
      const span = btn.querySelector('span');
      const orig = span?.textContent ?? 'Copy';
      if (span) span.textContent = 'Copied';
      btn.classList.add('copied');
      setTimeout(() => {
        if (span) span.textContent = orig;
        btn.classList.remove('copied');
      }, 1400);
    });
    pre.appendChild(btn);
  });
}

function attachInlineCodeClickToCopy(root: ParentNode): void {
  root.querySelectorAll<HTMLElement>('.grove-prose code').forEach((el) => {
    // Skip <code> inside <pre> — the pre copy button handles those.
    if (el.closest('pre')) return;
    if (el.dataset.groveCodeReady === '1') return;
    el.dataset.groveCodeReady = '1';
    el.setAttribute('role', 'button');
    el.setAttribute('tabindex', '0');
    el.setAttribute('aria-label', 'Click to copy');
    el.title = 'Click to copy';

    const trigger = async () => {
      const text = el.textContent ?? '';
      if (!text) return;
      const ok = await copyText(text);
      if (!ok) return;
      el.classList.add('grove-code-copied');
      showToast(`Copied: ${text.length > 32 ? text.slice(0, 29) + '…' : text}`);
      setTimeout(() => el.classList.remove('grove-code-copied'), 900);
    };
    el.addEventListener('click', trigger);
    el.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        trigger();
      }
    });
  });
}

function attachHeadingAnchors(root: ParentNode): void {
  root.querySelectorAll<HTMLHeadingElement>('.grove-prose h2, .grove-prose h3').forEach((h) => {
    if (!h.id || h.querySelector('.heading-anchor')) return;
    const anchor = document.createElement('a');
    anchor.href = `#${h.id}`;
    anchor.className = 'heading-anchor';
    anchor.setAttribute('aria-label', `Link to ${h.textContent ?? 'section'}`);
    anchor.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
      </svg>
    `;
    h.style.position = 'relative';
    h.insertBefore(anchor, h.firstChild);
  });
}

export function enhanceProse(root: ParentNode = document): void {
  attachCopyButtonsToPre(root);
  attachInlineCodeClickToCopy(root);
  attachHeadingAnchors(root);
}

// Auto-run on DOM ready + view-transition nav when used as a plain script.
if (typeof document !== 'undefined') {
  const run = () => enhanceProse();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
  document.addEventListener('astro:page-load', run);
}
