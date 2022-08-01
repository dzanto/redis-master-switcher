FROM python:3.10-slim

RUN pip install redis kubernetes

WORKDIR /code

COPY . .

ENTRYPOINT ["python", "main.py"]
