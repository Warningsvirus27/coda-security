import React from 'react';

export default function DocumentPreview({
  documents = [],
  selectedDocId,
  onSelectDoc,
  onSyncDocs,
  isSyncing,
}) {
  return (
    <div className="card shadow-sm border-0 mb-4">
      <div className="card-header bg-white py-3 d-flex align-items-center justify-content-between flex-wrap gap-2">
        <div className="d-flex align-items-center gap-2">
          <i className="bi bi-folder2-open text-primary fs-5"></i>
          <h5 className="mb-0 fw-bold">Monitored Coda Documents</h5>
          <span className="badge bg-secondary">{documents.length}</span>
        </div>
        <div className="d-flex gap-2">
          {selectedDocId && (
            <button
              className="btn btn-sm btn-outline-secondary d-flex align-items-center gap-1"
              onClick={() => onSelectDoc(null)}
            >
              <i className="bi bi-x-circle"></i> Clear Doc Filter
            </button>
          )}
          <button
            className="btn btn-sm btn-outline-primary d-flex align-items-center gap-1"
            onClick={onSyncDocs}
            disabled={isSyncing}
          >
            {isSyncing ? (
              <span className="spinner-border spinner-border-sm"></span>
            ) : (
              <i className="bi bi-arrow-repeat"></i>
            )}
            <span>Sync Coda Docs</span>
          </button>
        </div>
      </div>

      <div className="card-body p-3">
        {documents.length === 0 ? (
          <div className="text-center text-muted py-4">
            <i className="bi bi-files fs-1 d-block mb-2"></i>
            <p className="mb-1">No documents synchronized yet.</p>
            <small>Configure your Coda API key in Settings and run a scan to monitor documents.</small>
          </div>
        ) : (
          <div className="row g-3">
            {documents.map((doc) => {
              const isSelected = selectedDocId === doc.doc_id;
              const openCount = doc.open_alert_count || 0;
              const isPublic = doc.sharing_mode === 'public' || doc.is_published;

              return (
                <div key={doc.id || doc.doc_id} className="col-12 col-md-6 col-lg-3">
                  <div
                    className={`card h-100 border p-3 cursor-pointer ${
                      isSelected ? 'border-primary bg-primary-subtle shadow' : 'border-light-subtle shadow-sm'
                    }`}
                    onClick={() => onSelectDoc(isSelected ? null : doc.doc_id)}
                    style={{ transition: 'all 0.2s' }}
                  >
                    <div className="d-flex justify-content-between align-items-start mb-2">
                      <span className="badge bg-dark-subtle text-dark border small text-truncate" style={{ maxWidth: '140px' }}>
                        <i className="bi bi-filetype-doc me-1"></i>
                        {doc.doc_id}
                      </span>
                      <span
                        className={`badge ${
                          openCount > 0 ? 'bg-danger' : 'bg-success'
                        } rounded-pill d-flex align-items-center gap-1`}
                        title={`${openCount} open vulnerabilities in this document`}
                      >
                        <i className="bi bi-shield-fill"></i>
                        {openCount} {openCount === 1 ? 'Vuln' : 'Vulns'}
                      </span>
                    </div>

                    <h6 className="fw-bold text-dark text-truncate mb-2" title={doc.name}>
                      {doc.name}
                    </h6>

                    <div className="small text-muted mb-2">
                      <div>
                        <i className="bi bi-clock me-1"></i>
                        Updated {doc.days_since_update != null ? `${doc.days_since_update}d ago` : 'recently'}
                      </div>
                      <div>
                        <i className="bi bi-people me-1"></i>
                        Sharing: <span className={`badge ${isPublic ? 'bg-danger' : 'bg-secondary'}`}>{doc.sharing_mode}</span>
                      </div>
                    </div>

                    <div className="mt-auto pt-2 border-top d-flex justify-content-between align-items-center">
                      <small className="text-primary fw-semibold">
                        {isSelected ? '✓ Viewing Vulns' : 'Click to inspect'}
                      </small>
                      {doc.browser_link && (
                        <a
                          href={doc.browser_link}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-sm btn-link text-decoration-none p-0 text-muted"
                          onClick={(e) => e.stopPropagation()}
                          title="Open in Coda"
                        >
                          <i className="bi bi-box-arrow-up-right"></i>
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
