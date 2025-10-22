#!/bin/bash

# Verify project structure

echo "Checking project structure..."

errors=0

# Check root files
root_files=(
    "pytest.ini"
    "pyproject.toml"
    ".flake8"
    "setup.py"
    "requirements.txt"
    "requirements-dev.txt"
    "Makefile"
    "README.md"
    ".gitignore"
)

for file in "${root_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file (should be in project root)"
        ((errors++))
    else
        echo "✓ Found: $file"
    fi
done

# Check test conftest
if [ ! -f "gdrive_sync/tests/conftest.py" ]; then
    echo "❌ Missing: gdrive_sync/tests/conftest.py"
    ((errors++))
else
    echo "✓ Found: gdrive_sync/tests/conftest.py"
fi

# Check for misplaced files
if [ -f "gdrive_sync/pytest.ini" ]; then
    echo "⚠️  Warning: pytest.ini found in gdrive_sync/ (should be in root)"
    ((errors++))
fi

if [ -f "gdrive_sync/conftest.py" ]; then
    echo "⚠️  Warning: conftest.py found in gdrive_sync/ (should be in gdrive_sync/tests/)"
    ((errors++))
fi

# Check docker files
docker_files=(
    "docker/Dockerfile"
    "docker/docker-compose.yml"
    "docker/entrypoint.sh"
    "docker/.dockerignore"
)

for file in "${docker_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        ((errors++))
    else
        echo "✓ Found: $file"
    fi
done

echo ""
if [ $errors -eq 0 ]; then
    echo "✅ Project structure is correct!"
else
    echo "❌ Found $errors issue(s). Please fix them."
    exit 1
fi
