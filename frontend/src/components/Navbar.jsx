import React from 'react';

export default function Navbar({
  user,
  onOpenAuth,
  onLogout,
  onOpenSettings,
  onOpenActivities,
  onOpenExport,
  onTriggerScan,
  isScanning,
  wsConnected,
}) {
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark sticky-top shadow-sm px-3">
      <div className="container-fluid">
        <span className="navbar-brand d-flex align-items-center gap-2 fw-bold fs-4">
          <i className="bi bi-shield-lock-fill text-warning"></i>
          <span>SecureCoda</span>
          <span className="badge bg-secondary fs-6 fw-normal ms-2">Exposure Monitor</span>
        </span>

        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarContent"
          aria-controls="navbarContent"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className="collapse navbar-collapse" id="navbarContent">
          <div className="d-flex align-items-center gap-2 ms-auto flex-wrap">
            {/* Real-time WebSocket connection status badge */}
            <span
              className={`badge rounded-pill ${wsConnected ? 'bg-success' : 'bg-secondary'}`}
              title={wsConnected ? 'Connected to live WebSocket event stream' : 'Using dual polling mode'}
            >
              <i className="bi bi-broadcast me-1"></i>
              {wsConnected ? 'Live Stream' : 'Live Sync'}
            </span>

            {/* Scan Trigger button */}
            <button
              className="btn btn-outline-warning btn-sm d-flex align-items-center gap-1"
              onClick={onTriggerScan}
              disabled={isScanning}
            >
              {isScanning ? (
                <>
                  <span className="spinner-border spinner-border-sm" role="status"></span>
                  <span>Scanning...</span>
                </>
              ) : (
                <>
                  <i className="bi bi-play-circle-fill"></i>
                  <span>Run Scan</span>
                </>
              )}
            </button>

            {/* Export button */}
            <button
              className="btn btn-outline-info btn-sm d-flex align-items-center gap-1"
              onClick={onOpenExport}
              title="Export HTML or PDF compliance report"
            >
              <i className="bi bi-file-earmark-arrow-down"></i>
              <span>Export Report</span>
            </button>

            {/* Settings button */}
            <button
              className="btn btn-outline-light btn-sm d-flex align-items-center gap-1"
              onClick={onOpenSettings}
            >
              <i className="bi bi-gear-fill"></i>
              <span>Settings</span>
            </button>

            {/* Activity Logs button */}
            <button
              className="btn btn-outline-light btn-sm d-flex align-items-center gap-1"
              onClick={onOpenActivities}
            >
              <i className="bi bi-clock-history"></i>
              <span>Activity Log</span>
            </button>

            {/* User Profile / Auth */}
            {user ? (
              <div className="dropdown">
                <button
                  className="btn btn-primary btn-sm dropdown-toggle d-flex align-items-center gap-1"
                  type="button"
                  id="userDropdown"
                  data-bs-toggle="dropdown"
                  aria-expanded="false"
                >
                  <i className="bi bi-person-circle"></i>
                  <span>{user.username || user.email}</span>
                </button>
                <ul className="dropdown-menu dropdown-menu-end shadow" aria-labelledby="userDropdown">
                  <li className="dropdown-header text-truncate" style={{ maxWidth: '200px' }}>
                    {user.email || user.username}
                  </li>
                  <li><hr className="dropdown-divider" /></li>
                  <li>
                    <button className="dropdown-item text-danger d-flex align-items-center gap-2" onClick={onLogout}>
                      <i className="bi bi-box-arrow-right"></i> Sign Out
                    </button>
                  </li>
                </ul>
              </div>
            ) : (
              <button className="btn btn-primary btn-sm d-flex align-items-center gap-1" onClick={onOpenAuth}>
                <i className="bi bi-box-arrow-in-right"></i>
                <span>Sign In</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
