#!/bin/bash
set -ex
cd sentiment
uv sync --dev
uv run pytest
