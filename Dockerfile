FROM python:3.9-bullseye AS runtime
WORKDIR /app
COPY . .

RUN apt update
RUN apt install -y python3 python3-pip
RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "app.py"]
