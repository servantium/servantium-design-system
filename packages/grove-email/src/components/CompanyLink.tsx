/**
 * CompanyLink — a link to one of Servantium's own addresses, looked up in company.json, so moving
 * the app or the help center updates every email at the next build.
 *
 *   Sign in at <CompanyLink to="app" />.
 *   The <CompanyLink to="help">Help Center</CompanyLink> answers the common questions.
 *
 * Without children it prints the address itself (app.servantium.com). <Button> takes `to` too.
 */
import type { ReactNode } from 'react';
import { company, type UrlKey } from '@servantium/brand';
import { Link } from './Link';

export function CompanyLink({ to, children }: {
  /** website · app · help · privacy · terms · trust · releaseNotes · status */
  to: UrlKey;
  children?: ReactNode;
}) {
  return <Link href={company.urls[to]}>{children ?? company.urls[to].replace(/^https:\/\//, '').replace(/\/$/, '')}</Link>;
}
