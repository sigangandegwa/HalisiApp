# Halisi backend on Railway (or any container host). CPU-only: hashing, identity matching,
# payment/language/account scoring and templated remediation all run for real. CLIP stays off
# (ENABLE_CLIP=false) since Railway's free/hobby tier has no GPU and torch is ~2 GB — see
# requirements-ml.txt and docs/BREV_ENGINE_SETUP.md for the optional GPU upgrade path.
FROM python:3.12-slim

WORKDIR /app

# Install deps first so this layer is cached across code-only changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
# database/schema.sql lives one level up (repo root) and is run manually against Supabase's SQL
# editor (docs/BACKEND.md section 13, TSK-001) — the app never reads it at runtime, so it isn't
# copied here. The Railway service's root directory must be set to `backend/`.

RUN useradd --create-home --uid 10001 halisi && chown -R halisi:halisi /app
USER halisi

# Railway injects $PORT at runtime; default to 8080 for `docker run` without one.
ENV PORT=8080
EXPOSE 8080

# No --proxy-headers: Railway's edge proxy isn't on 127.0.0.1, so uvicorn's own forwarded-header
# rewriting would either do nothing (default --forwarded-allow-ips=127.0.0.1, safe but pointless)
# or, if ever loosened, let any client spoof request.client.host before app.core.security.client_ip
# gets a chance to check it. The app does its own (narrower) X-Forwarded-For handling instead.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
