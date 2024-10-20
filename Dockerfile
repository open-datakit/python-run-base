FROM python:3.11

RUN mkdir -p /usr/src/app
RUN mkdir -p /usr/src/app/datakit

WORKDIR /usr/src/app

COPY ./requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

COPY ./entrypoint.py .

VOLUME /usr/src/app/datakit

CMD [ "python", "./entrypoint.py" ]
