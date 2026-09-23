import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import StatsCards from './components/StatsCards';
import DocumentPreview from './components/DocumentPreview';
import VulnerabilityTable from './components/VulnerabilityTable';
import AuthModal from './components/AuthModal';
import RemediationModal from './components/RemediationModal';
import SettingsModal from './components/SettingsModal';
import ActivityLogModal from './components/ActivityLogModal';
import ExportModal from './components/ExportModal';
import ApiClient from './services/api';
import { useWebSocket } from './hooks/useWebSocket';

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({});
  const [documents, setDocuments] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedDocId, setSelectedDocId] = useState(null);

  const [isScanning, setIsScanning] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // Modals state
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showActivityModal, setShowActivityModal] = useState(false);
  const [remediatingAlert, setRemediatingAlert] = useState(null);
  const [showExportModal, setShowExportModal] = useState(false);

  // Show a temporary banner notification
  const showToast = (message, type = 'success') => {
    setToastMessage({ message, type });
    setTimeout(() => {
      setToastMessage(null);
    }, 4500);
  };

  // Fetch core dashboard data
  const fetchData = useCallback(async () => {
    try {
      const [alertsRes, statsRes, docsRes] = await Promise.all([
        ApiClient.getAlerts({ page_size: 100 }).catch(() => ({ results: [] })),
        ApiClient.getAlertStats().catch(() => ({})),
        ApiClient.getDocuments().catch(() => ({ results: [] })),
      ]);

      setAlerts(alertsRes.results || alertsRes || []);
      setStats(statsRes || {});
      setDocuments(docsRes.results || docsRes || []);
    } catch (err) {
      console.warn('Data fetch error:', err);
    }
  }, []);

  // WebSocket message handler
  const handleWsMessage = useCallback((payload) => {
    if (payload.event === 'ALERT_CREATED' || payload.event === 'new_alert') {
      showToast(`New security exposure detected!`, 'warning');
      fetchData();
    } else if (payload.event === 'ALERT_UPDATED' || payload.event === 'scan_completed') {
      fetchData();
    }
  }, [fetchData]);

  const { connected: wsConnected } = useWebSocket(handleWsMessage);

  // Initial load & dual-mode interval polling (every 20s)
  useEffect(() => {
    ApiClient.getCurrentUser()
      .then((res) => {
        if (res && res.authenticated) {
          setCurrentUser(res.user);
        }
      })
      .catch(() => {});

    fetchData();

    // Dual-mode background polling ensures fresh data without refresh
    const interval = setInterval(() => {
      fetchData();
    }, 20000);

    return () => clearInterval(interval);
  }, [fetchData]);

  // Trigger manual security scan
  const handleTriggerScan = async () => {
    setIsScanning(true);
    try {
      await ApiClient.triggerScan();
      showToast('Security scan initiated. Analyzing documents & exposure...', 'info');
      setTimeout(() => {
        fetchData();
        setIsScanning(false);
        showToast('Security scan completed successfully!', 'success');
      }, 3500);
    } catch (err) {
      setIsScanning(false);
      showToast(err.message || 'Failed to trigger scan.', 'danger');
    }
  };

  // Sync documents
  const handleSyncDocs = async () => {
    setIsSyncing(true);
    try {
      await ApiClient.syncDocuments();
      showToast('Documents sync initiated.', 'info');
      setTimeout(() => {
        fetchData();
        setIsSyncing(false);
        showToast('Coda documents synchronized.', 'success');
      }, 2500);
    } catch (err) {
      setIsSyncing(false);
      showToast(err.message || 'Failed to sync documents.', 'danger');
    }
  };

  // Handle remediation success
  const handleRemediationSuccess = (alertId, result) => {
    showToast(`Remediation executed: ${result.message}`, 'success');
    fetchData();
  };

  // Quick status update (e.g. acknowledge / re-open)
  const handleUpdateStatus = async (alertId, newStatus) => {
    try {
      await ApiClient.updateAlertStatus(alertId, newStatus);
      showToast(`Vulnerability status changed to ${newStatus}.`, 'info');
      fetchData();
    } catch (err) {
      showToast(err.message || 'Failed to update status.', 'danger');
    }
  };

  const handleLogout = async () => {
    try {
      await ApiClient.logout();
      setCurrentUser(null);
      showToast('Signed out successfully.', 'info');
    } catch (err) {
      setCurrentUser(null);
    }
  };

  return (
    <div className="d-flex flex-column min-vh-100">
      <Navbar
        user={currentUser}
        onOpenAuth={() => setShowAuthModal(true)}
        onLogout={handleLogout}
        onOpenSettings={() => setShowSettingsModal(true)}
        onOpenActivities={() => setShowActivityModal(true)}
        onTriggerScan={handleTriggerScan}
        isScanning={isScanning}
        wsConnected={wsConnected}
        onOpenExport={() => setShowExportModal(true)}
      />

      {/* Main Container */}
      <main className="container-fluid px-md-4 py-4 flex-grow-1">
        {/* Banner Alert Notification */}
        {toastMessage && (
          <div className={`alert alert-${toastMessage.type} alert-dismissible fade show shadow-sm`} role="alert">
            <i className="bi bi-bell-fill me-2"></i>
            {toastMessage.message}
            <button type="button" className="btn-close" onClick={() => setToastMessage(null)}></button>
          </div>
        )}

        {/* Header Title Bar */}
        <div className="d-flex flex-column flex-md-row align-items-md-center justify-content-between mb-4 pb-2 border-bottom">
          <div>
            <h1 className="h3 fw-bold mb-1">Exposure & Vulnerability Dashboard</h1>
            <p className="text-muted small mb-0">
              Continuous monitoring of Coda documents, public sharing leaks, unused documents, and sensitive PII exposures.
            </p>
          </div>
          <div className="mt-2 mt-md-0 d-flex align-items-center gap-2">
            <span className="small text-muted">
              Auto-refresh: <strong>Active</strong> (Dual WebSocket + Polling)
            </span>
          </div>
        </div>

        {/* 1. Summary Metrics Cards */}
        <StatsCards stats={stats} documentsCount={documents.length} />

        {/* 2. Documents Preview Grid */}
        <DocumentPreview
          documents={documents}
          selectedDocId={selectedDocId}
          onSelectDoc={setSelectedDocId}
          onSyncDocs={handleSyncDocs}
          isSyncing={isSyncing}
        />

        {/* 3. Sortable & Categorized Vulnerability Table */}
        <VulnerabilityTable
          alerts={alerts}
          onOpenRemediate={setRemediatingAlert}
          onUpdateStatus={handleUpdateStatus}
          selectedCategory={selectedCategory}
          onSelectCategory={setSelectedCategory}
          selectedDocId={selectedDocId}
        />
      </main>

      {/* Footer */}
      <footer className="bg-white border-top py-3 text-center text-muted small mt-auto">
        <div className="container-fluid">
          <span>SecureCoda Security Platform &copy; 2026. Metron Labs Assignment.</span>
          <span className="mx-2">&bull;</span>
          <span>Google SSO &amp; Coda REST API Integration</span>
        </div>
      </footer>

      {/* Modals */}
      <AuthModal
        show={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onAuthSuccess={(user) => {
          setCurrentUser(user);
          showToast(`Welcome back, ${user.username || user.email}!`, 'success');
        }}
      />

      <SettingsModal
        show={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        onConfigSaved={() => {
          showToast('Settings saved. Timeframe & token updated.', 'success');
          fetchData();
        }}
      />

      <ActivityLogModal
        show={showActivityModal}
        onClose={() => setShowActivityModal(false)}
      />

      <RemediationModal
        alert={remediatingAlert}
        show={!!remediatingAlert}
        onClose={() => setRemediatingAlert(null)}
        onRemediationSuccess={handleRemediationSuccess}
        currentUser={currentUser}
      />

      <ExportModal
        show={showExportModal}
        onClose={() => setShowExportModal(false)}
        onExportTriggered={() => {
          showToast('Report exported successfully!', 'success');
        }}
      />
    </div>
  );
}
