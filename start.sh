#!/bin/bash
cd "$(dirname "$0")"
if [ ! -f config.json ]; then
  cp config.example.json config.json
  echo "Created config.json from template. Please edit it with your settings."
  exit 1
fi
python3 server.py
