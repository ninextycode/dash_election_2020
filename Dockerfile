FROM ubuntu:20.04

RUN apt-get update
RUN apt-get install -y python3-pip

COPY . /elections_2020
WORKDIR /elections_2020
RUN pip3 install -r requirements.txt

ENV ELECTION_DATA_FOLDER /data

ENTRYPOINT ["gunicorn", "app.factory:build_server()"]
CMD ["-w",  "1"]