import React, { useState, useEffect } from 'react';
import ApiClient from '../services/api';

export default function RemediationModal({
  alert,
  show,
  onClose,
  onRemediationSuccess,
  currentUser,
}) {
  const [actions, setActions] = useState([]);
  const [selectedAction, setSelectedAction] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (alert && show) {
      setError('');
      // Load applicable actions for this alert category
      ApiClient.getRemediationActions(alert.category)
        .then((data) => {
          setActions(data);
          if (data && data.length > 0) {
            setSelectedAction(data[0].name);
          }
        })
        .catch((err) => {
          setError('Failed to fetch available remediation actions.');
        });
    }
  }, [alert, show]);

  if (!show || !alert) return null;

  const handleExecute = async () => {
    if (!selectedAction) return;
    setError('');
    setLoading(true);

    try {
      const res = await ApiClient.executeRemediation(alert.id, selectedAction);
      if (res && res.success) {
        onRemediationSuccess(alert.id, res);
        onClose();
      } else {
        setError(res.message || 'Remediation failed.');
      }
    } catch (err) {
      setError(err.message || 'Error executing remediation.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content shadow border-0">
          <div className="modal-header bg-danger text-white">
            <h5 className="modal-title d-flex align-items-center gap-2">
              <i className="bi bi-shield-fill-exclamation"></i>
              <span>Remediate Security Exposure</span>
            </h5>
            <button type="button" className="btn-close btn-close-white" onClick={onClose}></button>
          </div>

          <div className="modal-body p-4">
            {error && <div className="alert alert-danger py-2">{error}</div>}

            <div className="mb-3">
              <label className="form-label text-muted small text-uppercase fw-bold">Target Vulnerability</label>
              <div className="p-3 bg-light rounded border">
                <div className="fw-bold text-dark">{alert.title}</div>
                <div className="small text-muted mb-2">{alert.description}</div>
                <div className="small">
                  <strong>Document:</strong> {alert.document?.name} (<code>{alert.document?.doc_id}</code>)
                </div>
                {alert.metadata?.table_id && (
                  <div className="small">
                    <strong>Table ID:</strong> <code>{alert.metadata.table_id}</code>
                  </div>
                )}
                {alert.metadata?.row_id && (
                  <div className="small">
                    <strong>Row ID:</strong> <code>{alert.metadata.row_id}</code>
                  </div>
                )}
              </div>
            </div>

            <div className="mb-3">
              <label className="form-label text-muted small text-uppercase fw-bold">Select Remediation Action</label>
              <div className="list-group">
                {actions.map((act) => (
                  <label
                    key={act.name}
                    className={`list-group-item list-group-item-action cursor-pointer d-flex gap-3 align-items-start ${
                      selectedAction === act.name ? 'active' : ''
                    }`}
                  >
                    <input
                      type="radio"
                      name="remediationAction"
                      className="form-check-input mt-1"
                      checked={selectedAction === act.name}
                      onChange={() => setSelectedAction(act.name)}
                    />
                    <div>
                      <div className="fw-bold">{act.label}</div>
                      <div className={`small ${selectedAction === act.name ? 'text-white-50' : 'text-muted'}`}>
                        {act.description}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className="alert alert-warning small d-flex align-items-center gap-2 mb-0">
              <i className="bi bi-info-circle-fill fs-5"></i>
              <div>
                Remediation will be executed directly via the Coda REST API.
                An immutable audit trail will log that user <strong>{currentUser?.username || 'anonymous'}</strong> performed this action.
              </div>
            </div>
          </div>

          <div className="modal-footer bg-light">
            <button type="button" className="btn btn-outline-secondary" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button
              type="button"
              className="btn btn-danger d-flex align-items-center gap-2"
              onClick={handleExecute}
              disabled={loading || !selectedAction}
            >
              {loading ? <span className="spinner-border spinner-border-sm"></span> : <i className="bi bi-magic"></i>}
              <span>Execute Remediation</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
