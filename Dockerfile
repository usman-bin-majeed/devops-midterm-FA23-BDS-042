# CSC418 Lab Midterm - FA23-BDS-042
# Multi-stage build: train + test inside the image so the model is always
# trained with exactly the same library versions that serve it.

# ---- base: runtime dependencies (cached until requirements.txt changes) ----
FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---- train: retrain on the latest dataset, then run the test suite ----
FROM base AS train
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
ARG GIT_COMMIT=local
ENV GIT_COMMIT=${GIT_COMMIT}
COPY config.json train.py app.py ./
COPY dataset/ dataset/
COPY tests/ tests/
RUN python train.py && python -m pytest -q tests

# ---- runtime: slim serving image with the freshly trained model ----
FROM base AS runtime
COPY app.py config.json ./
COPY --from=train /app/artifacts ./artifacts
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)"
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
