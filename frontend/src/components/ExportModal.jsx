import React, { useState, useEffect } from 'react';
import ApiClient from '../services/api';

export default function ExportModal({ show, onClose, onExportTriggered }) {
  const [format, setFormat] = useState('html'); // 'html' | 'pdf'
  const [category, setCategory] = useState('all');
  const [severity, setSeverity] = useState('all');
  const [includeAudit, setIncludeAudit] = useState(true);
  const [title, setTitle] = useState('SecureCoda Compliance & Exposure Audit');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [activeTab, setActiveTab] = useState('new'); // 'new' | 'history'
  const [feedback, setFeedback] = useState({ type: '', message: '' });

  useEffect(() => {
    if (show) {
      setFeedback({ type: '', message: '' });
      ApiClient.getExportHistory()
        .then((data) => {
          setHistory(data || []);
        })
        .catch(() => {});
    }
  }, [show]);

  if (!show) return null;

  const handleExport = async (e) => {
    e.preventDefault();
    setLoading(true);
    setFeedback({ type: '', message: '' });

    try {
      const options = {
        category,
        severity,
        include_audit_trail: includeAudit,
      };
      await ApiClient.exportReport(format, title, options);
      setFeedback({ type: 'success', message: `${format.toUpperCase()} report generated & downloaded!` });
      if (onExportTriggered) onExportTriggered();
      setTimeout(() => {
        onClose();
      }, 1200);
    } catch (err) {
      setFeedback({ type: 'danger', message: err.message || 'Export failed.' });
    } finally {
      setLoading(false);
    }
  };

  const handleReExport = async (historyId, histFormat) => {
    setLoading(true);
    try {
      await ApiClient.reExport(historyId, histFormat);
      setFeedback({ type: 'success', message: `Report re-exported with previous options!` });
      setTimeout(() => {
        onClose();
      }, 1200);
    } catch (err) {
      setFeedback({ type: 'danger', message: err.message || 'Re-export failed.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-lg modal-dialog-centered">
        <div className="modal-content shadow border-0">
          <div className="modal-header bg-dark text-white">
            <h5 className="modal-title d-flex align-items-center gap-2">
              <i className="bi bi-file-earmark-arrow-down-fill text-warning"></i>
              <span>Export Compliance &amp; Exposure Report</span>
            </h5>
            <button type="button" className="btn-close btn-close-white" onClick={onClose}></button>
          </div>

          <div className="modal-body p-4">
            {feedback.message && (
              <div className={`alert alert-${feedback.type} py-2`}>{feedback.message}</div>
            )}

            {/* Nav Tabs */}
            <ul className="nav nav-pills mb-3">
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === 'new' ? 'active' : ''}`}
                  onClick={() => setActiveTab('new')}
                >
                  <i className="bi bi-plus-circle me-1"></i> New Export
                </button>
              </li>
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === 'history' ? 'active' : ''}`}
                  onClick={() => setActiveTab('history')}
                >
                  <i className="bi bi-clock-history me-1"></i> Previous Export Options ({history.length})
                </button>
              </li>
            </ul>

            {activeTab === 'new' ? (
              <form onSubmit={handleExport}>
                <div className="mb-3">
                  <label className="form-label small fw-bold">Report Title</label>
                  <input
                    type="text"
                    className="form-control"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                  />
                </div>

                <div className="row g-3 mb-3">
                  <div className="col-12 col-md-6">
                    <label className="form-label small fw-bold">Export Format</label>
                    <div className="d-flex gap-3">
                      <div className="form-check">
                        <input
                          className="form-check-input"
                          type="radio"
                          name="reportFormat"
                          id="formatHtml"
                          value="html"
                          checked={format === 'html'}
                          onChange={() => setFormat('html')}
                        />
                        <label className="form-check-label fw-semibold" htmlFor="formatHtml">
                          <i className="bi bi-filetype-html text-primary me-1"></i> HTML (Printable)
                        </label>
                      </div>
                      <div className="form-check">
                        <input
                          className="form-check-input"
                          type="radio"
                          name="reportFormat"
                          id="formatPdf"
                          value="pdf"
                          checked={format === 'pdf'}
                          onChange={() => setFormat('pdf')}
                        />
                        <label className="form-check-label fw-semibold" htmlFor="formatPdf">
                          <i className="bi bi-filetype-pdf text-danger me-1"></i> PDF Document
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="col-12 col-md-6">
                    <label className="form-label small fw-bold">Severity Scope</label>
                    <select
                      className="form-select"
                      value={severity}
                      onChange={(e) => setSeverity(e.target.value)}
                    >
                      <option value="all">All Severities</option>
                      <option value="critical">Critical Only</option>
                      <option value="high">High &amp; Critical</option>
                      <option value="medium">Medium, High &amp; Critical</option>
                    </select>
                  </div>
                </div>

                <div className="row g-3 mb-3">
                  <div className="col-12 col-md-6">
                    <label className="form-label small fw-bold">Category Scope</label>
                    <select
                      className="form-select"
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                    >
                      <option value="all">All Vulnerability Categories</option>
                      <option value="sensitive_table">Sensitive Table Data</option>
                      <option value="sensitive_page">Sensitive Page Data</option>
                      <option value="public_sharing">Public Sharing</option>
                      <option value="unused_doc">Unused Documents</option>
                    </select>
                  </div>

                  <div className="col-12 col-md-6 d-flex align-items-center">
                    <div className="form-check mt-3">
                      <input
                        className="form-check-input"
                        type="checkbox"
                        id="checkAudit"
                        checked={includeAudit}
                        onChange={(e) => setIncludeAudit(e.target.checked)}
                      />
                      <label className="form-check-label small fw-bold" htmlFor="checkAudit">
                        Include Remediation Audit Trail
                      </label>
                    </div>
                  </div>
                </div>

                <div className="modal-footer bg-light px-0 pb-0">
                  <button type="button" className="btn btn-outline-secondary" onClick={onClose} disabled={loading}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary d-flex align-items-center gap-2" disabled={loading}>
                    {loading ? <span className="spinner-border spinner-border-sm"></span> : <i className="bi bi-download"></i>}
                    <span>Generate &amp; Download</span>
                  </button>
                </div>
              </form>
            ) : (
              <div>
                <p className="text-muted small mb-2">
                  Select any previous export configuration to immediately re-run and download:
                </p>
                {history.length === 0 ? (
                  <div className="text-center py-4 text-muted">
                    No export history found yet.
                  </div>
                ) : (
                  <div className="list-group">
                    {history.map((hist) => (
                      <div key={hist.id} className="list-group-item d-flex justify-content-between align-items-center">
                        <div>
                          <div className="fw-bold">{hist.title}</div>
                          <small className="text-muted">
                            Format: <strong>{hist.format.toUpperCase()}</strong> | Date:{' '}
                            {new Date(hist.created_at).toLocaleString()}
                          </small>
                          <div className="small text-muted">
                            Options: {JSON.stringify(hist.options)}
                          </div>
                        </div>
                        <button
                          className="btn btn-sm btn-outline-primary d-flex align-items-center gap-1"
                          onClick={() => handleReExport(hist.id, hist.format)}
                          disabled={loading}
                        >
                          <i className="bi bi-arrow-repeat"></i> Re-Export
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
