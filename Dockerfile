FROM python:3.9.5

WORKDIR /
RUN mkdir /app
COPY . app/

RUN pip install -U pip setuptools && pip install -r /app/requirements.txt

WORKDIR /app/

CMD exec gunicorn --bind :$PORT --workers 1 main:app
