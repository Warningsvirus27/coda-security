import React, { useState, useEffect } from 'react';
import ApiClient from '../services/api';

export default function ActivityLogModal({ show, onClose }) {
  const [activeTab, setActiveTab] = useState('userActivities'); // 'userActivities' | 'remediationLogs'
  const [activities, setActivities] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (show) {
      setLoading(true);
      setError('');
      Promise.all([
        ApiClient.getUserActivities().catch(() => ({ results: [] })),
        ApiClient.getAuditLogs().catch(() => ({ results: [] })),
      ])
        .then(([actRes, auditRes]) => {
          setActivities(actRes.results || actRes || []);
          setAuditLogs(auditRes.results || auditRes || []);
        })
        .catch((err) => {
          setError('Failed to fetch activity history.');
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [show]);

  if (!show) return null;

  return (
    <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
        <div className="modal-content shadow border-0">
          <div className="modal-header bg-dark text-white">
            <h5 className="modal-title d-flex align-items-center gap-2">
              <i className="bi bi-journal-text text-warning"></i>
              <span>Audit & User Activity Ledger</span>
            </h5>
            <button type="button" className="btn-close btn-close-white" onClick={onClose}></button>
          </div>

          <div className="modal-body p-4">
            {/* Tabs */}
            <ul className="nav nav-tabs mb-3">
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === 'userActivities' ? 'active fw-bold' : ''}`}
                  onClick={() => setActiveTab('userActivities')}
                >
                  <i className="bi bi-person-lines-fill me-1"></i>
                  User Activities & Changes ({activities.length})
                </button>
              </li>
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === 'remediationLogs' ? 'active fw-bold' : ''}`}
                  onClick={() => setActiveTab('remediationLogs')}
                >
                  <i className="bi bi-shield-check me-1"></i>
                  Vulnerability Remediation Logs ({auditLogs.length})
                </button>
              </li>
            </ul>

            {loading ? (
              <div className="text-center py-5">
                <div className="spinner-border text-primary" role="status"></div>
                <div className="text-muted small mt-2">Loading activity logs...</div>
              </div>
            ) : error ? (
              <div className="alert alert-danger">{error}</div>
            ) : activeTab === 'userActivities' ? (
              <div className="table-responsive">
                <table className="table table-hover table-striped align-middle small mb-0">
                  <thead className="table-light text-muted text-uppercase">
                    <tr>
                      <th>Timestamp</th>
                      <th>User</th>
                      <th>Action</th>
                      <th>Description</th>
                      <th>IP Address</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activities.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="text-center py-4 text-muted">
                          No user activities recorded yet.
                        </td>
                      </tr>
                    ) : (
                      activities.map((act) => (
                        <tr key={act.id}>
                          <td className="text-nowrap text-muted">
                            {act.created_at ? new Date(act.created_at).toLocaleString() : 'N/A'}
                          </td>
                          <td className="fw-semibold">
                            <span className="badge bg-secondary-subtle text-dark border">
                              <i className="bi bi-person me-1"></i>
                              {act.username || 'system'}
                            </span>
                          </td>
                          <td>
                            <span className="badge bg-primary-subtle text-primary border border-primary">
                              {act.action}
                            </span>
                          </td>
                          <td className="text-dark">{act.description}</td>
                          <td className="text-muted font-monospace">{act.ip_address || '127.0.0.1'}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover table-striped align-middle small mb-0">
                  <thead className="table-light text-muted text-uppercase">
                    <tr>
                      <th>Time</th>
                      <th>User / Actor</th>
                      <th>Remediation Action</th>
                      <th>Vulnerability</th>
                      <th>Target Document</th>
                      <th>Result</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLogs.length === 0 ? (
                      <tr>
                        <td colSpan="6" className="text-center py-4 text-muted">
                          No remediation actions taken yet.
                        </td>
                      </tr>
                    ) : (
                      auditLogs.map((log) => (
                        <tr key={log.id}>
                          <td className="text-nowrap text-muted">
                            {log.performed_at ? new Date(log.performed_at).toLocaleString() : 'N/A'}
                          </td>
                          <td className="fw-semibold">
                            <span className="badge bg-secondary-subtle text-dark border">
                              <i className="bi bi-person me-1"></i>
                              {log.user_name || log.performed_by || 'system'}
                            </span>
                          </td>
                          <td>
                            <span className="badge bg-info-subtle text-info-emphasis border">
                              {log.action_type}
                            </span>
                          </td>
                          <td className="fw-semibold text-truncate" style={{ maxWidth: '240px' }} title={log.alert_title}>
                            {log.alert_title || 'Alert'}
                          </td>
                          <td className="text-truncate" style={{ maxWidth: '180px' }} title={log.document_name}>
                            {log.document_name || 'Coda Document'}
                          </td>
                          <td>
                            {log.success ? (
                              <span className="badge bg-success">
                                <i className="bi bi-check-lg me-1"></i> Success
                              </span>
                            ) : (
                              <span className="badge bg-danger" title={log.error_message}>
                                <i className="bi bi-x-circle me-1"></i> Failed
                              </span>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="modal-footer bg-light">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
