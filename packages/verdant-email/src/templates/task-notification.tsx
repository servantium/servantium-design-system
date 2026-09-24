/**
 * Task notification — the workhorse, so it is compact: the slim banner, the task as a data table,
 * the assigner's note, one action. Sample data is the Halcyon demo org's own task #3; assignee,
 * dates, predecessor and note all match the seed, so the email and the demo tell one story.
 */
import { company } from '@servantium/brand';
import { Banner, Body, Email, Footer } from '../components/Layout';
import { Button, Callout, DataTable, Eyebrow, Heading, Link, Spacer, Text } from '../components/Content';
import { defineTemplate } from '../template';

type Props = {
  assignerName: string;
  assignerRole: string;
  taskName: string;
  due: string;
  starts: string;
  engagement: string;
  client: string;
  waitingOn: string;
  note: string;
  taskUrl: string;
  planUrl: string;
  workspaceName: string;
};

export default defineTemplate<Props>({
  id: 'task-notification',
  name: 'Task notification',
  tone: 'activity',
  size: 'compact',
  sendsVia: 'A sender, triggered when a project_plan_items assignee changes',
  sample: {
    assignerName: 'Jules Hart',
    assignerRole: 'Senior Project Manager',
    taskName: 'Clinical sample manifest reconciliation',
    due: 'Fri, Oct 16, 2026',
    starts: 'Thu, Oct 8 · 7 days',
    engagement: 'AUR-417 — Phase II Immunogenicity & PK',
    client: 'Aurora Pharmaceuticals',
    waitingOn: 'Project kickoff & study handoff',
    note: "Please reconcile the Wave 1 manifest against Aurora's forecast before the first PK run. Flag anything outside the 10% tolerance.",
    taskUrl: `${company.urls.app}/engagements/eng-aur-417/project_plans?task=ppi-manifest`,
    planUrl: `${company.urls.app}/engagements/eng-aur-417/project_plans`,
    workspaceName: 'Halcyon Bioanalytical Services',
  },
  placeholders: {
    assignerName: '{{ assigner_name }}', assignerRole: '{{ assigner_role }}', taskName: '{{ task_name }}',
    due: '{{ due }}', starts: '{{ starts }}', engagement: '{{ engagement }}', client: '{{ client }}',
    waitingOn: '{{ waiting_on }}', note: '{{ note }}', taskUrl: '{{ task_url }}', planUrl: '{{ plan_url }}',
    workspaceName: '{{ workspace_name }}',
  },
  build: (p) => ({
    subject: `${p.assignerName} assigned you: ${p.taskName}`,
    preheader: `Due ${p.due} · ${p.engagement}`,
    body: (
      <Email>
        <Banner tone="activity" size="compact" label="Task" />
        <Body>
          <Eyebrow>{p.engagement}</Eyebrow>
          <Heading level={1} margin="0 0 22px">{p.assignerName} assigned you a task</Heading>
          <DataTable title={p.taskName} labelWidth={112} rows={[
            ['Due', <b>{p.due}</b>],
            ['Starts', p.starts],
            ['Engagement', p.engagement],
            ['Client', p.client],
            ['Waiting on', p.waitingOn],
          ]} />
          <Spacer size={16} />
          <Callout tone="notice" title={`${p.assignerName} wrote`}>
            &ldquo;{p.note}&rdquo;
          </Callout>
          <Spacer size={28} />
          <Button href={p.taskUrl} width={180}>Open task</Button>
          <Spacer size={18} />
          <Text size="sm" margin="0"><Link href={p.planUrl}>View the full project plan</Link></Text>
        </Body>
        <Footer reason={`You're receiving this because you're assigned to this task in ${p.workspaceName}.`}
          settingsHref={`${company.urls.app}/profile`} />
      </Email>
    ),
  }),
});
