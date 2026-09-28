/**
 * template — what every master email declares about how it's sent.
 *
 * The masters are MDX files in src/emails/; their frontmatter carries these values.
 */

/**
 * Which Postmark stream sends it.
 *   transactional — about this person's account or something they did. Must always arrive; never
 *                   carries an unsubscribe. Welcome, reset, tasks, incidents, required notices.
 *   broadcast     — optional reading sent to many. Postmark REQUIRES an unsubscribe here, keeps its
 *                   own unsubscribe list for the stream, and skips anyone on it. Release notes.
 */
export type Stream = 'transactional' | 'broadcast';
