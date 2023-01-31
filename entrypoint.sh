#!/bin/bash
set -euo pipefail

if [ -v DEV_MODE ]; then
    counter=0
    until alembic upgrade head || [[ $counter -gt 2 ]]; do
        ((counter++))
        sleep $counter
    done
fi

exec hypercorn --config=hypercorn.toml gitclub.main:app
