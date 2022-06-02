FROM python:3.9.13-slim

RUN adduser alkivi

WORKDIR /usr/src/app


RUN apt-get update \
	&& apt-get install zbar-tools -y


RUN pip install --upgrade pip
RUN pip install pipenv 

COPY Pipfile ./
COPY Pipfile.lock ./
RUN pipenv
RUN pipenv install --system

COPY app.py ./
ADD application ./application
COPY boot.sh ./boot.sh
RUN chmod a+x boot.sh

RUN chown -R alkivi:alkivi ./
USER alkivi

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]