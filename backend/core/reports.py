import io
from datetime import datetime
from django.utils import timezone
from .models import Alert, CodaDocument, AuditLog, ScanConfig


class ReportGenerator:
    """
    Class-based Report Generator for SecureCoda.
    Generates enterprise compliance & exposure reports in HTML and PDF formats.
    """

    @classmethod
    def get_report_data(cls, options: dict = None) -> dict:
        options = options or {}
        category = options.get('category')
        severity = options.get('severity')
        include_audit = options.get('include_audit_trail', True)

        alerts_qs = Alert.objects.select_related('document').all()
        if category and category != 'all':
            alerts_qs = alerts_qs.filter(category=category)
        if severity and severity != 'all':
            alerts_qs = alerts_qs.filter(severity=severity)

        documents_qs = CodaDocument.objects.all()
        audit_qs = AuditLog.objects.select_related('alert', 'user').all()[:50] if include_audit else []
        config = ScanConfig.get_config()

        total_alerts = alerts_qs.count()
        critical_count = alerts_qs.filter(severity=Alert.Severity.CRITICAL).count()
        high_count = alerts_qs.filter(severity=Alert.Severity.HIGH).count()
        open_count = alerts_qs.filter(status=Alert.Status.OPEN).count()
        resolved_count = alerts_qs.filter(status=Alert.Status.RESOLVED).count()

        return {
            'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'options': options,
            'config': config,
            'total_documents': documents_qs.count(),
            'total_alerts': total_alerts,
            'critical_count': critical_count,
            'high_count': high_count,
            'open_count': open_count,
            'resolved_count': resolved_count,
            'alerts': list(alerts_qs[:100]),
            'documents': list(documents_qs[:50]),
            'audit_logs': list(audit_qs),
        }

    @classmethod
    def generate_html(cls, options: dict = None) -> str:
        data = cls.get_report_data(options)
        alerts_rows = ""
        for a in data['alerts']:
            status_color = "#dc3545" if a.status == "open" else "#198754"
            sev_color = "#dc3545" if a.severity in ("critical", "high") else "#ffc107"
            alerts_rows += f"""
            <tr>
              <td><span style="background:{sev_color}; color:#fff; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:bold;">{a.severity.upper()}</span></td>
              <td><strong>{a.title}</strong><br><small style="color:#6c757d;">{a.description}</small></td>
              <td>{a.category}</td>
              <td>{a.document.name if a.document else 'N/A'}</td>
              <td><span style="color:{status_color}; font-weight:bold;">{a.status.upper()}</span></td>
              <td>{a.detected_at.strftime('%Y-%m-%d') if a.detected_at else ''}</td>
            </tr>
            """

        audit_rows = ""
        for log in data['audit_logs']:
            res_color = "#198754" if log.success else "#dc3545"
            audit_rows += f"""
            <tr>
              <td>{log.performed_at.strftime('%Y-%m-%d %H:%M') if log.performed_at else ''}</td>
              <td><strong>{log.performed_by}</strong></td>
              <td>{log.action_type}</td>
              <td>{log.alert.title if log.alert else ''}</td>
              <td><span style="color:{res_color}; font-weight:bold;">{'SUCCESS' if log.success else 'FAILED'}</span></td>
            </tr>
            """

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>SecureCoda Security & Exposure Audit Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.5; color: #212529; background: #fff; padding: 30px; }}
    .header {{ border-bottom: 2px solid #0d6efd; padding-bottom: 15px; margin-bottom: 25px; }}
    .metrics-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 25px; }}
    .metric-card {{ background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 15px; text-align: center; }}
    .metric-value {{ font-size: 26px; font-weight: bold; margin-top: 5px; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; font-size: 13px; }}
    th, td {{ border: 1px solid #dee2e6; padding: 8px 12px; text-align: left; }}
    th {{ background: #e9ecef; font-weight: 600; text-transform: uppercase; font-size: 11px; }}
    h2 {{ font-size: 18px; margin-top: 25px; margin-bottom: 12px; color: #0d1117; border-left: 4px solid #0d6efd; padding-left: 8px; }}
    .footer {{ margin-top: 40px; border-top: 1px solid #dee2e6; padding-top: 15px; font-size: 12px; color: #6c757d; text-align: center; }}
    @media print {{ body {{ padding: 0; }} }}
  </style>
</head>
<body>
  <div class="header">
    <h1 style="margin:0; font-size: 24px; color:#0d6efd;">SecureCoda — Security & Exposure Audit Report</h1>
    <p style="margin:5px 0 0 0; color:#6c757d; font-size: 13px;">
      Generated: {data['generated_at']} | Scope: Monitored Coda Documents & API Exposure
    </p>
  </div>

  <div class="metrics-grid">
    <div class="metric-card">
      <div style="font-size:12px; color:#6c757d; text-transform:uppercase;">Monitored Docs</div>
      <div class="metric-value" style="color:#0d6efd;">{data['total_documents']}</div>
    </div>
    <div class="metric-card">
      <div style="font-size:12px; color:#6c757d; text-transform:uppercase;">Critical Exposures</div>
      <div class="metric-value" style="color:#dc3545;">{data['critical_count']}</div>
    </div>
    <div class="metric-card">
      <div style="font-size:12px; color:#6c757d; text-transform:uppercase;">Active Vulnerabilities</div>
      <div class="metric-value" style="color:#fd7e14;">{data['open_count']}</div>
    </div>
    <div class="metric-card">
      <div style="font-size:12px; color:#6c757d; text-transform:uppercase;">Resolved Items</div>
      <div class="metric-value" style="color:#198754;">{data['resolved_count']}</div>
    </div>
  </div>

  <h2>Active Security Vulnerabilities & Exposures</h2>
  <table>
    <thead>
      <tr>
        <th>Severity</th>
        <th>Vulnerability / Description</th>
        <th>Category</th>
        <th>Document</th>
        <th>Status</th>
        <th>Detected</th>
      </tr>
    </thead>
    <tbody>
      {alerts_rows if alerts_rows else '<tr><td colspan="6" style="text-align:center;">No vulnerabilities matching criteria.</td></tr>'}
    </tbody>
  </table>

  {f'''<h2>Remediation Audit Trail</h2>
  <table>
    <thead>
      <tr>
        <th>Timestamp</th>
        <th>Actor</th>
        <th>Action Type</th>
        <th>Vulnerability</th>
        <th>Result</th>
      </tr>
    </thead>
    <tbody>
      {audit_rows if audit_rows else '<tr><td colspan="5" style="text-align:center;">No remediation actions logged.</td></tr>'}
    </tbody>
  </table>''' if data['audit_logs'] else ''}

  <div class="footer">
    SecureCoda Security Monitoring Engine &copy; {datetime.now().year} Metron Labs. Confidential compliance audit report.
  </div>
</body>
</html>"""
        return html_content

    @classmethod
    def generate_pdf(cls, options: dict = None) -> bytes:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        data = cls.get_report_data(options)
        styles = getSampleStyleSheet()
        elements = []

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0d6efd'),
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#6c757d'),
        )
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#212529'),
            spaceBefore=14,
            spaceAfter=6,
        )
        cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8, leading=10)

        # Title & Subtitle
        elements.append(Paragraph("SecureCoda — Security & Exposure Audit Report", title_style))
        elements.append(Paragraph(f"Generated: {data['generated_at']} | Scope: Monitored Coda Documents", subtitle_style))
        elements.append(Spacer(1, 15))

        # Metrics Summary Table
        metrics_data = [
            ["Monitored Docs", "Critical Exposures", "Active Vulnerabilities", "Resolved Items"],
            [str(data['total_documents']), str(data['critical_count']), str(data['open_count']), str(data['resolved_count'])],
        ]
        metrics_table = Table(metrics_data, colWidths=[130, 130, 130, 130])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, 1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 15))

        # Vulnerabilities Table
        elements.append(Paragraph("Active Security Vulnerabilities & Exposures", heading_style))
        vuln_rows = [["Severity", "Title / Description", "Category", "Document", "Status"]]
        for a in data['alerts'][:30]:
            vuln_rows.append([
                a.severity.upper(),
                Paragraph(f"<b>{a.title}</b><br/>{a.description[:100]}", cell_style),
                a.category,
                Paragraph(a.document.name if a.document else '', cell_style),
                a.status.upper(),
            ])

        vuln_table = Table(vuln_rows, colWidths=[65, 230, 85, 95, 55])
        vuln_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(vuln_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
