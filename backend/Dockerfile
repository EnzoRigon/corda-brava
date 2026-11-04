FROM python:3.11-slim AS build
WORKDIR /src
COPY pyproject.toml ./
COPY app ./app
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir .

FROM python:3.11-slim
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////data/corda_brava.db
RUN useradd --system --uid 10001 app && mkdir /data /app && chown app /data
COPY --from=build /opt/venv /opt/venv
COPY app /app/app
WORKDIR /app
USER app
VOLUME /data
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
  CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/health', timeout=2)"
# Single worker on purpose: queue, registry and dedup are in-process. The backend is only
# reachable via nginx, so trusting X-Forwarded-For from any peer is safe (login rate limit per client IP).
CMD ["uvicorn", "app.core.app_factory:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
