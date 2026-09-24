/**
 * template — the contract every email meets, whether it's written in TSX or MDX.
 *
 * Product emails (welcome, reset, task, notice) are TSX: their words are fixed and their DATA comes
 * from the product. Editorial emails (release notes, incidents, marketing) are MDX with frontmatter,
 * because a person writes each one. Both produce this same shape, so the export, the gallery, the
 * tests and the Postmark push treat them identically.
 */
import type { ReactElement } from 'react';
import type { Tone } from './theme';

/**
 * Which Postmark stream sends it.
 *   transactional — about this person's account or something they did. Must always arrive; never
 *                   carries an unsubscribe. Welcome, reset, tasks, incidents, required notices.
 *   broadcast     — optional reading sent to many. Postmark REQUIRES an unsubscribe here and adds
 *                   one if it's missing. Release notes, newsletters, marketing.
 */
export type Stream = 'transactional' | 'broadcast';

export type EmailTemplate<P> = {
  id: string;
  name: string;
  tone: Tone;
  stream: Stream;
  /** Who sends it and how, in plain words — the gallery prints this. */
  sendsVia: string;
  sample: P;
  /** Same shape as `sample`, with `{{ merge_fields }}` — for the Postmark/Jinja export. */
  placeholders?: P;
  build: (props: P) => { subject: string; preheader: string; body: ReactElement };
};

export const defineTemplate = <P,>(t: EmailTemplate<P>) => t;
