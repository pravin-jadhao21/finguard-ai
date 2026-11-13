import { useState, useEffect } from 'react';
import { fetchHealth, HealthResponse } from './services/api';
import { Navbar } from './components/Navbar';
import { PolicyPlayground } from './components/PolicyPlayground';
import { PolicyExplorer } from './components/PolicyExplorer';
import { AuditExplorer } from './components/AuditExplorer';
import { EvaluationLab } from './components/EvaluationLab';
import { HumanReviewQueue } from './components/HumanReviewQueue';

export type ActiveTab = 'playground' | 'policy_explorer' | 'audit' | 'evaluation' | 'review';

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>('playground');

  useEffect(() => {
    const check = async () => {
      try {
        setHealth(await fetchHealth());
      } catch {
        setHealth(null);
      }
    };
    check();
    const t = setInterval(check, 20000);
    return () => clearInterval(t);
  }, []);

  const isHealthy = !!health && health.status === 'healthy';
  const policyVersion = health?.active_policy_version || '-';

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isHealthy={isHealthy}
        policyVersion={policyVersion}
      />

      <main style={{ flex: 1, maxWidth: 1320, width: '100%', margin: '0 auto', padding: '24px 20px' }}>
        {activeTab === 'playground' && <PolicyPlayground />}
        {activeTab === 'policy_explorer' && <PolicyExplorer />}
        {activeTab === 'audit' && <AuditExplorer />}
        {activeTab === 'evaluation' && <EvaluationLab />}
        {activeTab === 'review' && <HumanReviewQueue />}
      </main>

      <footer style={{
        borderTop: '1px solid #e2e8f0',
        padding: '16px 20px',
        textAlign: 'center',
        fontSize: '0.75rem',
        color: '#94a3b8',
        background: '#ffffff',
      }}>
        <strong style={{ color: '#475569' }}>FinGuard AI</strong> — Deterministic Security &amp; Policy Gateway for BFSI Applications
        <span style={{ margin: '0 12px', color: '#e2e8f0' }}>|</span>
        Precedence: BLOCK &gt; ESCALATE &gt; REDIRECT &gt; TOKENIZE &gt; REDACT &gt; ALLOW
        <span style={{ margin: '0 12px', color: '#e2e8f0' }}>|</span>
        Local Sandbox Simulation
      </footer>
    </div>
  );
}
