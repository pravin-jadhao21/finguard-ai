import { useState, useEffect } from 'react';
import {
  Users, CheckCircle2, RefreshCw, UserCheck, AlertTriangle
} from 'lucide-react';
import {
  fetchReviewTickets, transitionTicket, ReviewTicket
} from '../services/api';

export function HumanReviewQueue() {
  const [tickets, setTickets] = useState<ReviewTicket[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('PENDING');

  // Transition form state
  const [activeTicketId, setActiveTicketId] = useState<string | null>(null);
  const [reviewerId, setReviewerId] = useState<string>('compliance_officer_01');
  const [notes, setNotes] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const loadTickets = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchReviewTickets(statusFilter || undefined);
      setTickets(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch review tickets.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTickets();
  }, [statusFilter]);

  const handleTransition = async (ticketId: string, newStatus: 'APPROVED' | 'REJECTED') => {
    if (!reviewerId.trim()) {
      alert('Reviewer ID is required for compliance traceability.');
      return;
    }
    setSubmitting(true);
    setActionSuccess(null);
    try {
      await transitionTicket(ticketId, newStatus, reviewerId.trim(), notes.trim());
      setActionSuccess(`Ticket ${ticketId} successfully transitioned to ${newStatus}.`);
      setActiveTicketId(null);
      setNotes('');
      await loadTickets();
    } catch (err: any) {
      alert(`Failed to transition ticket: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const pendingCount = tickets.filter((t) => t.status === 'PENDING').length;
  const approvedCount = tickets.filter((t) => t.status === 'APPROVED').length;
  const rejectedCount = tickets.filter((t) => t.status === 'REJECTED').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.45rem', fontWeight: 700, color: '#1e293b', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Users size={24} color="#9333ea" />
            Human-in-the-Loop Escalation Review Queue
          </h1>
          <p style={{ margin: '4px 0 0', fontSize: '0.84rem', color: '#64748b' }}>
            Compliance &amp; risk officer workbench for high-value transfers, sensitive overrides, and escalated transactions.
          </p>
        </div>

        <button
          onClick={loadTickets}
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
          Refresh Queue
        </button>
      </div>

      {actionSuccess && (
        <div style={{
          padding: '10px 14px',
          borderRadius: 8,
          background: '#ecfdf5',
          border: '1px solid #a7f3d0',
          color: '#065f46',
          fontSize: '0.82rem',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <CheckCircle2 size={16} />
          {actionSuccess}
        </div>
      )}

      {error && (
        <div style={{
          padding: '10px 14px',
          borderRadius: 8,
          background: '#fef2f2',
          border: '1px solid #fecaca',
          color: '#991b1b',
          fontSize: '0.82rem',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <AlertTriangle size={16} />
          {error}
        </div>
      )}

      {/* Summary KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: 14,
      }}>
        <div style={{
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: 10,
          padding: '14px 18px',
          borderLeft: '4px solid #9333ea',
        }}>
          <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
            Pending Human Review
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#9333ea', marginTop: 4 }}>
            {pendingCount}
          </div>
          <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: 2 }}>
            Awaiting officer sign-off
          </div>
        </div>

        <div style={{
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: 10,
          padding: '14px 18px',
          borderLeft: '4px solid #059669',
        }}>
          <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
            Approved Overrides
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#059669', marginTop: 4 }}>
            {approvedCount}
          </div>
          <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: 2 }}>
            Signed off with audit note
          </div>
        </div>

        <div style={{
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: 10,
          padding: '14px 18px',
          borderLeft: '4px solid #dc2626',
        }}>
          <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
            Rejected Transactions
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#dc2626', marginTop: 4 }}>
            {rejectedCount}
          </div>
          <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: 2 }}>
            Declined by compliance
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: 8, borderBottom: '1px solid #e2e8f0', paddingBottom: 8 }}>
        <button
          onClick={() => setStatusFilter('PENDING')}
          style={{
            padding: '6px 14px',
            borderRadius: 6,
            border: 'none',
            fontSize: '0.82rem',
            fontWeight: 600,
            cursor: 'pointer',
            background: statusFilter === 'PENDING' ? '#fdf4ff' : 'transparent',
            color: statusFilter === 'PENDING' ? '#9333ea' : '#64748b',
          }}
        >
          Pending Review ({pendingCount})
        </button>
        <button
          onClick={() => setStatusFilter('APPROVED')}
          style={{
            padding: '6px 14px',
            borderRadius: 6,
            border: 'none',
            fontSize: '0.82rem',
            fontWeight: 600,
            cursor: 'pointer',
            background: statusFilter === 'APPROVED' ? '#ecfdf5' : 'transparent',
            color: statusFilter === 'APPROVED' ? '#059669' : '#64748b',
          }}
        >
          Approved ({approvedCount})
        </button>
        <button
          onClick={() => setStatusFilter('REJECTED')}
          style={{
            padding: '6px 14px',
            borderRadius: 6,
            border: 'none',
            fontSize: '0.82rem',
            fontWeight: 600,
            cursor: 'pointer',
            background: statusFilter === 'REJECTED' ? '#fef2f2' : 'transparent',
            color: statusFilter === 'REJECTED' ? '#dc2626' : '#64748b',
          }}
        >
          Rejected ({rejectedCount})
        </button>
        <button
          onClick={() => setStatusFilter('')}
          style={{
            padding: '6px 14px',
            borderRadius: 6,
            border: 'none',
            fontSize: '0.82rem',
            fontWeight: 600,
            cursor: 'pointer',
            background: statusFilter === '' ? '#eff6ff' : 'transparent',
            color: statusFilter === '' ? '#2563eb' : '#64748b',
          }}
        >
          All Tickets ({tickets.length})
        </button>
      </div>

      {/* Tickets List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {tickets.length === 0 ? (
          <div style={{
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: 10,
            padding: 36,
            textAlign: 'center',
            color: '#94a3b8',
          }}>
            {loading ? 'Loading queue tickets...' : 'No tickets in the queue matching this status.'}
          </div>
        ) : (
          tickets.map((ticket) => (
            <div
              key={ticket.ticket_id}
              style={{
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: 10,
                padding: '16px 20px',
                display: 'flex',
                flexDirection: 'column',
                gap: 12,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontWeight: 700, fontFamily: 'monospace', fontSize: '0.86rem', color: '#1e293b' }}>
                    {ticket.ticket_id}
                  </span>
                  <StatusBadge status={ticket.status} />
                  <span style={{ fontSize: '0.74rem', color: '#64748b' }}>
                    Req: <code style={{ color: '#2563eb' }}>{ticket.request_id}</code>
                  </span>
                </div>

                <div style={{ fontSize: '0.74rem', color: '#94a3b8' }}>
                  {new Date(ticket.created_at).toLocaleString()}
                </div>
              </div>

              {/* Ticket Details */}
              <div style={{
                background: '#f8fafc',
                padding: '10px 14px',
                borderRadius: 8,
                border: '1px solid #f1f5f9',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: 10,
                fontSize: '0.78rem',
              }}>
                <div>
                  <span style={{ color: '#64748b' }}>Reason Code:</span>
                  <div style={{ fontWeight: 600, color: '#1e293b', fontFamily: 'monospace', marginTop: 2 }}>
                    {ticket.reason_code}
                  </div>
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>Risk Score &amp; Level:</span>
                  <div style={{ fontWeight: 600, color: ticket.risk_score > 60 ? '#dc2626' : '#d97706', marginTop: 2 }}>
                    {ticket.risk_score} / 100 ({ticket.risk_level})
                  </div>
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>Policy Set:</span>
                  <div style={{ fontWeight: 600, color: '#1e293b', marginTop: 2 }}>
                    {ticket.policy_id} (v{ticket.policy_version})
                  </div>
                </div>
                {ticket.reviewer_id && (
                  <div>
                    <span style={{ color: '#64748b' }}>Reviewed By:</span>
                    <div style={{ fontWeight: 600, color: '#059669', marginTop: 2 }}>
                      {ticket.reviewer_id}
                    </div>
                  </div>
                )}
              </div>

              {ticket.reviewer_notes && (
                <div style={{
                  fontSize: '0.78rem',
                  color: '#475569',
                  background: '#f1f5f9',
                  padding: '8px 12px',
                  borderRadius: 6,
                }}>
                  <strong>Officer Notes:</strong> {ticket.reviewer_notes}
                </div>
              )}

              {/* Action Buttons for PENDING */}
              {ticket.status === 'PENDING' && (
                <div style={{
                  marginTop: 4,
                  paddingTop: 10,
                  borderTop: '1px solid #f1f5f9',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 10,
                }}>
                  {activeTicketId === ticket.ticket_id ? (
                    <div style={{
                      background: '#faf5ff',
                      border: '1px solid #e9d5ff',
                      borderRadius: 8,
                      padding: 12,
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 10,
                    }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 10 }}>
                        <div>
                          <label style={{ fontSize: '0.74rem', color: '#6b21a8', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                            Officer ID:
                          </label>
                          <input
                            type="text"
                            value={reviewerId}
                            onChange={(e) => setReviewerId(e.target.value)}
                            style={{
                              width: '100%',
                              boxSizing: 'border-box',
                              padding: '6px 8px',
                              borderRadius: 6,
                              border: '1px solid #d8b4fe',
                              fontSize: '0.8rem',
                            }}
                          />
                        </div>
                        <div>
                          <label style={{ fontSize: '0.74rem', color: '#6b21a8', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                            Compliance Notes (Optional):
                          </label>
                          <input
                            type="text"
                            placeholder="e.g. Verified customer phone confirmation ID #8491"
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            style={{
                              width: '100%',
                              boxSizing: 'border-box',
                              padding: '6px 8px',
                              borderRadius: 6,
                              border: '1px solid #d8b4fe',
                              fontSize: '0.8rem',
                            }}
                          />
                        </div>
                      </div>

                      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                        <button
                          onClick={() => setActiveTicketId(null)}
                          style={{
                            padding: '6px 12px',
                            borderRadius: 6,
                            border: '1px solid #cbd5e1',
                            background: '#ffffff',
                            fontSize: '0.78rem',
                            cursor: 'pointer',
                          }}
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => handleTransition(ticket.ticket_id, 'REJECTED')}
                          disabled={submitting}
                          style={{
                            padding: '6px 14px',
                            borderRadius: 6,
                            border: 'none',
                            background: '#dc2626',
                            color: '#ffffff',
                            fontSize: '0.78rem',
                            fontWeight: 600,
                            cursor: submitting ? 'not-allowed' : 'pointer',
                          }}
                        >
                          Reject Request
                        </button>
                        <button
                          onClick={() => handleTransition(ticket.ticket_id, 'APPROVED')}
                          disabled={submitting}
                          style={{
                            padding: '6px 14px',
                            borderRadius: 6,
                            border: 'none',
                            background: '#059669',
                            color: '#ffffff',
                            fontSize: '0.78rem',
                            fontWeight: 600,
                            cursor: submitting ? 'not-allowed' : 'pointer',
                          }}
                        >
                          Approve Request
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button
                        onClick={() => setActiveTicketId(ticket.ticket_id)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                          padding: '6px 12px',
                          borderRadius: 6,
                          border: '1px solid #9333ea',
                          background: '#fdf4ff',
                          color: '#9333ea',
                          fontSize: '0.78rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        <UserCheck size={14} />
                        Review &amp; Decide Ticket
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { bg: string; color: string }> = {
    PENDING: { bg: '#fdf4ff', color: '#9333ea' },
    APPROVED: { bg: '#ecfdf5', color: '#059669' },
    REJECTED: { bg: '#fef2f2', color: '#dc2626' },
  };
  const c = map[status] || { bg: '#f1f5f9', color: '#475569' };
  return (
    <span style={{
      padding: '2px 8px',
      borderRadius: 5,
      fontSize: '0.72rem',
      fontWeight: 700,
      background: c.bg,
      color: c.color,
    }}>
      {status}
    </span>
  );
}
