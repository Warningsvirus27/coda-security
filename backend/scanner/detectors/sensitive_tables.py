"""
SecureCoda — Sensitive Data in Tables Detector

Scans table rows across all documents for sensitive information
such as passwords, personal identifiers, or financial data.
"""
import logging
from .base import BaseDetector
from .patterns import scan_text, is_sensitive_column
from scanner.registry import DetectorRegistry

logger = logging.getLogger('scanner')


@DetectorRegistry.register
class SensitiveTablesDetector(BaseDetector):
    name = 'sensitive_tables'
    category = 'sensitive_table'
    description = 'Scans table rows for sensitive data patterns (passwords, SSNs, credit cards, etc.)'

    def detect(self, documents: list, coda_client) -> list[dict]:
        """
        For each document:
        1. List all tables
        2. For each table, list all rows
        3. Scan each cell value against sensitive data patterns
        4. Also flag columns with sensitive-sounding names
        """
        alerts = []

        for doc in documents:
            try:
                tables = coda_client.list_tables(doc.doc_id)
            except Exception as e:
                logger.warning("Could not list tables for doc %s: %s", doc.doc_id, str(e))
                continue

            for table in tables:
                table_id = table.get('id', '')
                table_name = table.get('name', 'Unknown Table')

                logger.debug("Scanning table '%s' in doc '%s'", table_name, doc.name)

                # Check column names for sensitivity indicators
                try:
                    columns = coda_client.list_columns(doc.doc_id, table_id)
                    sensitive_columns = [
                        col for col in columns
                        if is_sensitive_column(col.get('name', ''))
                    ]
                    for col in sensitive_columns:
                        col_name = col.get('name', '')
                        alerts.append(self.create_alert_dict(
                            document=doc,
                            severity='high',
                            title=f'Sensitive column name: "{col_name}" in "{table_name}"',
                            description=(
                                f'Table "{table_name}" in document "{doc.name}" has a column '
                                f'named "{col_name}" which suggests it may contain sensitive data. '
                                f'Review the column contents and consider renaming or removing it.'
                            ),
                            metadata={
                                'table_id': table_id,
                                'table_name': table_name,
                                'column_id': col.get('id', ''),
                                'column_name': col_name,
                                'issue_type': 'sensitive_column_name',
                            },
                            fingerprint_parts=['col', table_id, col.get('id', '')],
                        ))
                except Exception as e:
                    logger.warning("Could not list columns for table %s: %s", table_id, str(e))

                # Scan row values
                try:
                    rows = coda_client.list_rows(doc.doc_id, table_id)
                except Exception as e:
                    logger.warning("Could not list rows for table %s in doc %s: %s",
                                   table_id, doc.doc_id, str(e))
                    continue

                for row in rows:
                    row_id = row.get('id', '')
                    row_name = row.get('name', '')
                    values = row.get('values', {})

                    for col_name, cell_value in values.items():
                        if cell_value is None:
                            continue

                        # Convert to string for scanning
                        cell_str = str(cell_value)
                        if len(cell_str) < 3:
                            continue

                        findings = scan_text(cell_str)
                        for finding in findings:
                            alerts.append(self.create_alert_dict(
                                document=doc,
                                severity=finding['severity'],
                                title=(
                                    f'{finding["description"]} in table "{table_name}", '
                                    f'column "{col_name}"'
                                ),
                                description=(
                                    f'Sensitive data ({finding["description"]}) detected in '
                                    f'table "{table_name}", column "{col_name}", '
                                    f'row "{row_name or row_id}" of document "{doc.name}". '
                                    f'Matched pattern: {finding["pattern_name"]}. '
                                    f'Value preview: {finding["masked_value"]}'
                                ),
                                metadata={
                                    'table_id': table_id,
                                    'table_name': table_name,
                                    'row_id': row_id,
                                    'row_name': row_name,
                                    'column_name': col_name,
                                    'pattern_name': finding['pattern_name'],
                                    'pattern_category': finding['category'],
                                    'masked_value': finding['masked_value'],
                                    'issue_type': 'sensitive_cell_value',
                                },
                                fingerprint_parts=[
                                    'cell', table_id, row_id, col_name,
                                    finding['pattern_name'],
                                ],
                            ))

        logger.info("Sensitive tables detector found %d alerts", len(alerts))
        return alerts
