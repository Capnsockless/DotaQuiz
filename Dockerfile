FROM jrottenberg/ffmpeg:4.0-scratch AS ffmpeg
FROM ubuntu
FROM python:3.9

WORKDIR /app

COPY --from=ffmpeg / /app


COPY . /app

RUN pip install -r requirements.txt

CMD ["python", "./discordquizbot.py"]
