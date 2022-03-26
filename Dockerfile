FROM jrottenberg/ffmpeg:4.0-scratch AS ffmpeg
FROM ubuntu
FROM python:3.9
COPY --from=ffmpeg / /


COPY . /

RUN pip install -r requirements.txt

CMD ["python", "./discordquizbot.py"]
