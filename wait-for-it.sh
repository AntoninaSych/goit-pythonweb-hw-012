#!/usr/bin/env bash
# wait-for-it.sh by vishnubob

set -e

HOST="$1"
shift
CMD="$@"

until nc -z -v -w30 "$(echo "$HOST" | cut -d':' -f1)" "$(echo "$HOST" | cut -d':' -f2)"; do
  echo "Waiting for $HOST..."
  sleep 1
done

echo "$HOST is up!"
exec $CMD
