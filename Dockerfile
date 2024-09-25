FROM python:3.11

RUN mkdir -p /usr/src/app
RUN mkdir -p /usr/src/app/datapackage

WORKDIR /usr/src/app

COPY ./requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

COPY ./entrypoint.py .

VOLUME /usr/src/app/datapackage

CMD [ "python", "./entrypoint.py" ]
