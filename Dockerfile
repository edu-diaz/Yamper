FROM python:3.6-slim@sha256:ac11ce85a603a835533b2ec608246fef2fea4a4b4790df97a20d9cce7032faf6

RUN apt-get -y update
RUN apt-get -y install git
RUN git clone https://github.com/gameduser/Yamper.git
WORKDIR /Yamper

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

CMD ["python3", "run.py"]