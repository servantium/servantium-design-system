# Fields: the data an email needs

A **field** is a value the sender supplies when the email goes out: a name, a date, a link. Each master declares its fields in its frontmatter. That list is the contract between this repo and the backend: the backend sends exactly those values, and nothing else is needed to render the email.

## Declaring a field

```yaml
fields:
  first_name: { example: Jules }
  due: { example: "Fri, Oct 16, 2026", note: Formatted for the recipient }
  message: { example: "Flag anything outside tolerance.", optional: true, note: The comment, if there was one }
```

| Key | Required | What it's for |
|---|---|---|
| `example` | yes | A realistic value. It fills the preview gallery and becomes Postmark's test data. It's **never sent**. |
| `note` | no | Guidance for whoever wires the email: the format, where the value comes from, what to leave out. Write one whenever the format matters. |
| `optional` | no | `true` when the email reads fine without the field. Pair it with `<If>` or `<Editable>` in the body. |

`first_name: Jules` is shorthand for `first_name: { example: Jules }`.

## Two kinds of field

**Text.** Almost every field. The value is one string.

**A list of items.** For content whose length varies: the rows of a digest, the paragraphs of a support reply, the earlier messages in a conversation. The example is a list, and each item is a map of text fields:

```yaml
thread:
  note: "Earlier messages, newest first, as { author, time, excerpt }"
  example:
    - { author: Dana Whitfield, time: "Mon, Oct 12 · 4:02 PM", excerpt: "Here are the screenshots…" }
    - { author: Priya Nair, time: "Mon, Oct 12 · 11:30 AM", excerpt: "Could you send a screenshot…" }
```

A list is repeated by a component: `<Updates>`, `<Paragraphs>`, `<Thread>`, or `<DataTable each="…">`. Each component reads fixed item keys, listed in [style-guide.md](./style-guide.md#lists-the-sender-fills), and the build checks the example items supply them.

There are no numbers, booleans or nested objects. Everything arrives as text the sender has already formatted, because Postmark prints values exactly as it receives them.

## Naming

| Rule | Yes | No |
|---|---|---|
| snake_case (the build enforces it) | `task_name` | `taskName`, `Task-Name` |
| Name the thing, not where it sits | `due`, `client` | `row_2_value`, `right_column` |
| Links end in `_url` | `task_url`, `set_password_url` | `link`, `button` |
| People are `_name`; greetings use `first_name` | `actor_name`, `agent_name`, `first_name` | `user`, `person` |
| The tenant is the organization | `organization_name` | `workspace_name`, `tenant`, `company` |
| Reuse a name across emails when it's the same thing | `organization_name` everywhere | `org`, `org_name`, `organisation` |
| References are shown as people see them | `ticket_id: "#1042"`, `incident_id: INC-042` | a database key |

Reusing names matters: the backend can build `organization_name` once and pass it to every email.

## Formatting: the sender formats, the template prints

Postmark can't format anything, so every value arrives ready to read. The backend knows the reader's time zone and locale; the template doesn't.

| Kind | Format | Example |
|---|---|---|
| Date | Weekday, month, day, year, in the reader's time zone | `Fri, Oct 16, 2026` |
| Date and time | Add the time and zone | `Tue, Oct 13, 2026 · 9:12 AM ET` |
| Relative time | Only where it can't go stale, like a digest row | `9:14 AM` |
| Duration | Words | `72 hours`, `within one business day` |
| Money | Currency symbol, thousands separators, no decimals unless they matter | `$184,500` |
| Counts in a sentence | The whole phrase, so plurals are right | `and 3 more updates` |
| Names | As the person wrote them, never upper-cased | `Dana Whitfield` |
| Verbs that follow a name | Lower-case, reads as a sentence | `assigned you`, `commented on` |
| Statuses | As the app shows them | `Not started`, `Investigating` |
| URLs | Absolute `https://`, deep-linked to the exact record | `https://app.servantium.com/engagements/…?task=…` |
| Text a person wrote | Plain text. Several paragraphs → a list of `{ text }`, split on blank lines | see `support-reply` |
| Long text in a list | Trim to the length the note gives | thread excerpts: 300 characters at most |

Values are HTML-escaped by Postmark (`{{ field }}`), so a customer's comment can't inject markup. Never use Postmark's raw form, `{{{ field }}}`. The one exception is Postmark's own unsubscribe link, which the build adds to broadcast mail.

## Where a field can go

| Place | Fields allowed? | Notes |
|---|---|---|
| `subject`, `preheader` | yes | The subject usually carries the event. |
| `label` | yes | Keep the result to 16 characters. `notification` uses `{{ category }}`. |
| `title` | **no** | The banner line is the same on every send, so it always fits one line. |
| `footer.reason`, `footer.settings` | yes | `settings` is a URL. |
| Body text and component props | yes | In a prop, the field is a string: `href="{{ task_url }}"`. |
| Inside `<If field="x">` or `<Editable field="x">` | only `{{ . }}` | Postmark scopes sections: nothing else is visible inside one. |
| Inside a list component | only that item's keys | Also Postmark scoping. |

The build enforces the last two, so an email can't quietly print nothing.

## What the contract becomes

Every build writes the contract from the frontmatter:

**`dist/contract.json`**: for every template alias, its stream (`outbound` or `broadcast`), sender, reply-to, subject, a sentence on when it's sent, and every field with its example, note and whether it's optional.

It's generated. Never edit it; change the master. Engineering can generate whatever types their code needs from it.

## Changing fields safely

A template and the code that sends it change at different times. Postmark prints a missing field as nothing, without an error, and ignores fields it doesn't use. So the order of a change matters more than the change:

| Change | Safe order |
|---|---|
| Add an **optional** field | Anytime. The email reads fine until the backend starts sending it. |
| Add a **required** field | Add it as `optional` first. Once the backend sends it, make it required. |
| **Rename** a field | Add the new name as optional, have the backend send both, then remove the old one. |
| **Remove** a field | Remove it from the master first. The backend can stop sending it afterwards; extra fields are harmless. |
| Change a field's **format** | Update the note, then tell engineering. The build can't see formats. |

Any change to fields shows up in the pull request as a diff to the frontmatter, so engineering can review the contract change directly.
