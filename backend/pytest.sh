#!/bin/sh -e
set -x

uv run python -m pytest tests/ -v