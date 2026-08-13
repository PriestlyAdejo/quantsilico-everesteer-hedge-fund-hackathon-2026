# Public-safe, reproducible worker base. Building/pushing/provisioning is an operator action.
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ARG PYTHON_VERSION=3.11
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       python${PYTHON_VERSION} python3-pip tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY configs/compute/worker-requirements.lock /tmp/worker-requirements.lock
RUN python${PYTHON_VERSION} -m pip install --no-cache-dir -r /tmp/worker-requirements.lock
COPY pyproject.toml README.md /workspace/
COPY src /workspace/src
RUN python${PYTHON_VERSION} -m pip install --no-cache-dir --no-deps /workspace

ENV PYTHONUNBUFFERED=1 \
    XLA_PYTHON_CLIENT_PREALLOCATE=false \
    QSEH_SYNTHETIC=1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python3.11", "-m", "qs_everesteer.jobs.worker", "--help"]
