#!/bin/bash
set -ex
cd sentiment
uv pip install -e .[dev]
uv run pytest
