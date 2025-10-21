"""Application-wide constants."""

from pathlib import Path

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

# Google Workspace MIME types to Open Document Format mapping
EXPORT_FORMATS = {
    'application/vnd.google-apps.document': {
        'format': 'application/vnd.oasis.opendocument.text',
        'extension': '.odt'
    },
    'application/vnd.google-apps.spreadsheet': {
        'format': 'application/vnd.oasis.opendocument.spreadsheet',
        'extension': '.ods'
    },
    'application/vnd.google-apps.presentation': {
        'format': 'application/vnd.oasis.opendocument.presentation',
        'extension': '.odp'
    },
    'application/vnd.google-apps.drawing': {
        'format': 'image/png',
        'extension': '.png'
    },
}

# Default exclusion patterns
DEFAULT_EXCLUSIONS = {
    # System files
    '.DS_Store',
    'Thumbs.db',
    'desktop.ini',
    '.Spotlight-V100',
    '.Trashes',
    # Version control
    '.git',
    '.svn',
    '.hg',
    '.gitignore',
    # IDE files
    '.idea',
    '.vscode',
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    # Temporary files
    '*.tmp',
    '*.temp',
    '*.bak',
    '~*',
    # Cache
    'node_modules',
    '.cache',
    '*.cache',
}

# Compression settings
COMPRESSION_THRESHOLD = 1024 * 1024  # 1MB
COMPRESSIBLE_EXTENSIONS = {
    '.txt', '.csv', '.json', '.xml', '.html', '.css', '.js',
    '.md', '.log', '.sql', '.py', '.java', '.cpp', '.h'
}

# File size limits
DEFAULT_MAX_FILE_SIZE = 0  # 0 = no limit

# Default paths
DEFAULT_DATA_DIR = Path.home() / '.gdrive_sync'
DEFAULT_CREDENTIALS_FILE = 'credentials.json'
DEFAULT_TOKEN_FILE = 'token.json'
