#!/bin/sh -e

echo 'Running Pytest suite...'

uv run python -m pytest tests/ -v

echo 'Pytest suite completed.'
