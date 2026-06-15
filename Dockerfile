FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir grpcio grpcio-tools aiortc pycryptodome av behave

COPY server/ .

COPY features/ ./features/

RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. signaling.proto

CMD ["python", "server.py"]
