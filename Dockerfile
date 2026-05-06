FROM python:3.13-slim

ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /
RUN chmod +x /wait-for-it.sh

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 33333

CMD ["/wait-for-it.sh", "mysql:3306", "--", \
     "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "33333"]
