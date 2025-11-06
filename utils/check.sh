#!/usr/bin/env bash
cd milton
clear &&
ruff format && ruff check &&
mypy --strict --strict --strict main.py &&
pyright