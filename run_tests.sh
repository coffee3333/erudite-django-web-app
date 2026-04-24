#!/bin/bash
set -a
source .env
set +a

.venv/bin/pytest tests/ -v
