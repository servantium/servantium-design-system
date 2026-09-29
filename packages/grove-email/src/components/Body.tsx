/**
 * Body — the white card the content sits on, closed by THE BOOKEND: a thin strip of the banner's
 * night sky along the bottom, so every email opens and closes on the same brand art. With images
 * off it's a plain forest bar.
 *
 * Frame, not content: everything a master writes below its frontmatter lands inside Body.
 */
import type { ReactNode } from 'react';
import { useAsset } from '../render';
import { color } from '../theme';

export function Body({ children }: { children: ReactNode }) {
  const { url, art } = useAsset();
  const bar = url('email/footer-bar.jpg');
  return (
    <>
      <tr>
        <td className="ve-px" bgcolor={color.surface} style={{ padding: '36px 40px 40px', backgroundColor: color.surface,
          border: `1px solid ${color.rule}`, borderTop: '0', borderBottom: '0' }}>
          {children}
        </td>
      </tr>
      <tr>
        <td height={12} bgcolor={color.banner} {...(art ? { background: bar } : {})}
          style={{ height: '12px', lineHeight: '12px', fontSize: '0', backgroundColor: color.banner, borderRadius: '0 0 14px 14px',
            ...(art ? { backgroundImage: `url(${bar})`, backgroundSize: 'cover', backgroundPosition: 'center', backgroundRepeat: 'no-repeat' } : {}) }}>&nbsp;</td>
      </tr>
    </>
  );
}
