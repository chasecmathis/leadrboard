#!/bin/sh

echo 'Running Pytest suite...'

uv run python -m pytest tests/ -v
PYTEST_EXIT=$?

if [ $PYTEST_EXIT -ne 0 ]; then
    echo "Pytest suite failed."
    exit 1
fi

echo 'Pytest suite passed!'
