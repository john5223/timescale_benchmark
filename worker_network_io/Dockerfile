FROM python:3.6-alpine

WORKDIR /app

# For psycopg2
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev

# For scipy
RUN apk add gcc gfortran build-base wget freetype-dev libpng-dev openblas-dev

RUN pip install --upgrade pip

RUN pip install eventlet asyncio


COPY requirements.txt .
RUN pip install -r requirements.txt

COPY server ./server/
COPY entrypoint_api.py ./
COPY entrypoint_celery.py ./

#ENTRYPOINT celery -A controller.tasks worker --loglevel=info
