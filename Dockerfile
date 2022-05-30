FROM python:3.8-alpine

RUN adduser -D alkivi

WORKDIR /usr/src/app

RUN apk --no-cache add \
        gcc g++ make libffi-dev openssl-dev git openssh-client musl-dev cargo libzbar

RUN pip install --upgrade pip
RUN pip install pipenv 
COPY Pipfile ./
COPY Pipfile.lock ./
RUN pipenv install --system --keep-outdated

COPY app.py ./
ADD application ./application
COPY boot.sh ./boot.sh
RUN chmod a+x boot.sh

RUN chown -R alkivi:alkivi ./
USER alkivi

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]