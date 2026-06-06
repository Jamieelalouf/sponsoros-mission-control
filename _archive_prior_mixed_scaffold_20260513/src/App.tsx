import { useMemo, useState } from 'react';
import {
  agents,
  approvalQueue,
  dailyReport,
  guardrails,
  overviewMetrics,
  pipeline,
  type PipelineCard
} from './data/sponsoros';

type View = 'Dashboard' | 'Agents' | 'Reports' | 'Settings';

const pipelineColumns = ['New', 'Qualified', 'Needs Enrichment', 'Draft Ready', 'Approved', 'Sent', 'Replied', 'Client'];

function App() {
  const [view, setView] = useState<View>('Dashboard');

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="kicker">SponsorOS Mission Control</p>
          <h1>Local-First Sponsorship Command Center</h1>
        </div>
        <div className="status-chip">Mode: Safe / Local / Isolated</div>
      </header>

      <section className="guardrail-banner">
        <strong>Guardrails Active</strong>
        <ul>
          {guardrails.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <nav className="tabs">
        {(['Dashboard', 'Agents', 'Reports', 'Settings'] as View[]).map((item) => (
          <button
            key={item}
            className={view === item ? 'tab active' : 'tab'}
            onClick={() => setView(item)}
            type="button"
          >
            {item}
          </button>
        ))}
      </nav>

      {view === 'Dashboard' && <Dashboard />}
      {view === 'Agents' && <AgentsView />}
      {view === 'Reports' && <ReportsView />}
      {view === 'Settings' && <SettingsView />}
    </div>
  );
}

function Dashboard() {
  return (
    <main className="stack-lg">
      <section className="metrics-grid">
        {overviewMetrics.map((metric) => (
          <article className="card metric" key={metric.label}>
            <p>{metric.label}</p>
            <h3>{metric.value}</h3>
            <span className={`delta ${metric.tone}`}>{metric.delta}</span>
          </article>
        ))}
      </section>

      <section className="stack-sm">
        <div className="section-head">
          <h2>Lead Pipeline</h2>
        </div>
        <div className="kanban-grid">
          {pipelineColumns.map((column) => (
            <div className="kanban-col" key={column}>
              <div className="kanban-head">
                <h3>{column}</h3>
                <span>{pipeline[column]?.length ?? 0}</span>
              </div>
              <div className="stack-sm">
                {(pipeline[column] ?? []).map((item) => (
                  <PipelineItem key={item.id} item={item} />
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="stack-sm">
        <div className="section-head">
          <h2>Approval Queue</h2>
        </div>
        <div className="approval-grid">
          {approvalQueue.map((item) => (
            <article key={item.id} className="card approval-card">
              <h3>{item.sponsor}</h3>
              <p>{item.subject}</p>
              <small>
                {item.draftType} · queued {item.queuedAt}
              </small>
              <div className="actions">
                <button type="button">Approve</button>
                <button type="button">Reject</button>
                <button type="button">Edit</button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

function PipelineItem({ item }: { item: PipelineCard }) {
  return (
    <article className="card pipeline-item">
      <h4>{item.company}</h4>
      <p>{item.contact}</p>
      <div className="row-between">
        <strong>{item.value}</strong>
        <span className={`pill ${item.priority.toLowerCase()}`}>{item.priority}</span>
      </div>
    </article>
  );
}

function AgentsView() {
  return (
    <main className="agents-grid">
      {agents.map((agent) => (
        <article className="card agent-card" key={agent.name}>
          <h3>{agent.name}</h3>
          <p>{agent.role}</p>
          <span className="status-dot">{agent.status}</span>
        </article>
      ))}
    </main>
  );
}

function ReportsView() {
  const conversion = useMemo(() => Math.round((dailyReport.replies / Math.max(dailyReport.qualified, 1)) * 100), []);
  return (
    <main className="reports-grid">
      <article className="card report-main">
        <h2>Daily Rollup · {dailyReport.date}</h2>
        <p>{dailyReport.note}</p>
        <div className="report-stats">
          <div><span>Leads Found</span><strong>{dailyReport.leadsFound}</strong></div>
          <div><span>Qualified</span><strong>{dailyReport.qualified}</strong></div>
          <div><span>Drafts Ready</span><strong>{dailyReport.draftsReady}</strong></div>
          <div><span>Approved</span><strong>{dailyReport.approved}</strong></div>
          <div><span>Sent</span><strong>{dailyReport.sent}</strong></div>
          <div><span>Replies</span><strong>{dailyReport.replies}</strong></div>
        </div>
      </article>
      <article className="card report-side">
        <h3>Health</h3>
        <p>Reply conversion: {conversion}%</p>
        <p>Top blocker: {dailyReport.topBlocker}</p>
      </article>
    </main>
  );
}

function SettingsView() {
  return (
    <main className="settings-grid">
      <article className="card">
        <h3>Operating Gmail</h3>
        <p>sponsorosops@gmail.com</p>
      </article>
      <article className="card">
        <h3>CRM Status</h3>
        <p>Disconnected by design (No-VISION guardrail).</p>
      </article>
      <article className="card">
        <h3>Local Port</h3>
        <p>5320</p>
      </article>
      <article className="card">
        <h3>Guardrails</h3>
        <ul>
          {guardrails.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </article>
    </main>
  );
}

export default App;
