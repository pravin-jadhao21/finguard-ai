import { useState, useEffect } from 'react';
import {
  FlaskConical, Play, CheckCircle2, XCircle, AlertTriangle,
  Search, RefreshCw
} from 'lucide-react';
import {
  runEvaluation, EvalResult
} from '../services/api';

export function EvaluationLab() {
  const [evalResult, setEvalResult] = useState<EvalResult | null>(null);
  const [running, setRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [typeFilter, setTypeFilter] = useState<'ALL' | 'ATTACK' | 'BENIGN'>('ALL');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'PASSED' | 'FAILED'>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const executeEvaluation = async () => {
    setRunning(true);
    setError(null);
    try {
      const res = await runEvaluation();
      setEvalResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to run golden benchmark evaluation.');
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    // Run evaluation automatically on first load to populate data
    executeEvaluation();
  }, []);

  const cases = evalResult?.case_results || [];

  const filteredCases = cases.filter((c) => {
    if (typeFilter === 'ATTACK' && !c.is_attack) return false;
    if (typeFilter === 'BENIGN' && c.is_attack) return false;
    if (statusFilter === 'PASSED' && !c.passed) return false;
    if (statusFilter === 'FAILED' && c.passed) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchCat = c.scenario_category.toLowerCase().includes(q);
      const matchInput = c.input.toLowerCase().includes(q);
      const matchRule = c.matched_rule.toLowerCase().includes(q);
      if (!matchCat && !matchInput && !matchRule) return false;
    }
    return true;
  });

  const summary = evalResult?.summary_metrics;
  const meta = evalResult?.evaluation_metadata;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.45rem', fontWeight: 700, color: '#1e293b', display: 'flex', alignItems: 'center', gap: 8 }}>
            <FlaskConical size={24} color="#2563eb" />
            Evaluation Lab &amp; Golden Benchmark Suite
          </h1>
          <p style={{ margin: '4px 0 0', fontSize: '0.84rem', color: '#64748b' }}>
            Run deterministic benchmark test cases across prompt injection, jailbreaks, PII leakage, and transaction compliance.
          </p>
        </div>

        <button
          onClick={executeEvaluation}
          disabled={running}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '9px 18px',
            borderRadius: 7,
            border: 'none',
            background: '#2563eb',
            color: '#ffffff',
            fontSize: '0.84rem',
            fontWeight: 600,
            cursor: running ? 'not-allowed' : 'pointer',
            boxShadow: '0 1px 3px rgba(37, 99, 235, 0.3)',
          }}
        >
          {running ? <RefreshCw size={15} className="animate-spin" /> : <Play size={15} />}
          {running ? 'Running Benchmark Cases...' : 'Run Benchmark Evaluation'}
        </button>
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

      {/* Benchmark Summary Metrics Cards */}
      {summary && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Top Metrics Row */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: 14,
          }}>
            {/* Overall Pass Rate */}
            <div style={{
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: 10,
              padding: '16px 18px',
              borderLeft: '4px solid #059669',
            }}>
              <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
                Pass Rate
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#059669', marginTop: 4 }}>
                {(summary.overall_pass_rate * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 2 }}>
                {summary.passed_cases} of {summary.total_cases} passed
              </div>
            </div>

            {/* Precision & Recall */}
            <div style={{
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: 10,
              padding: '16px 18px',
              borderLeft: '4px solid #2563eb',
            }}>
              <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
                Precision / Recall
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#1e293b', marginTop: 4 }}>
                {(summary.precision * 100).toFixed(0)}% / {(summary.recall * 100).toFixed(0)}%
              </div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 2 }}>
                F1 Score: {(summary.f1_score * 100).toFixed(1)}%
              </div>
            </div>

            {/* False Positive Rate */}
            <div style={{
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: 10,
              padding: '16px 18px',
              borderLeft: '4px solid #d97706',
            }}>
              <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
                False Positive Rate
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#d97706', marginTop: 4 }}>
                {(summary.false_positive_rate * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 2 }}>
                FNR: {(summary.false_negative_rate * 100).toFixed(1)}%
              </div>
            </div>

            {/* Test Case Split */}
            <div style={{
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: 10,
              padding: '16px 18px',
              borderLeft: '4px solid #9333ea',
            }}>
              <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
                Adversarial vs Benign
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#1e293b', marginTop: 4 }}>
                {summary.attack_cases} / {summary.benign_cases}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 2 }}>
                Total: {summary.total_cases} scenarios
              </div>
            </div>

            {/* Latency */}
            <div style={{
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: 10,
              padding: '16px 18px',
              borderLeft: '4px solid #0284c7',
            }}>
              <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
                Mean Latency
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0284c7', marginTop: 4 }}>
                {summary.mean_latency_ms.toFixed(1)} ms
              </div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 2 }}>
                P95: {summary.p95_latency_ms.toFixed(1)} ms
              </div>
            </div>
          </div>

          {/* Dataset Info Strip */}
          {meta && (
            <div style={{
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: 8,
              padding: '8px 16px',
              display: 'flex',
              gap: 16,
              fontSize: '0.75rem',
              color: '#64748b',
              flexWrap: 'wrap',
            }}>
              <span>Dataset: <strong style={{ color: '#1e293b' }}>{meta.dataset_name}</strong></span>
              <span>Dataset Ver: <strong style={{ color: '#1e293b' }}>v{meta.dataset_version}</strong></span>
              <span>Policy: <strong style={{ color: '#1e293b' }}>{meta.policy_id} (v{meta.policy_version})</strong></span>
              <span>Tested At: <strong style={{ color: '#1e293b' }}>{new Date(meta.timestamp).toLocaleTimeString()}</strong></span>
            </div>
          )}
        </div>
      )}

      {/* Filter and Search Bar */}
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
            placeholder="Search scenario, prompt, matched rule..."
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
          <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 500 }}>Type:</span>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as any)}
            style={{
              padding: '6px 10px',
              borderRadius: 6,
              border: '1px solid #cbd5e1',
              fontSize: '0.8rem',
              background: '#ffffff',
            }}
          >
            <option value="ALL">All Types</option>
            <option value="ATTACK">Adversarial Attacks</option>
            <option value="BENIGN">Benign Requests</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 500 }}>Result:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            style={{
              padding: '6px 10px',
              borderRadius: 6,
              border: '1px solid #cbd5e1',
              fontSize: '0.8rem',
              background: '#ffffff',
            }}
          >
            <option value="ALL">All Outcomes</option>
            <option value="PASSED">Passed Only</option>
            <option value="FAILED">Failed Only</option>
          </select>
        </div>

        <div style={{ marginLeft: 'auto', fontSize: '0.78rem', color: '#94a3b8' }}>
          {filteredCases.length} of {cases.length} Cases
        </div>
      </div>

      {/* Benchmark Case Results List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {filteredCases.length === 0 ? (
          <div style={{
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: 10,
            padding: 36,
            textAlign: 'center',
            color: '#94a3b8',
          }}>
            {running ? 'Running evaluation suite...' : 'No test cases match the filter criteria.'}
          </div>
        ) : (
          filteredCases.map((c) => (
            <div
              key={c.case_id}
              style={{
                background: '#ffffff',
                border: `1px solid ${c.passed ? '#e2e8f0' : '#fecaca'}`,
                borderRadius: 10,
                padding: '14px 18px',
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
                borderLeft: `4px solid ${c.passed ? '#059669' : '#dc2626'}`,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {c.passed ? (
                    <CheckCircle2 size={18} color="#059669" />
                  ) : (
                    <XCircle size={18} color="#dc2626" />
                  )}
                  <span style={{ fontWeight: 700, fontSize: '0.84rem', color: '#1e293b' }}>
                    {c.case_id}: {c.scenario_category}
                  </span>
                  <span style={{
                    padding: '2px 7px',
                    borderRadius: 4,
                    fontSize: '0.7rem',
                    fontWeight: 600,
                    background: c.is_attack ? '#fef2f2' : '#ecfdf5',
                    color: c.is_attack ? '#dc2626' : '#059669',
                  }}>
                    {c.is_attack ? 'Adversarial' : 'Benign'}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                    Latency: <strong>{c.latency_ms?.toFixed(1) || 0} ms</strong>
                  </span>
                  <span style={{
                    padding: '3px 8px',
                    borderRadius: 5,
                    fontSize: '0.74rem',
                    fontWeight: 700,
                    background: c.passed ? '#ecfdf5' : '#fef2f2',
                    color: c.passed ? '#059669' : '#dc2626',
                  }}>
                    {c.passed ? 'PASSED' : 'FAILED'}
                  </span>
                </div>
              </div>

              {/* Input Prompt Box */}
              <div style={{
                background: '#f8fafc',
                padding: '8px 12px',
                borderRadius: 6,
                fontSize: '0.78rem',
                fontFamily: 'monospace',
                color: '#334155',
                border: '1px solid #f1f5f9',
              }}>
                "{c.input}"
              </div>

              {/* Decision Comparison */}
              <div style={{
                display: 'flex',
                gap: 16,
                fontSize: '0.78rem',
                alignItems: 'center',
                flexWrap: 'wrap',
              }}>
                <div>
                  <span style={{ color: '#64748b' }}>Expected: </span>
                  <strong style={{ color: '#1e293b' }}>{c.expected_decision}</strong>
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>Actual: </span>
                  <strong style={{ color: c.passed ? '#059669' : '#dc2626' }}>{c.actual_decision}</strong>
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>Matched Rule: </span>
                  <code style={{ color: '#2563eb', fontWeight: 600 }}>{c.matched_rule || 'NONE'}</code>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
