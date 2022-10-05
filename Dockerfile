FROM python:3.10-alpine

COPY requirements.txt requirements.txt

RUN apk add --no-cache git

RUN /usr/local/bin/python3.10 -m pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt 

RUN apk update && apk add bash

COPY . .

EXPOSE 3000

CMD [ "python3", "launcher.py" ]