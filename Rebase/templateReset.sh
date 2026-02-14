#!/bin/bash
# ======== Robust Template Reset Runner ========

PROJECT_DIR="/Users/simran/PycharmProjects/Rebase"
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="$PROJECT_DIR/log.txt"

# Set environment for cron
export HOME="/Users/simran"
export PATH="$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Log environment info
{
  echo "========== $(date) =========="
  echo "Current working directory: $(pwd)"
  echo "Python being used: $(which python)"
  python --version
} >> "$LOG_FILE"

# Run template reset script
python "$PROJECT_DIR/templateReset.py" >> "$LOG_FILE" 2>&1

echo "Template reset completed at $(date)" >> "$LOG_FILE"

