FROM python:3.9

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends --no-install-suggests \
      libsensors5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /
RUN pip install -r requirements.txt

COPY *.py /

CMD ["python", "-u", "./app.py"]
