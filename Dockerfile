FROM ubuntu:20.04

RUN apt-get update
RUN apt-get install -y python3-pip

WORKDIR /elections_2020

COPY requirements.txt ./
RUN pip3 install -r requirements.txt

COPY . /elections_2020

ENV ELECTION_DATA_FOLDER /data

ENTRYPOINT ["gunicorn", "app.factory:build_server()", "--bind", "0.0.0.0"]
CMD ["-w",  "1"]