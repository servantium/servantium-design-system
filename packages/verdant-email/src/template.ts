/**
 * template — the contract every email template meets.
 *
 * A template is its words and two decisions (banner size, tone). It ships SAMPLE props so it can be
 * previewed, and optionally PLACEHOLDER props — the same shape with `{{ jinja }}` strings in place of
 * values — so the export can write a version engineering's Python services fill in with Jinja, the
 * engine their document templates already use. One source; the portal sends the rendered React,
 * the triggers send the Jinja export.
 */
import type { ReactElement } from 'react';
import type { BannerSize } from './components/Layout';
import type { Tone } from './theme';

export type EmailTemplate<P> = {
  id: string;
  name: string;
  tone: Tone;
  size: BannerSize;
  /** Who sends it today, in plain words — the gallery prints this. */
  sendsVia: string;
  sample: P;
  placeholders?: P;
  build: (props: P) => { subject: string; preheader: string; body: ReactElement };
};

export const defineTemplate = <P,>(t: EmailTemplate<P>) => t;
