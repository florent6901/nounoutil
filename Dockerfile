FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
ENV DB=/data/asmat.db TZ=Europe/Paris
VOLUME /data
EXPOSE 8000
CMD ["sh","docker-entrypoint.sh"]
