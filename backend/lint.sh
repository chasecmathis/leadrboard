#!/bin/sh -e

echo 'Running Black formatting...'

uv run black ./

echo 'Black formatting completed.'

echo 'Running Ruff check...'

uv run ruff check ./

echo 'Ruff check completed.'
