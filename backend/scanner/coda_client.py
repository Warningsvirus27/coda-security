"""
SecureCoda — Coda REST API Client

A reusable, rate-limit-aware wrapper around the Coda v1 API.
All API calls are logged and include exponential backoff retry logic.
"""
import time
import logging
import requests
from typing import Optional
from django.conf import settings

logger = logging.getLogger('scanner.coda_client')

# Default retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # seconds: 2, 4, 8


class CodaAPIError(Exception):
    """Raised when a Coda API call fails after retries."""
    def __init__(self, message, status_code=None, response_body=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class CodaClient:
    """
    Wrapper for the Coda REST API v1.

    Usage:
        client = CodaClient(api_token='your-token')
        docs = client.list_documents()
    """

    BASE_URL = 'https://coda.io/apis/v1'

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or settings.CODA_API_TOKEN
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
        })
        logger.debug("CodaClient initialized")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """
        Make an API request with retry logic and rate limit handling.
        Retries on 429 (rate limited) and 5xx errors.
        """
        url = f"{self.BASE_URL}{path}"

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug("API %s %s (attempt %d)", method.upper(), path, attempt)
                response = self.session.request(method, url, **kwargs)

                # Rate limited — wait and retry
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', RETRY_BACKOFF_FACTOR ** attempt))
                    logger.warning("Rate limited on %s, retrying in %ds", path, retry_after)
                    time.sleep(retry_after)
                    continue

                # Server error — retry with backoff
                if response.status_code >= 500:
                    wait_time = RETRY_BACKOFF_FACTOR ** attempt
                    logger.warning("Server error %d on %s, retrying in %ds",
                                   response.status_code, path, wait_time)
                    time.sleep(wait_time)
                    continue

                # Client error — don't retry
                if response.status_code >= 400:
                    error_body = response.text
                    logger.error("API error %d on %s: %s", response.status_code, path, error_body)
                    raise CodaAPIError(
                        f"API error {response.status_code}: {error_body}",
                        status_code=response.status_code,
                        response_body=error_body,
                    )

                # Success
                return response.json() if response.content else {}

            except requests.RequestException as e:
                if attempt == MAX_RETRIES:
                    logger.error("Network error on %s after %d attempts: %s", path, attempt, str(e))
                    raise CodaAPIError(f"Network error: {str(e)}")
                wait_time = RETRY_BACKOFF_FACTOR ** attempt
                logger.warning("Network error on %s, retrying in %ds: %s", path, wait_time, str(e))
                time.sleep(wait_time)

        raise CodaAPIError(f"Max retries exceeded for {path}")

    def _paginate(self, path: str, params: Optional[dict] = None, items_key: str = 'items') -> list:
        """
        Handle Coda API pagination. Follows nextPageToken until all items are collected.
        """
        all_items = []
        params = params or {}

        while True:
            data = self._request('GET', path, params=params)
            items = data.get(items_key, [])
            all_items.extend(items)

            next_page = data.get('nextPageToken')
            if not next_page:
                break

            params['pageToken'] = next_page
            logger.debug("Paginating %s, fetched %d items so far", path, len(all_items))

        logger.info("Fetched %d total items from %s", len(all_items), path)
        return all_items

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def whoami(self) -> dict:
        """
        Validate the API token and return user info.
        GET /whoami
        """
        result = self._request('GET', '/whoami')
        logger.info("Authenticated as: %s", result.get('name', 'unknown'))
        return result

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    def list_documents(self, query: Optional[str] = None) -> list:
        """
        List all accessible documents with metadata.
        GET /docs
        """
        params = {}
        if query:
            params['query'] = query
        return self._paginate('/docs', params=params)

    def get_document(self, doc_id: str) -> dict:
        """
        Get detailed metadata for a single document.
        GET /docs/{docId}
        """
        return self._request('GET', f'/docs/{doc_id}')

    def delete_document(self, doc_id: str) -> dict:
        """
        Delete a document.
        DELETE /docs/{docId}
        """
        logger.warning("Deleting document %s", doc_id)
        return self._request('DELETE', f'/docs/{doc_id}')

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------

    def list_pages(self, doc_id: str) -> list:
        """
        List all pages in a document.
        GET /docs/{docId}/pages
        """
        return self._paginate(f'/docs/{doc_id}/pages')

    def get_page(self, doc_id: str, page_id: str) -> dict:
        """
        Get metadata for a specific page.
        GET /docs/{docId}/pages/{pageIdOrName}
        """
        return self._request('GET', f'/docs/{doc_id}/pages/{page_id}')

    def export_page(self, doc_id: str, page_id: str, output_format: str = 'html') -> str:
        """
        Export page content as HTML or Markdown.
        This is an async operation: POST to begin, then poll for status.
        Returns the exported content as a string.
        """
        # Step 1: Begin export
        logger.info("Starting page export: doc=%s, page=%s, format=%s", doc_id, page_id, output_format)
        begin_response = self._request(
            'POST',
            f'/docs/{doc_id}/pages/{page_id}/export',
            json={'outputFormat': output_format},
        )

        request_id = begin_response.get('id')
        if not request_id:
            raise CodaAPIError("No request ID returned from page export")

        # Step 2: Poll for completion
        for poll_attempt in range(30):  # Max 30 polls (~60 seconds)
            time.sleep(2)  # Wait 2 seconds between polls
            status_response = self._request(
                'GET',
                f'/docs/{doc_id}/pages/{page_id}/export/{request_id}',
            )

            export_status = status_response.get('status')
            if export_status == 'complete':
                download_link = status_response.get('downloadLink')
                if download_link:
                    # Download the exported content
                    content_response = requests.get(download_link)
                    content_response.raise_for_status()
                    logger.info("Page export complete: doc=%s, page=%s", doc_id, page_id)
                    return content_response.text
                raise CodaAPIError("Export complete but no download link provided")

            if export_status == 'failed':
                raise CodaAPIError(f"Page export failed: {status_response}")

            logger.debug("Export status: %s (poll %d/30)", export_status, poll_attempt + 1)

        raise CodaAPIError("Page export timed out after 60 seconds")

    # ------------------------------------------------------------------
    # Tables
    # ------------------------------------------------------------------

    def list_tables(self, doc_id: str) -> list:
        """
        List all tables (and views) in a document.
        GET /docs/{docId}/tables
        """
        return self._paginate(f'/docs/{doc_id}/tables')

    def get_table(self, doc_id: str, table_id: str) -> dict:
        """
        Get metadata for a specific table.
        GET /docs/{docId}/tables/{tableIdOrName}
        """
        return self._request('GET', f'/docs/{doc_id}/tables/{table_id}')

    def list_columns(self, doc_id: str, table_id: str) -> list:
        """
        List columns in a table.
        GET /docs/{docId}/tables/{tableIdOrName}/columns
        """
        return self._paginate(f'/docs/{doc_id}/tables/{table_id}/columns')

    # ------------------------------------------------------------------
    # Rows
    # ------------------------------------------------------------------

    def list_rows(self, doc_id: str, table_id: str, limit: int = 500) -> list:
        """
        List all rows in a table (paginated).
        GET /docs/{docId}/tables/{tableIdOrName}/rows
        """
        return self._paginate(
            f'/docs/{doc_id}/tables/{table_id}/rows',
            params={'limit': limit, 'useColumnNames': 'true'},
        )

    def get_row(self, doc_id: str, table_id: str, row_id: str) -> dict:
        """
        Get a specific row.
        GET /docs/{docId}/tables/{tableIdOrName}/rows/{rowIdOrName}
        """
        return self._request('GET', f'/docs/{doc_id}/tables/{table_id}/rows/{row_id}')

    def update_row(self, doc_id: str, table_id: str, row_id: str, cells: list) -> dict:
        """
        Update values in a specific row.
        PUT /docs/{docId}/tables/{tableIdOrName}/rows/{rowIdOrName}

        Args:
            cells: List of dicts, e.g. [{"column": "Name", "value": "[REDACTED]"}]
        """
        logger.info("Updating row %s in table %s, doc %s", row_id, table_id, doc_id)
        return self._request(
            'PUT',
            f'/docs/{doc_id}/tables/{table_id}/rows/{row_id}',
            json={'row': {'cells': cells}},
        )

    def delete_row(self, doc_id: str, table_id: str, row_id: str) -> dict:
        """
        Delete a specific row.
        DELETE /docs/{docId}/tables/{tableIdOrName}/rows/{rowIdOrName}
        """
        logger.warning("Deleting row %s from table %s in doc %s", row_id, table_id, doc_id)
        return self._request('DELETE', f'/docs/{doc_id}/tables/{table_id}/rows/{row_id}')

    # ------------------------------------------------------------------
    # Permissions / ACL
    # ------------------------------------------------------------------

    def get_permissions(self, doc_id: str) -> list:
        """
        Get sharing permissions for a document.
        GET /docs/{docId}/acl/permissions
        """
        data = self._request('GET', f'/docs/{doc_id}/acl/permissions')
        return data.get('items', [])

    def delete_permission(self, doc_id: str, permission_id: str) -> dict:
        """
        Revoke a specific permission on a document.
        DELETE /docs/{docId}/acl/permissions/{permissionId}
        """
        logger.warning("Revoking permission %s on doc %s", permission_id, doc_id)
        return self._request('DELETE', f'/docs/{doc_id}/acl/permissions/{permission_id}')
