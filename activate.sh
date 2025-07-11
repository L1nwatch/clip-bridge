#!/bin/bash
# Auto-activate virtual environment
if [ -f "utils/.venv/bin/activate" ]; then
    source utils/.venv/bin/activate
    echo "Virtual environment activated: $VIRTUAL_ENV"
else
    echo "Virtual environment not found at utils/.venv/bin/activate"
fi
