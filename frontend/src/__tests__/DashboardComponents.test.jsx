import React from 'react';
import { render, screen } from '@testing-library/react';
import StatsCards from '../components/StatsCards';
import DocumentPreview from '../components/DocumentPreview';
import VulnerabilityTable from '../components/VulnerabilityTable';
import AuthModal from '../components/AuthModal';
import SettingsModal from '../components/SettingsModal';

describe('SecureCoda Dashboard Components Unit Tests', () => {
  test('StatsCards renders metric values accurately', () => {
    const stats = {
      critical_alerts: 4,
      high_alerts: 2,
      open_alerts: 10,
      total_alerts: 15,
    };
    render(<StatsCards stats={stats} documentsCount={8} />);

    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  test('DocumentPreview displays documents and vulnerability count badges', () => {
    const mockDocs = [
      {
        id: 'doc-1',
        doc_id: 'doc_payroll_01',
        name: 'Payroll Ledger',
        open_alert_count: 3,
        sharing_mode: 'public',
        days_since_update: 45,
      },
    ];
    render(<DocumentPreview documents={mockDocs} selectedDocId={null} onSelectDoc={() => {}} />);

    expect(screen.getByText('Payroll Ledger')).toBeInTheDocument();
    expect(screen.getByText('3 Vulns')).toBeInTheDocument();
    expect(screen.getByText('public')).toBeInTheDocument();
  });

  test('VulnerabilityTable renders headers, category filter pills and items', () => {
    const mockAlerts = [
      {
        id: 'alt-1',
        title: 'Exposed AWS Key',
        severity: 'critical',
        category: 'sensitive_table',
        status: 'open',
        description: 'sk_live_... exposed',
        document: { name: 'DevOps Secrets', doc_id: 'doc_devops' },
        detected_at: '2026-09-23T10:00:00Z',
      },
    ];
    render(
      <VulnerabilityTable
        alerts={mockAlerts}
        onOpenRemediate={() => {}}
        onUpdateStatus={() => {}}
        selectedCategory={null}
        onSelectCategory={() => {}}
      />
    );

    expect(screen.getByText('Exposed AWS Key')).toBeInTheDocument();
    expect(screen.getByText('critical')).toBeInTheDocument();
    expect(screen.getByText('Resolve')).toBeInTheDocument();
    expect(screen.getByText('Sensitive Table Data')).toBeInTheDocument();
  });

  test('AuthModal renders Sign In, Sign Up, and Google SSO', () => {
    render(<AuthModal show={true} onClose={() => {}} onAuthSuccess={() => {}} />);

    expect(screen.getByText(/Sign in with Google SSO/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Sign In/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Sign Up/i).length).toBeGreaterThan(0);
  });

  test('SettingsModal displays Coda API Key test and Slack Pending Phase 2 badge', () => {
    render(<SettingsModal show={true} onClose={() => {}} onConfigSaved={() => {}} />);

    expect(screen.getByText(/Coda REST API Authentication Key/i)).toBeInTheDocument();
    expect(screen.getByText(/Test Connection/i)).toBeInTheDocument();
    expect(screen.getByText(/Unused Documents Inactivity Timeframe/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Pending \(Phase 2\)/i).length).toBeGreaterThan(0);
  });
});
