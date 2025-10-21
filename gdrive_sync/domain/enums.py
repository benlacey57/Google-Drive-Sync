"""Domain enumerations."""

from enum import Enum


class OperationType(Enum):
    """Types of sync operations."""
    DOWNLOAD = "download"
    UPLOAD = "upload"
    SYNC = "sync"
    ANALYSIS = "analysis"


class FileCategory(Enum):
    """Categories for file types."""
    IMAGES = "Images"
    VIDEOS = "Videos"
    AUDIO = "Audio"
    TEXT = "Text"
    PDFS = "PDFs"
    DOCUMENTS = "Documents"
    SPREADSHEETS = "Spreadsheets"
    PRESENTATIONS = "Presentations"
    ARCHIVES = "Archives"
    GOOGLE_DOCS = "Google Docs"
    OTHER = "Other"
