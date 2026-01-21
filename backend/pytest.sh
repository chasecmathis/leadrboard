#!/bin/sh

echo 'Running Pytest suite...'

uv run python -m pytest tests/ -v

echo $?

echo 'Pytest suite completed.'
