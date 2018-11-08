FROM python:3.6

RUN apt-get update
RUN apt-get install -y vim

WORKDIR /src
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# uwsgi --http :8000 --module config.wsgi