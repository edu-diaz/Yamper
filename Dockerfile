FROM python:3.6

RUN git clone https://github.com/gameduser/Yamper.git
WORKDIR /Yamper

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

CMD ["python3", "run.py"]