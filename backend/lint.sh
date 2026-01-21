#!/bin/sh

uv run black --check ./
BLACK_EXIT=$?

uv run ruff check ./
RUFF_EXIT=$?

if [ $BLACK_EXIT -ne 0 ] || [ $RUFF_EXIT -ne 0 ]; then
    echo "Linting failed."
    exit 1
fi

echo "All linting passed!"