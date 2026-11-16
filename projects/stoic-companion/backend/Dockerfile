FROM python:3.12-slim
WORKDIR /workspace
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY backend /workspace/backend
COPY corpus /workspace/corpus
COPY eval/questions.json /workspace/eval/questions.json
COPY pyproject.toml /workspace/pyproject.toml
ENV PYTHONPATH=/workspace/backend
RUN useradd -m stoic && mkdir -p /workspace/backend/data && chown -R stoic:stoic /workspace
USER stoic
WORKDIR /workspace/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
