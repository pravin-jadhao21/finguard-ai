import { Shield, FlaskConical, BookOpen, ScrollText, Users } from 'lucide-react';
import type { ActiveTab } from '../App';

interface NavbarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  isHealthy: boolean;
  policyVersion: string;
}

const TABS: { id: ActiveTab; label: string; icon: typeof Shield }[] = [
  { id: 'playground', label: 'Policy Playground', icon: Shield },
  { id: 'policy_explorer', label: 'Policy Explorer', icon: BookOpen },
  { id: 'audit', label: 'Audit Explorer', icon: ScrollText },
  { id: 'evaluation', label: 'Evaluation Lab', icon: FlaskConical },
  { id: 'review', label: 'Review Queue', icon: Users },
];

export function Navbar({ activeTab, setActiveTab, isHealthy, policyVersion }: NavbarProps) {
  return (
    <header style={{
      background: '#ffffff',
      borderBottom: '1px solid #e2e8f0',
      position: 'sticky',
      top: 0,
      zIndex: 50,
    }}>
      <div style={{
        maxWidth: 1320,
        margin: '0 auto',
        padding: '0 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: 60,
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 34, height: 34, borderRadius: 8,
            background: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Shield size={18} color="#fff" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1rem', color: '#1e293b', lineHeight: 1.2 }}>
              FinGuard AI
            </div>
            <div style={{ fontSize: '0.68rem', color: '#94a3b8', fontWeight: 500 }}>
              Deterministic Security Gateway
            </div>
          </div>
        </div>

        {/* Tabs */}
        <nav style={{ display: 'flex', gap: 4 }}>
          {TABS.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`tab-btn ${isActive ? 'tab-btn-active' : ''}`}
                style={{ display: 'flex', alignItems: 'center', gap: 5 }}
              >
                <Icon size={15} />
                {tab.label}
              </button>
            );
          })}
        </nav>

        {/* Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: '0.8rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span className={`status-dot ${isHealthy ? 'status-healthy' : 'status-unhealthy'}`} />
            <span style={{ color: isHealthy ? '#059669' : '#dc2626', fontWeight: 600 }}>
              {isHealthy ? 'Healthy' : 'Offline'}
            </span>
          </div>
          <div style={{
            padding: '3px 10px', borderRadius: 6,
            background: '#f1f5f9', fontSize: '0.75rem', fontWeight: 600, color: '#475569',
          }}>
            Policy v{policyVersion}
          </div>
        </div>
      </div>
    </header>
  );
}
