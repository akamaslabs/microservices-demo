#!/bin/bash

set -e

if [ -n "$RUN_ONLINE" ]; then
  echo "Running online test"
  locust --skip-log-setup 2>&1 &
  sleep 5s
  python3 online_test.py
else
  echo "Starting locust Web UI"
  locust 2>&1
fi