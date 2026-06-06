export type OverviewMetric = {
  label: string;
  value: string;
  delta: string;
  tone: 'good' | 'warn' | 'neutral';
};

export type PipelineCard = {
  id: string;
  company: string;
  contact: string;
  value: string;
  priority: 'High' | 'Medium' | 'Low';
};

export type ApprovalItem = {
  id: string;
  sponsor: string;
  subject: string;
  draftType: 'Initial Outreach' | 'Follow-up' | 'Reply Draft';
  queuedAt: string;
};

export const guardrails = [
  'No-send mode: UI placeholders only. No email sending is implemented.',
  'No-spend mode: no paid integrations or transactions.',
  'No-VISION mode: this app is isolated from VISION repos and CRM.'
];

export const overviewMetrics: OverviewMetric[] = [
  { label: 'Leads Found', value: '1,284', delta: '+42 today', tone: 'good' },
  { label: 'Qualified', value: '318', delta: '+19 today', tone: 'good' },
  { label: 'Drafts Ready', value: '47', delta: '+8 today', tone: 'good' },
  { label: 'Approvals Pending', value: '16', delta: '4 aging >24h', tone: 'warn' },
  { label: 'Replies', value: '22', delta: '+6 today', tone: 'good' },
  { label: 'Pipeline Value', value: '$186,500', delta: '+$12,000 this week', tone: 'good' },
  { label: 'Blockers', value: '3', delta: '2 data gaps, 1 legal', tone: 'warn' }
];

export const pipeline: Record<string, PipelineCard[]> = {
  New: [
    { id: 'new-1', company: 'Pulse Hydration', contact: 'Maya Singh', value: '$6,000', priority: 'High' },
    { id: 'new-2', company: 'Aero Threads', contact: 'Leo Martin', value: '$4,000', priority: 'Medium' }
  ],
  Qualified: [
    { id: 'q-1', company: 'Nova Fuel', contact: 'Hana Kim', value: '$12,000', priority: 'High' },
    { id: 'q-2', company: 'Stride Labs', contact: 'Evan Ross', value: '$7,500', priority: 'Medium' }
  ],
  'Needs Enrichment': [
    { id: 'e-1', company: 'Kinetiq', contact: 'Unknown', value: '$5,000', priority: 'Low' }
  ],
  'Draft Ready': [
    { id: 'd-1', company: 'Zephyr Nutrition', contact: 'Nina Brooks', value: '$9,000', priority: 'High' }
  ],
  Approved: [
    { id: 'a-1', company: 'Motion Peak', contact: 'Chris Diaz', value: '$8,500', priority: 'Medium' }
  ],
  Sent: [
    { id: 's-1', company: 'Vanta Water', contact: 'Riley Shaw', value: '$11,000', priority: 'High' }
  ],
  Replied: [
    { id: 'r-1', company: 'ProForm Labs', contact: 'Avery Bell', value: '$13,000', priority: 'High' }
  ],
  Client: [
    { id: 'c-1', company: 'Urban Athlete Co.', contact: 'Jordan Hale', value: '$22,000', priority: 'High' }
  ]
};

export const approvalQueue: ApprovalItem[] = [
  {
    id: 'ap-1',
    sponsor: 'Nova Fuel',
    subject: 'SponsorOS Intro + Audience Fit',
    draftType: 'Initial Outreach',
    queuedAt: '2026-05-13 19:20'
  },
  {
    id: 'ap-2',
    sponsor: 'Stride Labs',
    subject: 'Follow-up with media kit references',
    draftType: 'Follow-up',
    queuedAt: '2026-05-13 18:47'
  },
  {
    id: 'ap-3',
    sponsor: 'ProForm Labs',
    subject: 'Reply draft for budget question',
    draftType: 'Reply Draft',
    queuedAt: '2026-05-13 18:11'
  }
];

export const agents = [
  { name: 'Scout', role: 'Lead discovery and source coverage', status: 'Online' },
  { name: 'Enricher', role: 'Company + contact enrichment', status: 'Online' },
  { name: 'Copywriter', role: 'Draft outreach and follow-ups', status: 'Online' },
  { name: 'Approval Manager', role: 'Gatekeeper for final approvals', status: 'Reviewing' },
  { name: 'Reply Monitor', role: 'Inbound reply classification', status: 'Idle' },
  { name: 'Daily Strategist', role: 'Daily rollups and prioritization', status: 'Online' }
];

export const dailyReport = {
  date: '2026-05-13',
  leadsFound: 42,
  qualified: 19,
  draftsReady: 8,
  approved: 5,
  sent: 0,
  replies: 6,
  topBlocker: 'Missing sponsorship budget ranges from newly found leads',
  note: 'No-send guardrail enforced. All sending actions remain disabled.'
};
