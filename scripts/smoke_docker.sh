#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

IMAGE="${CADX_DOCKER_IMAGE:-cadx:local}"
CONTAINER="${CADX_DOCKER_CONTAINER:-cadx-smoke}"
PORT="${CADX_DOCKER_PORT:-8000}"
BASE_URL="http://127.0.0.1:${PORT}"

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker CLI is not available. Install Docker to run the CADX container smoke." >&2
    exit 2
fi
if ! docker info >/dev/null 2>&1; then
    echo "Docker daemon is not available. Start Docker Desktop or a compatible daemon, then rerun scripts/smoke_docker.sh." >&2
    exit 2
fi

docker build -t "${IMAGE}" .

docker run --rm "${IMAGE}" python -m compileall src/cadx tests >/dev/null
docker run --rm "${IMAGE}" cadx run-demo >/dev/null
docker run --rm "${IMAGE}" cadx validate | grep -Eq '"status": "(pass|warning)"'
docker run --rm "${IMAGE}" pytest -q tests/test_server.py

docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
docker run -d --name "${CONTAINER}" -p "${PORT}:8000" -v "$(pwd)/runs:/app/runs" "${IMAGE}" >/dev/null
cleanup() {
    docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

for _ in $(seq 1 30); do
    if curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

curl -fsS "${BASE_URL}/health" | grep -q '"status":"ok"'
curl -fsS "${BASE_URL}/workflows" | grep -q 'pan_tilt_2axis_demo'
curl -fsS "${BASE_URL}/dashboard" | grep -q 'CADX local review dashboard'
curl -fsS "${BASE_URL}/runs/pan_tilt_2axis_demo" | grep -Eq '"validation_status":"(pass|warning)"'
curl -fsS "${BASE_URL}/runs/pan_tilt_2axis_demo/artifacts" | grep -q 'preview.json'

echo "CADX Docker smoke passed: ${IMAGE} served ${BASE_URL} with canonical run metadata."
