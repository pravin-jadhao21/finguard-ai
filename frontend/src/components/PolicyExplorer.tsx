import { useState, useEffect } from 'react';
import {
  BookOpen, Shield, Code2, CheckCircle2, AlertCircle, RefreshCw,
  Search, SlidersHorizontal, ArrowUpDown, History
} from 'lucide-react';
import {
  fetchPolicies, validatePolicy, applyPolicy, fetchPolicyHistory,
  PolicyDefinitionResponse, PolicyValidationResult, PolicyRule, DecisionType
} from '../services/api';

const PRECEDENCE_MATRIX = [
  { rank: 1, action: 'BLOCK', weight: 100, color: '#dc2626', bg: '#fef2f2', desc: 'Highest precedence — Immediate rejection' },
  { rank: 2, action: 'ESCALATE', weight: 80, color: '#9333ea', bg: '#fdf4ff', desc: 'Routes to human compliance officer' },
  { rank: 3, action: 'REDIRECT', weight: 60, color: '#d97706', bg: '#fffbeb', desc: 'Reroutes to deterministic safe workflow' },
  { rank: 4, action: 'TOKENIZE', weight: 40, color: '#16a34a', bg: '#f0fdf4', desc: 'Replaces sensitive entities with reversible tokens' },
  { rank: 5, action: 'REDACT', weight: 20, color: '#0284c7', bg: '#f0f9ff', desc: 'Masks PII/PCI with [REDACTED_*]' },
  { rank: 6, action: 'ALLOW', weight: 0, color: '#059669', bg: '#ecfdf5', desc: 'Baseline — Request proceeds unchanged' },
];

export function PolicyExplorer() {
  const [activeSubTab, setActiveSubTab] = useState<'rules' | 'editor' | 'history'>('rules');
  const [policy, setPolicy] = useState<PolicyDefinitionResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [actionFilter, setActionFilter] = useState('ALL');

  // YAML Editor State
  const [yamlContent, setYamlContent] = useState('');
  const [validationResult, setValidationResult] = useState<PolicyValidationResult | null>(null);
  const [validating, setValidating] = useState(false);
  const [applying, setApplying] = useState(false);
  const [applyMessage, setApplyMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Version History State
  const [history, setHistory] = useState<Array<{ policy_id: string; version: string; name: string; rules_count: number }>>([]);

  const loadPolicy = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchPolicies();
      setPolicy(data);
      // Pre-fill editor sample if empty
      if (!yamlContent && data) {
        setYamlContent(generateYamlFromPolicy(data));
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch active policy definition.');
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const res = await fetchPolicyHistory();
      setHistory(res.versions || []);
    } catch {
      // Non-critical
    }
  };

  useEffect(() => {
    loadPolicy();
    loadHistory();
  }, []);

  const handleValidate = async () => {
    setValidating(true);
    setValidationResult(null);
    setApplyMessage(null);
    try {
      const res = await validatePolicy(yamlContent);
      setValidationResult(res);
    } catch (err: any) {
      setValidationResult({
        valid: false,
        policy_id: null,
        version: null,
        name: null,
        rules_count: 0,
        errors: [err.message || 'Failed to validate YAML policy'],
      });
    } finally {
      setValidating(false);
    }
  };

  const handleApply = async () => {
    if (!window.confirm('Are you sure you want to apply this policy? This will update the active gateway policy rules.')) {
      return;
    }
    setApplying(true);
    setApplyMessage(null);
    try {
      const res = await applyPolicy(yamlContent);
      setApplyMessage({
        type: 'success',
        text: `Policy v${res.version} applied successfully with ${res.rules_count} active rules!`,
      });
      await loadPolicy();
      await loadHistory();
    } catch (err: any) {
      setApplyMessage({
        type: 'error',
        text: `Failed to apply policy: ${err.message}`,
      });
    } finally {
      setApplying(false);
    }
  };

  const filteredRules = (policy?.rules || []).filter((rule) => {
    if (categoryFilter !== 'ALL' && rule.category !== categoryFilter) return false;
    if (actionFilter !== 'ALL' && rule.action !== actionFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchName = rule.name.toLowerCase().includes(q);
      const matchId = rule.id.toLowerCase().includes(q);
      const matchReason = rule.reason_code.toLowerCase().includes(q);
      if (!matchName && !matchId && !matchReason) return false;
    }
    return true;
  });

  const categories = Array.from(new Set((policy?.rules || []).map((r) => r.category)));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.45rem', fontWeight: 700, color: '#1e293b', display: 'flex', alignItems: 'center', gap: 8 }}>
            <BookOpen size={24} color="#2563eb" />
            Policy Engine &amp; Rule Definition Explorer
          </h1>
          <p style={{ margin: '4px 0 0', fontSize: '0.84rem', color: '#64748b' }}>
            Inspect active versioned rules, review action precedence hierarchy, and author/validate policy configurations.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button
            onClick={loadPolicy}
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
            Refresh
          </button>
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
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {/* Sub-tab Navigation */}
      <div style={{ display: 'flex', gap: 8, borderBottom: '1px solid #e2e8f0', paddingBottom: 8 }}>
        <button
          onClick={() => setActiveSubTab('rules')}
          style={{
            padding: '7px 16px',
            borderRadius: 7,
            border: 'none',
            fontSize: '0.84rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: activeSubTab === 'rules' ? '#eff6ff' : 'transparent',
            color: activeSubTab === 'rules' ? '#2563eb' : '#64748b',
          }}
        >
          <Shield size={15} />
          Configured Rules ({policy?.rules_count || 0})
        </button>
        <button
          onClick={() => setActiveSubTab('editor')}
          style={{
            padding: '7px 16px',
            borderRadius: 7,
            border: 'none',
            fontSize: '0.84rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: activeSubTab === 'editor' ? '#eff6ff' : 'transparent',
            color: activeSubTab === 'editor' ? '#2563eb' : '#64748b',
          }}
        >
          <Code2 size={15} />
          YAML Policy Editor &amp; Validator
        </button>
        <button
          onClick={() => setActiveSubTab('history')}
          style={{
            padding: '7px 16px',
            borderRadius: 7,
            border: 'none',
            fontSize: '0.84rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: activeSubTab === 'history' ? '#eff6ff' : 'transparent',
            color: activeSubTab === 'history' ? '#2563eb' : '#64748b',
          }}
        >
          <History size={15} />
          Version History ({history.length})
        </button>
      </div>

      {/* Policy Metadata Card */}
      {policy && (
        <div style={{
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: 10,
          padding: '16px 20px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 16,
        }}>
          <div>
            <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 600, letterSpacing: '0.04em' }}>
              Active Policy ID
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1e293b', fontFamily: 'monospace', marginTop: 2 }}>
              {policy.policy_id}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 600, letterSpacing: '0.04em' }}>
              Active Version
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#059669', fontFamily: 'monospace', marginTop: 2 }}>
              v{policy.policy_version}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 600, letterSpacing: '0.04em' }}>
              Friendly Name
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 600, color: '#334155', marginTop: 2 }}>
              {policy.name || 'Default Financial Policy'}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 600, letterSpacing: '0.04em' }}>
              Configured Rules
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#2563eb', marginTop: 2 }}>
              {policy.rules_count} Rules Loaded
            </div>
          </div>
        </div>
      )}

      {/* Precedence Matrix Strip */}
      <div style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: 10,
        padding: '14px 18px',
      }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
          <ArrowUpDown size={14} color="#64748b" />
          Deterministic Decision Precedence Matrix (Strictly Ordered)
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {PRECEDENCE_MATRIX.map((p) => (
            <div
              key={p.action}
              style={{
                flex: '1 1 150px',
                padding: '8px 12px',
                borderRadius: 8,
                background: p.bg,
                border: `1px solid ${p.color}30`,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 700, fontSize: '0.78rem', color: p.color }}>
                  {p.rank}. {p.action}
                </span>
                <span style={{ fontSize: '0.7rem', color: p.color, fontWeight: 600, fontFamily: 'monospace' }}>
                  wt {p.weight}
                </span>
              </div>
              <div style={{ fontSize: '0.68rem', color: '#64748b', marginTop: 3 }}>
                {p.desc}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* TAB 1: Configured Rules */}
      {activeSubTab === 'rules' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
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
                placeholder="Search rule ID, name, reason code..."
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
              <SlidersHorizontal size={14} color="#64748b" />
              <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 500 }}>Category:</span>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                style={{
                  padding: '6px 10px',
                  borderRadius: 6,
                  border: '1px solid #cbd5e1',
                  fontSize: '0.8rem',
                  background: '#ffffff',
                }}
              >
                <option value="ALL">All Categories</option>
                {categories.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 500 }}>Action:</span>
              <select
                value={actionFilter}
                onChange={(e) => setActionFilter(e.target.value)}
                style={{
                  padding: '6px 10px',
                  borderRadius: 6,
                  border: '1px solid #cbd5e1',
                  fontSize: '0.8rem',
                  background: '#ffffff',
                }}
              >
                <option value="ALL">All Actions</option>
                <option value="BLOCK">BLOCK</option>
                <option value="ESCALATE">ESCALATE</option>
                <option value="REDIRECT">REDIRECT</option>
                <option value="TOKENIZE">TOKENIZE</option>
                <option value="REDACT">REDACT</option>
                <option value="ALLOW">ALLOW</option>
              </select>
            </div>

            <div style={{ marginLeft: 'auto', fontSize: '0.78rem', color: '#94a3b8' }}>
              Showing {filteredRules.length} of {policy?.rules?.length || 0} rules
            </div>
          </div>

          {/* Rules Table */}
          <div style={{
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: 10,
            overflowX: 'auto',
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontWeight: 600 }}>
                  <th style={{ padding: '10px 14px' }}>Rule ID</th>
                  <th style={{ padding: '10px 14px' }}>Name &amp; Reason</th>
                  <th style={{ padding: '10px 14px' }}>Category</th>
                  <th style={{ padding: '10px 14px' }}>Action</th>
                  <th style={{ padding: '10px 14px' }}>Priority / Weight</th>
                  <th style={{ padding: '10px 14px' }}>Condition / Pattern</th>
                </tr>
              </thead>
              <tbody>
                {filteredRules.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ padding: 32, textAlign: 'center', color: '#94a3b8' }}>
                      No rules matched the selected filters.
                    </td>
                  </tr>
                ) : (
                  filteredRules.map((rule, idx) => (
                    <RuleRow key={rule.id || idx} rule={rule} />
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: YAML Editor & Validator */}
      {activeSubTab === 'editor' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: 10,
            padding: '16px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '0.98rem', fontWeight: 700, color: '#1e293b' }}>
                  Live YAML Policy Definition
                </h3>
                <p style={{ margin: '2px 0 0', fontSize: '0.78rem', color: '#64748b' }}>
                  Modify rules, condition patterns, actions, and priorities. Validate syntax and semantics before applying.
                </p>
              </div>

              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  onClick={handleValidate}
                  disabled={validating}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '8px 16px',
                    borderRadius: 7,
                    border: '1px solid #2563eb',
                    background: '#eff6ff',
                    color: '#2563eb',
                    fontSize: '0.82rem',
                    fontWeight: 600,
                    cursor: validating ? 'not-allowed' : 'pointer',
                  }}
                >
                  <CheckCircle2 size={15} />
                  {validating ? 'Validating...' : 'Validate YAML'}
                </button>
                <button
                  onClick={handleApply}
                  disabled={applying || (validationResult !== null && !validationResult.valid)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '8px 16px',
                    borderRadius: 7,
                    border: 'none',
                    background: '#2563eb',
                    color: '#ffffff',
                    fontSize: '0.82rem',
                    fontWeight: 600,
                    cursor: applying ? 'not-allowed' : 'pointer',
                  }}
                >
                  <RefreshCw size={15} className={applying ? 'animate-spin' : ''} />
                  {applying ? 'Applying...' : 'Apply as Active Policy'}
                </button>
              </div>
            </div>

            {/* Notifications */}
            {applyMessage && (
              <div style={{
                padding: '10px 14px',
                borderRadius: 8,
                background: applyMessage.type === 'success' ? '#ecfdf5' : '#fef2f2',
                border: `1px solid ${applyMessage.type === 'success' ? '#a7f3d0' : '#fecaca'}`,
                color: applyMessage.type === 'success' ? '#065f46' : '#991b1b',
                fontSize: '0.82rem',
                fontWeight: 500,
              }}>
                {applyMessage.text}
              </div>
            )}

            {validationResult && (
              <div style={{
                padding: '12px 16px',
                borderRadius: 8,
                background: validationResult.valid ? '#ecfdf5' : '#fef2f2',
                border: `1px solid ${validationResult.valid ? '#a7f3d0' : '#fecaca'}`,
                fontSize: '0.82rem',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 700, color: validationResult.valid ? '#065f46' : '#991b1b' }}>
                  {validationResult.valid ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
                  {validationResult.valid
                    ? `Validation Passed: Policy '${validationResult.name}' (v${validationResult.version}) has ${validationResult.rules_count} valid rules.`
                    : 'Validation Failed with Errors:'}
                </div>
                {validationResult.errors && validationResult.errors.length > 0 && (
                  <ul style={{ margin: '8px 0 0', paddingLeft: 20, color: '#991b1b' }}>
                    {validationResult.errors.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {/* YAML Code Textarea */}
            <div style={{ border: '1px solid #cbd5e1', borderRadius: 8, overflow: 'hidden' }}>
              <div style={{
                background: '#f8fafc',
                padding: '6px 12px',
                borderBottom: '1px solid #e2e8f0',
                fontSize: '0.74rem',
                color: '#64748b',
                fontFamily: 'monospace',
                display: 'flex',
                justifyContent: 'space-between',
              }}>
                <span>default_policy.yaml</span>
                <span>UTF-8 YAML</span>
              </div>
              <textarea
                value={yamlContent}
                onChange={(e) => setYamlContent(e.target.value)}
                rows={22}
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  padding: 12,
                  fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                  fontSize: '0.82rem',
                  lineHeight: 1.5,
                  border: 'none',
                  outline: 'none',
                  resize: 'vertical',
                  background: '#fafbfc',
                  color: '#1e293b',
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Version History */}
      {activeSubTab === 'history' && (
        <div style={{
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: 10,
          padding: '16px 20px',
        }}>
          <h3 style={{ margin: '0 0 12px', fontSize: '0.98rem', fontWeight: 700, color: '#1e293b' }}>
            Policy Version Transition History
          </h3>
          <p style={{ margin: '0 0 16px', fontSize: '0.8rem', color: '#64748b' }}>
            Immutable audit record of all policy versions applied during the active gateway lifecycle.
          </p>

          {history.length === 0 ? (
            <div style={{ padding: 24, textAlign: 'center', color: '#94a3b8', fontSize: '0.84rem' }}>
              No previous version transitions recorded yet. The gateway is currently running the baseline policy (v{policy?.policy_version || '1.0.0'}).
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {history.map((ver, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '12px 16px',
                    borderRadius: 8,
                    border: '1px solid #e2e8f0',
                    background: '#f8fafc',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#1e293b' }}>
                      {ver.name}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', fontFamily: 'monospace', marginTop: 2 }}>
                      ID: {ver.policy_id} &bull; v{ver.version}
                    </div>
                  </div>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#2563eb' }}>
                    {ver.rules_count} Rules
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function RuleRow({ rule }: { rule: PolicyRule }) {
  const getActionBadge = (action: DecisionType) => {
    const map: Record<string, { bg: string; color: string }> = {
      BLOCK: { bg: '#fef2f2', color: '#dc2626' },
      ESCALATE: { bg: '#fdf4ff', color: '#9333ea' },
      REDIRECT: { bg: '#fffbeb', color: '#d97706' },
      TOKENIZE: { bg: '#f0fdf4', color: '#16a34a' },
      REDACT: { bg: '#f0f9ff', color: '#0284c7' },
      ALLOW: { bg: '#ecfdf5', color: '#059669' },
    };
    const c = map[action] || { bg: '#f1f5f9', color: '#475569' };
    return (
      <span style={{
        padding: '3px 8px',
        borderRadius: 5,
        fontSize: '0.72rem',
        fontWeight: 700,
        background: c.bg,
        color: c.color,
      }}>
        {action}
      </span>
    );
  };

  return (
    <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
      <td style={{ padding: '10px 14px', fontFamily: 'monospace', fontWeight: 700, color: '#2563eb' }}>
        {rule.id}
      </td>
      <td style={{ padding: '10px 14px' }}>
        <div style={{ fontWeight: 600, color: '#1e293b' }}>{rule.name}</div>
        <div style={{ fontSize: '0.72rem', color: '#64748b', fontFamily: 'monospace', marginTop: 2 }}>
          {rule.reason_code}
        </div>
      </td>
      <td style={{ padding: '10px 14px' }}>
        <span style={{
          padding: '2px 7px',
          borderRadius: 4,
          fontSize: '0.72rem',
          fontWeight: 500,
          background: '#f1f5f9',
          color: '#475569',
        }}>
          {rule.category}
        </span>
      </td>
      <td style={{ padding: '10px 14px' }}>
        {getActionBadge(rule.action)}
      </td>
      <td style={{ padding: '10px 14px' }}>
        <div style={{ fontSize: '0.78rem', color: '#334155' }}>
          P: <strong>{rule.priority}</strong> &bull; W: <strong>{rule.weight}</strong>
        </div>
      </td>
      <td style={{ padding: '10px 14px', maxWidth: 300 }}>
        {rule.condition?.pattern ? (
          <code style={{ fontSize: '0.72rem', background: '#f8fafc', padding: '2px 5px', borderRadius: 3, color: '#e11d48' }}>
            {rule.condition.pattern}
          </code>
        ) : rule.condition?.keywords ? (
          <span style={{ fontSize: '0.74rem', color: '#64748b' }}>
            Keywords: {rule.condition.keywords.slice(0, 3).join(', ')}...
          </span>
        ) : rule.condition?.max_amount ? (
          <span style={{ fontSize: '0.74rem', color: '#64748b' }}>
            Amount &gt; ${rule.condition.max_amount}
          </span>
        ) : (
          <span style={{ fontSize: '0.74rem', color: '#94a3b8' }}>Default match</span>
        )}
      </td>
    </tr>
  );
}

function generateYamlFromPolicy(policy: PolicyDefinitionResponse): string {
  const lines: string[] = [
    `policy_id: "${policy.policy_id}"`,
    `version: "${policy.policy_version}"`,
    `name: "${policy.name}"`,
    `description: "${policy.description || ''}"`,
    `default_action: "ALLOW"`,
    `rules:`,
  ];

  for (const r of policy.rules) {
    lines.push(`  - id: "${r.id}"`);
    lines.push(`    name: "${r.name}"`);
    lines.push(`    category: "${r.category}"`);
    lines.push(`    action: "${r.action}"`);
    lines.push(`    priority: ${r.priority}`);
    lines.push(`    weight: ${r.weight}`);
    lines.push(`    reason_code: "${r.reason_code}"`);
    if (r.condition) {
      lines.push(`    condition:`);
      if (r.condition.pattern) {
        lines.push(`      pattern: "${r.condition.pattern.replace(/"/g, '\\"')}"`);
      }
      if (r.condition.keywords) {
        lines.push(`      keywords: [${r.condition.keywords.map((k) => `"${k}"`).join(', ')}]`);
      }
      if (r.condition.max_amount !== undefined && r.condition.max_amount !== null) {
        lines.push(`      max_amount: ${r.condition.max_amount}`);
      }
      if (r.condition.required_role) {
        lines.push(`      required_role: "${r.condition.required_role}"`);
      }
    }
    if (r.redirect_target) {
      lines.push(`    redirect_target: "${r.redirect_target}"`);
    }
  }

  return lines.join('\n');
}
