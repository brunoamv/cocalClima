#!/bin/bash

LOG_FILE="/home/bruno/Desktop/Mega/Curso/Django/App/cocalTempo2/scripts/ScriptAutomacao_YT_log_$(date +%Y-%m-%d_%H-%M-%S).log"

/usr/bin/python3 /home/bruno/Desktop/Mega/Curso/Django/App/cocalTempo2/scripts/ScriptAutomacao_YT.py >> "$LOG_FILE" 2>&1
