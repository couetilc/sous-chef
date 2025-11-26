#!/bin/bash
# Helper script to run multiple parallel turkey scoring workers
# Usage: ./bin/parallel-score-turkey.sh [num_workers] [batch_size]

NUM_WORKERS=${1:-5}  # Default: 5 workers
BATCH_SIZE=${2:-10}  # Default: 10 recipes per batch

echo "Starting $NUM_WORKERS parallel turkey scoring workers..."
echo "Batch size: $BATCH_SIZE"
echo "Press Ctrl+C to stop all workers"
echo ""

# Array to store background process IDs
pids=()

# Start workers in background
for i in $(seq 1 $NUM_WORKERS); do
    docker compose run --rm backend python manage.py score_recipes_turkey_parallel \
        --batch-size "$BATCH_SIZE" \
        --worker-id "turkey-worker-$i" &
    pids+=($!)
    echo "Started turkey-worker-$i (PID: ${pids[-1]})"
done

echo ""
echo "All workers started. Waiting for completion..."

# Wait for all workers to complete
for pid in "${pids[@]}"; do
    wait $pid
done

echo ""
echo "All workers finished!"
