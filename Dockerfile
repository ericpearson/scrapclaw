FROM ghcr.io/d4vinci/scrapling:latest

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && scrapling install

COPY main.py .

EXPOSE 8192

ENTRYPOINT []
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8192}"]
