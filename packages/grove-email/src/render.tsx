/**
 * render — turns a component tree into a complete, send-ready HTML email.
 *
 * React renders the BODY. The document around it (doctype, <head>, the Outlook-only comments) is
 * written here as a string, because those are the parts React cannot express: it has no way to
 * emit an HTML comment, and Outlook's layout depends on `<!--[if mso]>` comments that wrap other
 * elements. Keeping them in one function means no template ever has to know they exist.
 */
import { createContext, useContext, type ReactNode } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { hostedUrl, localAssetPath } from '@servantium/brand';
import { color, fonts } from './theme';

// ── Where images load from ─────────────────────────────────────────────────────────────────────
export type AssetOptions = {
  /** Sent mail: every image from its permanent, fingerprinted address at assets.servantium.com.
   *  Otherwise images load from a local copy of the brand assets — right for previews only. */
  hosted?: boolean;
  /** Per-file overrides, by asset path. */
  overrides?: Record<string, string>;
  /** Draw the header art. */
  art?: boolean;
};

const AssetContext = createContext<AssetOptions>({ hosted: false, art: true });

/** Components call this for every image, so hosting is decided once per render, not per file. */
export function useAsset() {
  const opts = useContext(AssetContext);
  return {
    url: (path: string) => opts.overrides?.[path] ?? (opts.hosted ? hostedUrl(path) : localAssetPath(path)),
    art: opts.art !== false,
  };
}

// ── Raw HTML ───────────────────────────────────────────────────────────────────────────────────
/** For the few places that need markup React won't write (VML buttons). Renders a bare <div>. */
export const Raw = ({ html }: { html: string }) => <div dangerouslySetInnerHTML={{ __html: html }} />;

// ── The document ───────────────────────────────────────────────────────────────────────────────
export type RenderInput = {
  subject: string;
  /** The grey line after the subject in the inbox. Say something the subject doesn't. */
  preheader: string;
  children: ReactNode;
  assets?: AssetOptions;
};

const HEAD_STYLE = `
  /* Progressive enhancement ONLY. Everything needed to read the email is inline; these rules make
     it better where they are honoured (iOS Mail, Apple Mail, Gmail apps, Outlook.com). */
  a[x-apple-data-detectors]{color:inherit !important;text-decoration:none !important;}
  u + #body a{color:inherit;text-decoration:none;}
  @media only screen and (max-width:620px){
    .ve-container{width:100% !important;}
    .ve-px{padding-left:24px !important;padding-right:24px !important;}
    .ve-stack{display:block !important;width:100% !important;}
    .ve-title{font-size:22px !important;line-height:28px !important;}
    .ve-astro{width:84px !important;height:84px !important;}
    .ve-astro-cell{width:96px !important;}
    .ve-hide-sm{display:none !important;}
    .ve-kv-label{width:96px !important;}
    .ve-label{letter-spacing:1px !important;}
    .ve-btn a{display:block !important;}
  }`;

/** Zero-width filler after the preheader, so clients don't pull body text into the preview. */
const PREHEADER_PAD = '&#8199;&#65279;&#847; '.repeat(70);

export function renderEmail({ subject, preheader, children, assets }: RenderInput): string {
  const body = renderToStaticMarkup(
    <AssetContext.Provider value={assets ?? { hosted: false, art: true }}>{children}</AssetContext.Provider>,
  );
  const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  return `<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<meta name="format-detection" content="telephone=no, date=no, address=no, email=no, url=no">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>${esc(subject)}</title>
<!--[if mso]>
<noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript>
<style>td,th,p,a,span,div,h2,h3{font-family:Arial,Helvetica,sans-serif !important;} h1{font-family:Georgia,'Times New Roman',serif !important;}</style>
<![endif]-->
<!--[if !mso]><!-->
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
<!--<![endif]-->
<style>${HEAD_STYLE}</style>
</head>
<body id="body" style="margin:0;padding:0;width:100%;background-color:${color.canvas};-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;">
<div style="display:none;max-height:0;max-width:0;overflow:hidden;opacity:0;mso-hide:all;font-size:1px;line-height:1px;color:${color.canvas};">${esc(preheader)}${PREHEADER_PAD}</div>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="${color.canvas}" style="background-color:${color.canvas};">
<tr><td align="center" style="padding:32px 12px 40px;">
<!--[if mso]><table role="presentation" width="600" align="center" cellspacing="0" cellpadding="0" border="0"><tr><td><![endif]-->
${body}
<!--[if mso]></td></tr></table><![endif]-->
</td></tr>
</table>
</body>
</html>
`;
}

/**
 * The Firebase console's message box takes a BODY, not a document: it drops <head>, so the web
 * fonts and mobile rules go (the email still reads correctly at any width). This keeps everything
 * from the preheader to the end of the outer table.
 */
export function toFirebaseFragment(html: string): string {
  const start = html.indexOf('<div style="display:none');
  const end = html.lastIndexOf('</body>');
  return `${html.slice(start, end).trim()}\n`;
}

export { fonts };
