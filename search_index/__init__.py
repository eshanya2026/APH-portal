"""
APH SmartSearch AI — Search Index Module
"""

from .database import (
    DEFAULT_DB_PATH,
    init_db,
    get_connection,
    upsert_document,
    get_document,
    get_all_documents,
    delete_document,
    mark_document_error,
    get_indexing_stats,
    search_passages,
    classify_access_level,
    detect_sensitive_content,
    record_indexing_run
)

__all__ = [
    'DEFAULT_DB_PATH',
    'init_db',
    'get_connection',
    'upsert_document',
    'get_document',
    'get_all_documents',
    'delete_document',
    'mark_document_error',
    'get_indexing_stats',
    'search_passages',
    'classify_access_level',
    'detect_sensitive_content',
    'record_indexing_run'
]
