# Email templates

<!-- GENERATED from src/emails/*.mdx by `npm run build`. Edit the masters, not this page; `npm test` fails if it's stale. -->

Every email, with the data its sender supplies. The alias is the Postmark template alias and the master's file name. Streams are Postmark's: `outbound` for transactional mail, `broadcast` for mail people can unsubscribe from. Every email is sent from `Servantium <notifications@servantium.com>` with Reply-To `help@servantium.com` unless its notes say otherwise. How to name and format values: [fields.md](./fields.md).

| Alias | Name | Stream | Fields |
|---|---|---|---|
| [`welcome`](#welcome) | Welcome — joining an organization | outbound | 6 |
| [`welcome-organization`](#welcome-organization) | Welcome — new organization | outbound | 5 |
| [`password-reset`](#password-reset) | Password reset | outbound | 2 |
| [`task`](#task) | Task message | outbound | 11 |
| [`notification`](#notification) | Notification | outbound | 9 |
| [`digest`](#digest) | Digest | outbound | 10 |
| [`support-received`](#support-received) | Support — request received | outbound | 4 |
| [`support-reply`](#support-reply) | Support — reply in a conversation | outbound | 7 |
| [`incident`](#incident) | Incident — service disruption | outbound | 10 |
| [`incident-resolved`](#incident-resolved) | Incident — resolved | outbound | 9 |
| [`maintenance`](#maintenance) | Scheduled maintenance | outbound | 9 |
| [`release-notes`](#release-notes) | Release notes | broadcast | 1 |
| [`regulatory-notice`](#regulatory-notice) | Regulatory notice | outbound | 6 |

## welcome

**Welcome — joining an organization** · [`src/emails/welcome.mdx`](../src/emails/welcome.mdx)

Postmark template `welcome`, transactional. Sent when someone adds a person to an existing organization. It is also the invitation: the new account has no password until they set one.

| | |
|---|---|
| Stream | `outbound` |
| Subject | `{{ inviter_name }} added you to {{ organization_name }} on Servantium` |
| Preheader | `Set your password to get started. Your link expires in {{ expires_in }}.` |
| Banner | Welcome · “Welcome to Servantium” · default tone |
| Footer reason | Sent because {{ inviter_name }} added you to {{ organization_name }}. |

| Field | | Note | Example |
|---|---|---|---|
| `first_name` | text | The new user's first name | Jules |
| `inviter_name` | text | The person who added them | Dana Whitfield |
| `organization_name` | text |  | Halcyon Bioanalytical Services |
| `email` | text | The address they'll sign in with | jules.hart@halcyon.example |
| `set_password_url` | text | Firebase Admin SDK generatePasswordResetLink(email) | https://app.servantium.com/__/auth/action?mode=resetPassword&oobCode=Xk2pQ9vLmT7wR4sN8yBc |
| `expires_in` | text | How long that link lives | 72 hours |

## welcome-organization

**Welcome — new organization** · [`src/emails/welcome-organization.mdx`](../src/emails/welcome-organization.mdx)

Postmark template `welcome-organization`, transactional. Sent to the first administrator when a new organization is created. Like `welcome`, it carries the set-password link.

| | |
|---|---|
| Stream | `outbound` |
| Subject | `Your Servantium organization is ready` |
| Preheader | `Set your password, then bring in your team. Your link expires in {{ expires_in }}.` |
| Banner | Welcome · “Welcome to Servantium” · default tone |
| Footer reason | Sent because {{ organization_name }} was set up with you as its administrator. |

| Field | | Note | Example |
|---|---|---|---|
| `first_name` | text | The administrator's first name | Dana |
| `organization_name` | text |  | Halcyon Bioanalytical Services |
| `email` | text | The address they'll sign in with | dana.whitfield@halcyon.example |
| `set_password_url` | text | Firebase Admin SDK generatePasswordResetLink(email) | https://app.servantium.com/__/auth/action?mode=resetPassword&oobCode=Wq8nT2vLkP5zR9sH3yXe |
| `expires_in` | text | How long that link lives | 72 hours |

## password-reset

**Password reset** · [`src/emails/password-reset.mdx`](../src/emails/password-reset.mdx)

Postmark template `password-reset`, transactional, from a backend function that generates the link. Until that exists, Firebase sends it: paste firebase/password-reset.html into Authentication → Templates.

| | |
|---|---|
| Stream | `outbound` |
| Subject | `Reset your Servantium password` |
| Preheader | `This link expires in 1 hour. If you didn't ask for it, you can ignore this email.` |
| Banner | Security · “Reset your password” · default tone |
| Footer reason | Sent because someone asked to reset this account's password. |

| Field | | Note | Example |
|---|---|---|---|
| `email` | text | The account's address. Firebase fills %EMAIL% in its own copy. | jules.hart@halcyon.example |
| `reset_url` | text | Firebase Admin SDK generatePasswordResetLink(email). Firebase fills %LINK% in its own copy. | https://app.servantium.com/__/auth/action?mode=resetPassword&oobCode=Rt5nW2qZc8LmK3vP9xYh |

## task

**Task message** · [`src/emails/task.mdx`](../src/emails/task.mdx)

Postmark template `task`, transactional. Sent to the people on a task when something happens to it: it's assigned, someone comments, a date moves, it's completed. One template for every task event — `action` says which.

| | |
|---|---|
| Stream | `outbound` |
| Subject | `{{ actor_name }} {{ action }}: {{ task_name }}` |
| Preheader | `Due {{ due }} · {{ engagement }}` |
| Banner | Task · “Task update” · default tone |
| Footer reason | Sent because you're on this task in {{ organization_name }}. |

| Field | | Note | Example |
|---|---|---|---|
| `actor_name` | text | Who did it | Jules Hart |
| `action` | text | Lower-case, reads after the name: assigned you · commented on · changed the due date of · completed | assigned you |
| `task_name` | text |  | Clinical sample manifest reconciliation |
| `due` | text | Formatted for the recipient | Fri, Oct 16, 2026 |
| `status` | text | The task's status as the app shows it | Not started |
| `engagement` | text | Engagement code and name | AUR-417 — Phase II Immunogenicity & PK |
| `client` | text |  | Aurora Pharmaceuticals |
| `message` | text, optional | The note or comment that came with the event. Leave it out and the panel doesn't appear. | Please reconcile the Wave 1 manifest against Aurora's forecast before the first PK run.… |
| `task_url` | text |  | https://app.servantium.com/engagements/eng-aur-417/project_plans?task=ppi-manifest |
| `plan_url` | text, optional | Leave it out and the plan link doesn't appear | https://app.servantium.com/engagements/eng-aur-417/project_plans |
| `organization_name` | text |  | Halcyon Bioanalytical Services |

## notification

**Notification** · [`src/emails/notification.mdx`](../src/emails/notification.mdx)

Postmark template `notification`, transactional. The general-purpose notification for everything that isn't a task: approvals, mentions, a quote changing status, a plan being published. One template, many events — the product fills in what happened.

| | |
|---|---|
| Stream | `outbound` |
| Subject | `{{ headline }}` |
| Preheader | `{{ summary }}` |
| Banner | {{ category }} · “An update for you” · default tone |
| Footer reason | {{ reason }} |

| Field | | Note | Example |
|---|---|---|---|
| `category` | text | One or two words for the banner label: Quote · Approval · Mention · Plan | Quote |
| `headline` | text | What happened, in one line. Also the subject. | Dana Whitfield approved the Phase II quote |
| `summary` | text | The line that shows after the subject in the inbox | $184,500 · version 3 · ready to staff |
| `context` | text | Where it happened | AUR-417 · Aurora Pharmaceuticals |
| `message` | text | One or two sentences of detail | Version 3 of the quote is approved. The project plan can now be staffed — the roles bel… |
| `details` | list of { label, value } | Rows for the summary table, as { label, value }. At least one. | 3 items, e.g. Quote · Phase II Immunogenicity & PK · v3 |
| `action_label` | text | The button label, 24 characters or fewer | Open the quote |
| `action_url` | text |  | https://app.servantium.com/engagements/eng-aur-417/quotes/q-3 |
| `reason` | text | Why this person got it, one short sentence starting “Sent because…” | Sent because you lead AUR-417 in Halcyon Bioanalytical Services. |

## digest

**Digest** · [`src/emails/digest.mdx`](../src/emails/digest.mdx)

Postmark template `digest`, transactional. A scheduled job sends it to people who chose a daily or weekly summary instead of an email per event. One email, many updates. Needs notification preferences in the app before it ships.

| | |
|---|---|
| Stream | `outbound` |
| Subject | `{{ summary }}` |
| Preheader | `{{ highlights }}` |
| Banner | {{ period }} · “Here's what changed” · default tone |
| Footer reason | Sent because you chose digest emails in {{ organization_name }}. |

| Field | | Note | Example |
|---|---|---|---|
| `first_name` | text |  | Jules |
| `period` | text | Daily digest or Weekly digest | Daily digest |
| `date_range` | text | The day, or the week (Oct 12–16) | Tuesday, October 13 |
| `organization_name` | text |  | Halcyon Bioanalytical Services |
| `summary` | text | Also the subject | 5 updates in Servantium since yesterday |
| `highlights` | text | The line after the subject in the inbox | 2 tasks assigned to you, a quote approved, and 2 more |
| `items` | list of { category, time, title, context, url } | The updates, newest first, as { category, time, title, context, url }. Ten at most — the rest go in `more`. | 5 items, e.g. Task · 9:14 AM · Jules Hart assigned you “Clinical sample manifest reconciliation” · AU… |
| `more` | text, optional | When there are more than ten. Leave it out otherwise. | and 3 more updates |
| `inbox_url` | text |  | https://app.servantium.com/notifications |
| `preferences_url` | text | Where they change or stop the digest | https://app.servantium.com/settings/notifications |

## support-received

**Support — request received** · [`src/emails/support-received.mdx`](../src/emails/support-received.mdx)

Postmark template `support-received`, transactional. The automatic first reply when a request reaches help@. Set Reply-To to the request's own address (e.g. help+1042@servantium.com) so replies join the right conversation.

| | |
|---|---|
| Stream | `outbound` |
| Subject | `[{{ ticket_id }}] {{ ticket_subject }}` |
| Preheader | `We've got it, and we'll reply {{ reply_by }}.` |
| Banner | Support · “We got your request” · default tone |
| Footer reason | Sent because you wrote to our support team. |

| Field | | Note | Example |
|---|---|---|---|
| `first_name` | text |  | Dana |
| `ticket_id` | text | Our reference | #1042 |
| `ticket_subject` | text | The subject as they wrote it | Quote total doesn't match my spreadsheet |
| `reply_by` | text | Our promise, as policy sets it: “within one business day”, “by Tuesday” | within one business day |

## support-reply

**Support — reply in a conversation** · [`src/emails/support-reply.mdx`](../src/emails/support-reply.mdx)

Postmark template `support-reply`, transactional. Every message from our team on a request: answers, questions back, and the resolution. Keep the same subject, set In-Reply-To and References to the previous message's Message-ID, and set Reply-To to the request's own address, so the whole conversation stays in one thread in their inbox and in ours.

| | |
|---|---|
| Stream | `outbound` |
| Subject | `[{{ ticket_id }}] {{ ticket_subject }}` |
| Preheader | `{{ preview }}` |
| Banner | Support · “A reply from our team” · default tone |
| Footer reason | Sent because you asked us for help ({{ ticket_id }}). |

| Field | | Note | Example |
|---|---|---|---|
| `agent_name` | text | Who on our team wrote this reply | Priya Nair |
| `preview` | text | The reply's first sentence | Thanks for the screenshots — we've found the cause. |
| `reply` | list of { text } | The new message, one item per paragraph, as { text }. Plain text: split on blank lines. | 3 items, e.g. Hi Dana, |
| `status_note` | text, optional | Where things stand, when it helps: “We've marked this resolved. Reply if you need anything else — it reopens automatically.” | We'll keep this open until you confirm. |
| `thread` | list of { author, time, excerpt } | Earlier messages, newest first, as { author, time, excerpt }. Excerpt: the message as one paragraph, 300 characters at most. | 3 items, e.g. Dana Whitfield · Mon, Oct 12 · 4:02 PM · Here are the screenshots. The quote says $184,… |
| `ticket_id` | text |  | #1042 |
| `ticket_subject` | text |  | Quote total doesn't match my spreadsheet |

## incident

**Incident — service disruption** · [`src/emails/incident.mdx`](../src/emails/incident.mdx)

Postmark template `incident`, transactional, to each administrator of an affected organization: when the incident opens and at every status change.

| | |
|---|---|
| Stream | `outbound` |
| Subject | `Service disruption: {{ incident_title }}` |
| Preheader | `{{ status }}. Next update by {{ next_update }}.` |
| Banner | Service status · “Service disruption” · urgent tone |
| Footer reason | Sent to administrators of {{ organization_name }}. |

| Field | | Note | Example |
|---|---|---|---|
| `first_name` | text |  | Dana |
| `organization_name` | text |  | Halcyon Bioanalytical Services |
| `incident_title` | text | What's broken | Quotes and project plans aren't loading |
| `incident_id` | text | Our reference | INC-042 |
| `status` | text | Investigating · Identified · Monitoring | Investigating |
| `started_at` | text |  | Tue, Oct 13, 2026 · 9:12 AM ET |
| `affected` | text |  | Quotes and project plans |
| `next_update` | text |  | 10:00 AM ET |
| `update` | text | The latest update | Some organizations see an error when opening a quote or a project plan. Sign-in and eve… |
| `status_url` | text | The status page entry | https://status.servantium.com/incidents/INC-042 |

## incident-resolved

**Incident — resolved** · [`src/emails/incident-resolved.mdx`](../src/emails/incident-resolved.mdx)

Postmark template `incident-resolved`, transactional, to everyone who received `incident` for the same incident.

| | |
|---|---|
| Stream | `outbound` |
| Subject | `Resolved: {{ incident_title }}` |
| Preheader | `Fixed at {{ resolved_at }}. Everything is working normally.` |
| Banner | Service status · “Issue resolved” · default tone |
| Footer reason | Sent because we emailed you about this incident. |

| Field | | Note | Example |
|---|---|---|---|
| `first_name` | text |  | Dana |
| `incident_title` | text |  | Quotes and project plans weren't loading |
| `incident_id` | text |  | INC-042 |
| `started_at` | text |  | Tue, Oct 13 · 9:12 AM ET |
| `resolved_at` | text |  | Tue, Oct 13 · 10:41 AM ET |
| `duration` | text |  | 1 hour 29 minutes |
| `affected` | text |  | Quotes and project plans |
| `summary` | text |  | A configuration change slowed one of our databases, and requests for quotes and project… |
| `report_url` | text |  | https://status.servantium.com/incidents/INC-042 |

## maintenance

**Scheduled maintenance** · [`src/emails/maintenance.mdx`](../src/emails/maintenance.mdx)

Postmark template `maintenance`, transactional, to every administrator, at least 72 hours before a planned window.

| | |
|---|---|
| Stream | `outbound` |
| Subject | `Scheduled maintenance on {{ date }}` |
| Preheader | `Servantium will be unavailable for up to {{ duration }}, starting {{ starts }}.` |
| Banner | Service status · “Planned maintenance” · attention tone |
| Footer reason | Sent to administrators of {{ organization_name }}. |

| Field | | Note | Example |
|---|---|---|---|
| `first_name` | text |  | Dana |
| `organization_name` | text |  | Halcyon Bioanalytical Services |
| `date` | text |  | Saturday, Oct 24 |
| `starts` | text |  | Sat, Oct 24 · 10:00 PM ET |
| `ends` | text |  | Sun, Oct 25 · 12:00 AM ET |
| `duration` | text |  | 2 hours |
| `reason` | text | Completes “We'll take Servantium offline to …” | upgrade the database that stores quotes and project plans |
| `affected` | text |  | Everything: the web and mobile apps, and API integrations |
| `status_url` | text |  | https://status.servantium.com |

## release-notes

**Release notes** · [`src/emails/release-notes.mdx`](../src/emails/release-notes.mdx)

Postmark template `release-notes`, broadcast stream. Rewritten each month from the help site’s release notes, then sent to active users in batches of 500. Postmark skips anyone who has unsubscribed.

| | |
|---|---|
| Stream | `broadcast` |
| Subject | `What's new in Servantium — June 2026` |
| Preheader | `Secure Search, Contact Workspaces, and 83 more improvements.` |
| Banner | Release notes · “What's new in Servantium” · default tone |
| Footer reason | Sent to Servantium users about product updates. |

| Field | | Note | Example |
|---|---|---|---|
| `first_name` | text | From the user's profile | Jules |

## regulatory-notice

**Regulatory notice** · [`src/emails/regulatory-notice.mdx`](../src/emails/regulatory-notice.mdx)

Postmark template `regulatory-notice`, transactional, one message per organization administrator. The change itself arrives as data (`change_summary`, `change_details`), so the template stays generic and nothing about an upcoming change is written into this public repo. Replies go to help@, which is monitored — the body invites objections by reply. Legal review pending.

| | |
|---|---|
| Stream | `outbound` |
| Subject | `Notice: changes to Servantium's sub-processors, effective {{ effective_date }}` |
| Preheader | `No action is needed. You may object within 30 days under your Data Processing Addendum.` |
| Banner | Service notice · “Sub-processor update” · default tone |
| Footer reason | A required notice for administrators of {{ organization_name }}. |

| Field | | Note | Example |
|---|---|---|---|
| `admin_first_name` | text |  | Dana |
| `organization_name` | text |  | Halcyon Bioanalytical Services |
| `effective_date` | text | At least 30 days after sending | October 24, 2026 |
| `reference` | text | Our reference for this notice | SVC-2026-0917 |
| `change_summary` | text | What's changing, in plain words. Written and approved per notice; never stored in this repo. | We're adding a sub-processor to deliver in-app email notifications, such as task assign… |
| `change_details` | list of { label, value } | The facts of the change as { label, value } rows: sub-processor, purpose, data processed, location. | 4 items, e.g. Sub-processor · Postmark (ActiveCampaign, LLC) |
