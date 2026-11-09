FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0
COPY . .
# Hugging Face Spaces run the container as user 1000; the run registry must be writable by it.
RUN useradd -m -u 1000 psl && mkdir -p /app/runs && chown -R psl /app
USER psl
# One BLAS thread: the simulation is already parallel across paths, and multiple threads on a small
# container stalled runs on shared hosts.
ENV OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    PSL_HOST=0.0.0.0 PSL_PORT=7860 PSL_RUNS_DIR=/app/runs PSL_AUTH_MODE=open PSL_LLM=off \
    PSL_PROFILE=demo PSL_GATES=open PSL_DEV_MODE=off PSL_TICK_PACE=0.02 \
    PSL_FRAME_ANCESTORS="https://huggingface.co https://*.hf.space"
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request,os;urllib.request.urlopen('http://127.0.0.1:%s/healthz' % os.environ.get('PSL_PORT','7860'))" || exit 1
CMD gunicorn -w 1 --threads 8 --timeout 900 -b 0.0.0.0:${PSL_PORT:-7860} dash_app:server
