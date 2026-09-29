/**
 * Email-only HTML attributes React's types leave off <td>. `bgcolor` is the background Outlook
 * desktop actually honours; `background` is the image attribute older Gmail reads when it ignores
 * the CSS. React passes both through untouched — this only teaches the type checker they exist.
 */
import 'react';

declare module 'react' {
  interface TdHTMLAttributes<T> {
    bgcolor?: string;
    background?: string;
  }
}
