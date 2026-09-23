import logging
from django.http import HttpResponse
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers

from .activity_logger import ActivityLogger
from .models import ExportHistory
from .reports import ReportGenerator

logger = logging.getLogger('reports')


class ExportHistorySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default='anonymous')

    class Meta:
        model = ExportHistory
        fields = ['id', 'user', 'username', 'title', 'format', 'options', 'created_at']


class ReportViewSet(viewsets.ViewSet):
    """
    Class-based ViewSet for generating HTML and PDF reports,
    retrieving previous export presets, and re-exporting with previously used options.
    """
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def export(self, request):
        """Generate and download a compliance/exposure report in HTML or PDF format."""
        export_format = request.data.get('format', 'html').lower()
        title = request.data.get('title', 'SecureCoda Security & Exposure Audit Report')
        options = request.data.get('options', {})

        if export_format not in ('html', 'pdf'):
            return Response(
                {'error': 'Invalid format. Supported formats: "html", "pdf".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user if request.user.is_authenticated else None
        history_record = ExportHistory.objects.create(
            user=user,
            title=title,
            format=export_format,
            options=options,
        )

        ActivityLogger.log(
            request=request,
            action='REPORT_EXPORTED',
            description=f"Exported security report in {export_format.upper()} format",
            details={'history_id': str(history_record.id), 'format': export_format, 'options': options},
            user=user,
        )

        if export_format == 'pdf':
            pdf_bytes = ReportGenerator.generate_pdf(options)
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="securecoda-report-{history_record.id}.pdf"'
            return response
        else:
            html_content = ReportGenerator.generate_html(options)
            response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="securecoda-report-{history_record.id}.html"'
            return response

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Returns the list of previously used export configurations."""
        records = ExportHistory.objects.all()[:25]
        serializer = ExportHistorySerializer(records, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='re-export')
    def re_export(self, request, pk=None):
        """Re-exports a report using the exact same options from a previous export."""
        try:
            record = ExportHistory.objects.get(id=pk)
        except ExportHistory.DoesNotExist:
            return Response({'error': 'Export history record not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Allow format override if requested
        export_format = request.data.get('format', record.format).lower()
        options = record.options or {}

        # Log new export
        user = request.user if request.user.is_authenticated else None
        new_record = ExportHistory.objects.create(
            user=user,
            title=f"Re-export: {record.title}",
            format=export_format,
            options=options,
        )

        ActivityLogger.log(
            request=request,
            action='REPORT_RE_EXPORTED',
            description=f"Re-exported report {record.id} with saved options",
            details={'original_id': str(record.id), 'new_id': str(new_record.id), 'format': export_format},
            user=user,
        )

        if export_format == 'pdf':
            pdf_bytes = ReportGenerator.generate_pdf(options)
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="securecoda-report-{new_record.id}.pdf"'
            return response
        else:
            html_content = ReportGenerator.generate_html(options)
            response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="securecoda-report-{new_record.id}.html"'
            return response
