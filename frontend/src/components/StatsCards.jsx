import React from 'react';

export default function StatsCards({ stats = {}, documentsCount = 0 }) {
  const critical = stats.critical_alerts || 0;
  const high = stats.high_alerts || 0;
  const openAlerts = stats.open_alerts || 0;
  const totalAlerts = stats.total_alerts || 0;
  const resolved = totalAlerts - openAlerts;

  return (
    <div className="row g-3 mb-4">
      {/* Monitored Documents Card */}
      <div className="col-12 col-sm-6 col-xl-3">
        <div className="card h-100 border-0 shadow-sm border-start border-primary border-4">
          <div className="card-body d-flex align-items-center justify-content-between">
            <div>
              <p className="text-muted small text-uppercase fw-bold mb-1">Monitored Docs</p>
              <h3 className="fw-bold mb-0 text-dark">{documentsCount}</h3>
            </div>
            <div className="bg-primary-subtle text-primary p-3 rounded-circle fs-4">
              <i className="bi bi-file-earmark-text"></i>
            </div>
          </div>
        </div>
      </div>

      {/* Critical Vulnerabilities Card */}
      <div className="col-12 col-sm-6 col-xl-3">
        <div className="card h-100 border-0 shadow-sm border-start border-danger border-4">
          <div className="card-body d-flex align-items-center justify-content-between">
            <div>
              <p className="text-muted small text-uppercase fw-bold mb-1">Critical Exposures</p>
              <h3 className="fw-bold mb-0 text-danger">{critical}</h3>
            </div>
            <div className="bg-danger-subtle text-danger p-3 rounded-circle fs-4">
              <i className="bi bi-exclamation-octagon-fill"></i>
            </div>
          </div>
        </div>
      </div>

      {/* Total Open Vulnerabilities Card */}
      <div className="col-12 col-sm-6 col-xl-3">
        <div className="card h-100 border-0 shadow-sm border-start border-warning border-4">
          <div className="card-body d-flex align-items-center justify-content-between">
            <div>
              <p className="text-muted small text-uppercase fw-bold mb-1">Active Vulnerabilities</p>
              <h3 className="fw-bold mb-0 text-warning-emphasis">{openAlerts}</h3>
            </div>
            <div className="bg-warning-subtle text-warning-emphasis p-3 rounded-circle fs-4">
              <i className="bi bi-shield-exclamation"></i>
            </div>
          </div>
        </div>
      </div>

      {/* Resolved / Remediated Card */}
      <div className="col-12 col-sm-6 col-xl-3">
        <div className="card h-100 border-0 shadow-sm border-start border-success border-4">
          <div className="card-body d-flex align-items-center justify-content-between">
            <div>
              <p className="text-muted small text-uppercase fw-bold mb-1">Resolved Items</p>
              <h3 className="fw-bold mb-0 text-success">{resolved}</h3>
            </div>
            <div className="bg-success-subtle text-success p-3 rounded-circle fs-4">
              <i className="bi bi-check-circle-fill"></i>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
