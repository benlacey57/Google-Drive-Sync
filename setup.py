"""Setup script for Google Drive Sync tool."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="gdrive-sync",
    version="1.0.0",
    author="Ben Lacey",
    author_email="hello@benlacey.co.uk",
    description="Professional Google Drive synchronisation tool with compression and metrics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/benlacey57/gdrive-sync",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Archiving :: Backup",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "google-auth-oauthlib>=1.2.0",
        "google-auth-httplib2>=0.2.0",
        "google-api-python-client>=2.108.0",
        "rich>=13.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.1",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
            "pylint>=2.17.5",
            "isort>=5.12.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "gdrive-sync=main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
