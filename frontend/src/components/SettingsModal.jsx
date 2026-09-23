import React, { useState, useEffect } from 'react';
import ApiClient from '../services/api';

export default function SettingsModal({ show, onClose, onConfigSaved }) {
  const [codaToken, setCodaToken] = useState('');
  const [maskedToken, setMaskedToken] = useState('');
  const [timeframeValue, setTimeframeValue] = useState(90);
  const [timeframeUnit, setTimeframeUnit] = useState('days');
  const [scanInterval, setScanInterval] = useState(60);
  const [slackChannel, setSlackChannel] = useState('#security-alerts');

  const [loading, setLoading] = useState(false);
  const [validatingToken, setValidatingToken] = useState(false);
  const [tokenStatus, setTokenStatus] = useState(null); // { valid: bool, message: str }
  const [feedback, setFeedback] = useState({ type: '', message: '' });

  useEffect(() => {
    if (show) {
      setFeedback({ type: '', message: '' });
      setTokenStatus(null);
      ApiClient.getConfig()
        .then((cfg) => {
          if (cfg) {
            setMaskedToken(cfg.coda_api_token_masked || '');
            setTimeframeValue(cfg.unused_threshold_value || 90);
            setTimeframeUnit(cfg.unused_threshold_unit || 'days');
            setScanInterval(cfg.scan_interval_minutes || 60);
            setSlackChannel(cfg.slack_channel || '#security-alerts');
          }
        })
        .catch(() => {});
    }
  }, [show]);

  if (!show) return null;

  const handleTestToken = async () => {
    setValidatingToken(true);
    setTokenStatus(null);
    try {
      const res = await ApiClient.validateToken(codaToken);
      setTokenStatus({
        valid: res.valid,
        message: res.message || 'Token is valid!',
      });
    } catch (err) {
      setTokenStatus({
        valid: false,
        message: err.message || 'Token validation failed.',
      });
    } finally {
      setValidatingToken(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    setFeedback({ type: '', message: '' });

    try {
      const payload = {
        unused_threshold_value: parseInt(timeframeValue, 10),
        unused_threshold_unit: timeframeUnit,
        scan_interval_minutes: parseInt(scanInterval, 10),
        slack_channel: slackChannel,
      };

      if (codaToken.trim()) {
        payload.coda_api_token = codaToken.trim();
      }

      const updated = await ApiClient.updateConfig(payload);
      setFeedback({ type: 'success', message: 'Configuration saved successfully!' });
      if (onConfigSaved) onConfigSaved(updated);
      setTimeout(() => {
        onClose();
      }, 900);
    } catch (err) {
      setFeedback({ type: 'danger', message: err.message || 'Failed to update settings.' });
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
              <i className="bi bi-sliders text-warning"></i>
              <span>System & Integration Configuration</span>
            </h5>
            <button type="button" className="btn-close btn-close-white" onClick={onClose}></button>
          </div>

          <form onSubmit={handleSave}>
            <div className="modal-body p-4">
              {feedback.message && (
                <div className={`alert alert-${feedback.type} py-2 d-flex align-items-center gap-2`}>
                  <i className={`bi ${feedback.type === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle'}`}></i>
                  <span>{feedback.message}</span>
                </div>
              )}

              {/* 1. Coda API Authentication Key */}
              <div className="card mb-4 border-light-subtle shadow-sm">
                <div className="card-header bg-light fw-bold d-flex align-items-center gap-2">
                  <i className="bi bi-key-fill text-primary"></i>
                  <span>Coda REST API Authentication Key</span>
                </div>
                <div className="card-body">
                  <p className="text-muted small mb-2">
                    Enter your Coda API bearer token to scan documents, tables, pages, and permissions.
                    The key is securely verified against Coda's <code>/whoami</code> endpoint.
                  </p>

                  <div className="row g-2 align-items-center">
                    <div className="col-12 col-md-8">
                      <input
                        type="password"
                        className="form-control"
                        placeholder={maskedToken ? `Current: ${maskedToken}` : 'Paste Coda API Bearer Token...'}
                        value={codaToken}
                        onChange={(e) => setCodaToken(e.target.value)}
                      />
                    </div>
                    <div className="col-12 col-md-4">
                      <button
                        type="button"
                        className="btn btn-outline-primary w-100 d-flex align-items-center justify-content-center gap-1"
                        onClick={handleTestToken}
                        disabled={validatingToken}
                      >
                        {validatingToken ? (
                          <span className="spinner-border spinner-border-sm"></span>
                        ) : (
                          <i className="bi bi-shield-check"></i>
                        )}
                        <span>Test Connection</span>
                      </button>
                    </div>
                  </div>

                  {tokenStatus && (
                    <div className={`mt-2 small alert ${tokenStatus.valid ? 'alert-success' : 'alert-danger'} py-2 mb-0`}>
                      <i className={`bi ${tokenStatus.valid ? 'bi-check-circle-fill' : 'bi-x-circle-fill'} me-1`}></i>
                      {tokenStatus.message}
                    </div>
                  )}
                </div>
              </div>

              {/* 2. Unused Documents Timeframe Configuration */}
              <div className="card mb-4 border-light-subtle shadow-sm">
                <div className="card-header bg-light fw-bold d-flex align-items-center gap-2">
                  <i className="bi bi-calendar-event text-warning"></i>
                  <span>Unused Documents Inactivity Timeframe</span>
                </div>
                <div className="card-body">
                  <p className="text-muted small mb-3">
                    Configure the threshold after which unaccessed or unmodified Coda documents are flagged as security exposures.
                  </p>

                  <div className="row g-3 align-items-center">
                    <div className="col-12 col-md-6">
                      <label className="form-label small fw-bold">Inactivity Threshold Value</label>
                      <input
                        type="number"
                        min="1"
                        className="form-control"
                        value={timeframeValue}
                        onChange={(e) => setTimeframeValue(e.target.value)}
                        required
                      />
                    </div>

                    <div className="col-12 col-md-6">
                      <label className="form-label small fw-bold">Timeframe Unit</label>
                      <select
                        className="form-select"
                        value={timeframeUnit}
                        onChange={(e) => setTimeframeUnit(e.target.value)}
                      >
                        <option value="days">Days (Standard enterprise policy)</option>
                        <option value="hours">Hours (Fast auditing)</option>
                        <option value="minutes">Minutes (Testing & demo mode)</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              {/* 3. Slack Integration — Phase 2 Pending */}
              <div className="card border-light-subtle shadow-sm bg-light-subtle">
                <div className="card-header bg-light d-flex align-items-center justify-content-between">
                  <div className="fw-bold d-flex align-items-center gap-2">
                    <i className="bi bi-slack text-danger"></i>
                    <span>Slack API Alert Integration</span>
                  </div>
                  <span className="badge bg-warning text-dark border border-warning">
                    <i className="bi bi-hourglass-split me-1"></i>
                    Pending (Phase 2)
                  </span>
                </div>
                <div className="card-body">
                  <p className="text-muted small mb-2">
                    Direct webhook integration to stream critical exposure alerts to designated Slack channels.
                    This module is marked as <strong>Pending (Phase 2)</strong>.
                  </p>
                  <div className="row g-2">
                    <div className="col-12 col-md-6">
                      <label className="form-label small text-muted">Target Slack Channel</label>
                      <input
                        type="text"
                        className="form-control"
                        value={slackChannel}
                        onChange={(e) => setSlackChannel(e.target.value)}
                        disabled
                      />
                    </div>
                    <div className="col-12 col-md-6">
                      <label className="form-label small text-muted">Integration Status</label>
                      <input
                        type="text"
                        className="form-control bg-light"
                        value="Queued for Phase 2 Deployment"
                        disabled
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="modal-footer bg-light">
              <button type="button" className="btn btn-outline-secondary" onClick={onClose} disabled={loading}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary d-flex align-items-center gap-2" disabled={loading}>
                {loading ? <span className="spinner-border spinner-border-sm"></span> : <i className="bi bi-check-lg"></i>}
                <span>Save Settings</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
