import { useState, useEffect } from 'react';
import {
  ScrollText, RefreshCw, Search, ShieldCheck, CheckCircle2,
  AlertTriangle, Eye, X, Cpu
} from 'lucide-react';
import {
  fetchAuditLogs, explainDecision, AuditLogEntry, DecisionExplanation
} from '../services/api';

export function AuditExplorer() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [decisionFilter, setDecisionFilter] = useState<string>('');
  const [versionFilter, setVersionFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Explain Modal State
  const [selectedExplanation, setSelectedExplanation] = useState<DecisionExplanation | null>(null);
  const [explaining, setExplaining] = useState<boolean>(false);
  const [explainError, setExplainError] = useState<string | null>(null);

  const loadLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAuditLogs({
        decision: decisionFilter || undefined,
        policy_version: versionFilter || undefined,
        limit: 100,
      });
      setLogs(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch audit log entries.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [decisionFilter, versionFilter]);

  const handleExplain = async (requestId: string) => {
    setExplaining(true);
    setExplainError(null);
    setSelectedExplanation(null);
    try {
      const res = await explainDecision(requestId);
      setSelectedExplanation(res);
    } catch (err: any) {
      setExplainError(err.message || 'Failed to fetch decision explainability trace.');
    } finally {
      setExplaining(false);
    }
  };

  const filteredLogs = logs.filter((log) => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchReq = log.request_id.toLowerCase().includes(q);
      const matchReason = log.reason_code.toLowerCase().includes(q);
      const matchRule = log.matched_rule_id?.toLowerCase().includes(q) || false;
      if (!matchReq && !matchReason && !matchRule) return false;
    }
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.45rem', fontWeight: 700, color: '#1e293b', display: 'flex', alignItems: 'center', gap: 8 }}>
            <ScrollText size={24} color="#2563eb" />
            Immutable Audit Explorer &amp; Decision Explainability
          </h1>
          <p style={{ margin: '4px 0 0', fontSize: '0.84rem', color: '#64748b' }}>
            Zero-confidential-payload audit trail with cryptographic request IDs, version traceability, and root-cause explainability.
          </p>
        </div>

        <button
          onClick={loadLogs}
          disabled={loading}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '7px 14px',
            borderRadius: 7,
            border: '1px solid #cbd5e1',
            background: '#ffffff',
            fontSize: '0.8rem',
            fontWeight: 500,
            cursor: loading ? 'not-allowed' : 'pointer',
            color: '#475569',
          }}
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh Logs
        </button>
      </div>

      {/* Security Guarantee Banner */}
      <div style={{
        background: '#f8fafc',
        border: '1px solid #e2e8f0',
        borderRadius: 10,
        padding: '12px 18px',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
      }}>
        <ShieldCheck size={22} color="#059669" style={{ flexShrink: 0 }} />
        <div style={{ fontSize: '0.82rem', color: '#334155' }}>
          <strong>Zero Confidential Data Storage Guarantee:</strong> FinGuard AI audit records store deterministic decision outcomes, matched policy rules, and risk metadata. Raw user prompts, credit card numbers, and banking credentials are never written to the audit log.
        </div>
      </div>

      {error && (
        <div style={{
          padding: '12px 16px',
          borderRadius: 8,
          background: '#fef2f2',
          border: '1px solid #fecaca',
          color: '#991b1b',
          fontSize: '0.84rem',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <AlertTriangle size={16} />
          {error}
        </div>
      )}

      {/* Filters Bar */}
      <div style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: 10,
        padding: '12px 16px',
        display: 'flex',
        gap: 12,
        alignItems: 'center',
        flexWrap: 'wrap',
      }}>
        <div style={{ position: 'relative', flex: '1 1 240px' }}>
          <Search size={15} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
          <input
            type="text"
            placeholder="Search request ID, reason code, matched rule..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '7px 10px 7px 32px',
              borderRadius: 6,
              border: '1px solid #cbd5e1',
              fontSize: '0.82rem',
              outline: 'none',
            }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 500 }}>Decision:</span>
          <select
            value={decisionFilter}
            onChange={(e) => setDecisionFilter(e.target.value)}
            style={{
              padding: '6px 10px',
              borderRadius: 6,
              border: '1px solid #cbd5e1',
              fontSize: '0.8rem',
              background: '#ffffff',
            }}
          >
            <option value="">All Decisions</option>
            <option value="BLOCK">BLOCK</option>
            <option value="ESCALATE">ESCALATE</option>
            <option value="REDIRECT">REDIRECT</option>
            <option value="TOKENIZE">TOKENIZE</option>
            <option value="REDACT">REDACT</option>
            <option value="ALLOW">ALLOW</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 500 }}>Policy Version:</span>
          <input
            type="text"
            placeholder="e.g. 1.0.0"
            value={versionFilter}
            onChange={(e) => setVersionFilter(e.target.value)}
            style={{
              width: 90,
              padding: '6px 10px',
              borderRadius: 6,
              border: '1px solid #cbd5e1',
              fontSize: '0.8rem',
              outline: 'none',
            }}
          />
        </div>

        <div style={{ marginLeft: 'auto', fontSize: '0.78rem', color: '#94a3b8' }}>
          {filteredLogs.length} Records Loaded
        </div>
      </div>

      {/* Logs Table */}
      <div style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: 10,
        overflowX: 'auto',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontWeight: 600 }}>
              <th style={{ padding: '10px 14px' }}>Timestamp</th>
              <th style={{ padding: '10px 14px' }}>Request ID</th>
              <th style={{ padding: '10px 14px' }}>Traffic</th>
              <th style={{ padding: '10px 14px' }}>Policy Version</th>
              <th style={{ padding: '10px 14px' }}>Decision</th>
              <th style={{ padding: '10px 14px' }}>Reason Code</th>
              <th style={{ padding: '10px 14px' }}>Risk Level</th>
              <th style={{ padding: '10px 14px' }}>Latency</th>
              <th style={{ padding: '10px 14px', textAlign: 'center' }}>Explain</th>
            </tr>
          </thead>
          <tbody>
            {filteredLogs.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ padding: 36, textAlign: 'center', color: '#94a3b8' }}>
                  {loading ? 'Loading audit records...' : 'No audit records match the current criteria.'}
                </td>
              </tr>
            ) : (
              filteredLogs.map((log) => (
                <tr key={log.request_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '10px 14px', color: '#64748b', fontSize: '0.76rem', whiteSpace: 'nowrap' }}>
                    {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </td>
                  <td style={{ padding: '10px 14px', fontFamily: 'monospace', fontSize: '0.74rem', color: '#2563eb' }}>
                    {log.request_id.slice(0, 14)}...
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{
                      padding: '2px 6px',
                      borderRadius: 4,
                      fontSize: '0.7rem',
                      fontWeight: 600,
                      background: log.direction === 'INBOUND' ? '#f0f9ff' : '#fdf4ff',
                      color: log.direction === 'INBOUND' ? '#0369a1' : '#7e22ce',
                    }}>
                      {log.direction}
                    </span>
                  </td>
                  <td style={{ padding: '10px 14px', fontFamily: 'monospace', fontSize: '0.76rem', color: '#475569' }}>
                    v{log.policy_version}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <DecisionBadge decision={log.decision} />
                  </td>
                  <td style={{ padding: '10px 14px', fontFamily: 'monospace', fontSize: '0.74rem', color: '#334155' }}>
                    {log.reason_code}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{
                      padding: '2px 7px',
                      borderRadius: 4,
                      fontSize: '0.7rem',
                      fontWeight: 600,
                      background: getRiskBg(log.risk_metadata?.risk_level || 'LOW'),
                      color: getRiskColor(log.risk_metadata?.risk_level || 'LOW'),
                    }}>
                      {log.risk_metadata?.risk_level || 'LOW'} ({log.risk_metadata?.risk_score || 0})
                    </span>
                  </td>
                  <td style={{ padding: '10px 14px', fontSize: '0.76rem', color: '#64748b' }}>
                    {log.latency_ms?.toFixed(1) || 0} ms
                  </td>
                  <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                    <button
                      onClick={() => handleExplain(log.request_id)}
                      style={{
                        padding: '4px 8px',
                        borderRadius: 5,
                        border: '1px solid #cbd5e1',
                        background: '#ffffff',
                        cursor: 'pointer',
                        color: '#2563eb',
                        fontSize: '0.74rem',
                        fontWeight: 600,
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                      }}
                    >
                      <Eye size={12} />
                      Explain
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Decision Explainability Modal / Drawer */}
      {(selectedExplanation || explaining || explainError) && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(15, 23, 42, 0.45)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: 20,
        }}>
          <div style={{
            background: '#ffffff',
            borderRadius: 12,
            maxWidth: 600,
            width: '100%',
            maxHeight: '85vh',
            overflowY: 'auto',
            padding: 24,
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Cpu size={20} color="#2563eb" />
                <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#1e293b' }}>
                  Deterministic Decision Explainability
                </h3>
              </div>
              <button
                onClick={() => setSelectedExplanation(null)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#64748b' }}
              >
                <X size={18} />
              </button>
            </div>

            {explaining && (
              <div style={{ padding: 30, textAlign: 'center', color: '#64748b' }}>
                <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 10px' }} />
                Loading decision explanation...
              </div>
            )}

            {explainError && (
              <div style={{ padding: 16, background: '#fef2f2', borderRadius: 8, color: '#b91c1c', fontSize: '0.84rem' }}>
                {explainError}
              </div>
            )}

            {selectedExplanation && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div style={{
                  padding: 12,
                  borderRadius: 8,
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 10,
                  fontSize: '0.8rem',
                }}>
                  <div>
                    <span style={{ color: '#64748b' }}>Request ID:</span>
                    <div style={{ fontWeight: 600, fontFamily: 'monospace', color: '#1e293b', wordBreak: 'break-all' }}>
                      {selectedExplanation.request_id}
                    </div>
                  </div>
                  <div>
                    <span style={{ color: '#64748b' }}>Traffic Direction:</span>
                    <div style={{ fontWeight: 600, color: '#1e293b' }}>
                      {selectedExplanation.direction}
                    </div>
                  </div>
                  <div>
                    <span style={{ color: '#64748b' }}>Policy Set &amp; Version:</span>
                    <div style={{ fontWeight: 600, color: '#1e293b' }}>
                      {selectedExplanation.policy_id} (v{selectedExplanation.policy_version})
                    </div>
                  </div>
                  <div>
                    <span style={{ color: '#64748b' }}>Gateway Latency:</span>
                    <div style={{ fontWeight: 600, color: '#1e293b' }}>
                      {selectedExplanation.latency_ms?.toFixed(2)} ms
                    </div>
                  </div>
                </div>

                <div style={{
                  padding: 14,
                  borderRadius: 8,
                  background: '#eff6ff',
                  border: '1px solid #bfdbfe',
                }}>
                  <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: '#1d4ed8', fontWeight: 700 }}>
                    Deterministic Outcome
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 4 }}>
                    <DecisionBadge decision={selectedExplanation.decision} />
                    <span style={{ fontFamily: 'monospace', fontWeight: 600, fontSize: '0.85rem', color: '#1e293b' }}>
                      {selectedExplanation.reason_code}
                    </span>
                  </div>
                </div>

                <div>
                  <h4 style={{ margin: '0 0 6px', fontSize: '0.84rem', fontWeight: 600, color: '#334155' }}>
                    Matched Policy Rule ID
                  </h4>
                  <div style={{
                    padding: '8px 12px',
                    borderRadius: 6,
                    background: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    fontFamily: 'monospace',
                    fontSize: '0.82rem',
                    color: '#2563eb',
                    fontWeight: 700,
                  }}>
                    {selectedExplanation.matched_rule_id}
                  </div>
                </div>

                <div>
                  <h4 style={{ margin: '0 0 6px', fontSize: '0.84rem', fontWeight: 600, color: '#334155' }}>
                    Risk Assessment &amp; Triggers
                  </h4>
                  <div style={{
                    padding: '10px 14px',
                    borderRadius: 8,
                    background: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 6,
                    fontSize: '0.8rem',
                  }}>
                    <div>
                      Risk Score: <strong>{selectedExplanation.risk_summary.risk_score}</strong> / 100 &bull; Level: <strong>{selectedExplanation.risk_summary.risk_level}</strong>
                    </div>
                    {selectedExplanation.risk_summary.triggers.length > 0 && (
                      <div>
                        <span style={{ color: '#64748b' }}>Triggers:</span>
                        <ul style={{ margin: '4px 0 0', paddingLeft: 18, color: '#dc2626' }}>
                          {selectedExplanation.risk_summary.triggers.map((t, idx) => (
                            <li key={idx}>{t}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>

                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 12px',
                  borderRadius: 6,
                  background: '#ecfdf5',
                  border: '1px solid #a7f3d0',
                  color: '#065f46',
                  fontSize: '0.76rem',
                }}>
                  <CheckCircle2 size={16} />
                  Zero raw user prompt or confidential payload stored in audit logs.
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
                  <button
                    onClick={() => setSelectedExplanation(null)}
                    style={{
                      padding: '7px 16px',
                      borderRadius: 6,
                      border: '1px solid #cbd5e1',
                      background: '#ffffff',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Close
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function DecisionBadge({ decision }: { decision: string }) {
  const map: Record<string, { bg: string; color: string }> = {
    BLOCK: { bg: '#fef2f2', color: '#dc2626' },
    ESCALATE: { bg: '#fdf4ff', color: '#9333ea' },
    REDIRECT: { bg: '#fffbeb', color: '#d97706' },
    TOKENIZE: { bg: '#f0fdf4', color: '#16a34a' },
    REDACT: { bg: '#f0f9ff', color: '#0284c7' },
    ALLOW: { bg: '#ecfdf5', color: '#059669' },
  };
  const c = map[decision] || { bg: '#f1f5f9', color: '#475569' };
  return (
    <span style={{
      padding: '3px 8px',
      borderRadius: 5,
      fontSize: '0.72rem',
      fontWeight: 700,
      background: c.bg,
      color: c.color,
    }}>
      {decision}
    </span>
  );
}

function getRiskBg(level: string) {
  switch (level) {
    case 'CRITICAL': return '#fef2f2';
    case 'HIGH': return '#fff1f2';
    case 'MEDIUM': return '#fffbeb';
    case 'LOW': default: return '#ecfdf5';
  }
}

function getRiskColor(level: string) {
  switch (level) {
    case 'CRITICAL': return '#dc2626';
    case 'HIGH': return '#e11d48';
    case 'MEDIUM': return '#d97706';
    case 'LOW': default: return '#059669';
  }
}
