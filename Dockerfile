FROM python:3.9.13-slim

RUN adduser alkivi

WORKDIR /usr/src/app


RUN DEBIAN_FRONTEND=noninteractive apt-get -qq update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y libzbar-dev

# Clean image
RUN apt-get -yqq clean && \
    apt-get -yqq purge && \
    rm -rf /tmp/* /var/tmp/* && \
    rm -rf /var/lib/apt/lists/*


RUN pip install --upgrade pip
RUN pip install pipenv 

COPY Pipfile ./
COPY Pipfile.lock ./
RUN pipenv
RUN pipenv install --system

#COPY app.py ./
ADD application ./application
COPY boot.sh ./boot.sh
COPY wsgi.py ./wsgi.py
RUN mkdir -p ./volume/log
RUN chmod a+x boot.sh

RUN chown -R alkivi:alkivi ./
USER alkivi

EXPOSE 8000
ENTRYPOINT ["./boot.sh"]
