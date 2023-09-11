FROM python:3.8.3-slim-buster

# prevent Python from writing •pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# ensure Python output is sent directly to 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        build-essential \
        default-libmysqlclient-dev \
        binutils \
        libproj-dev \
        gdal-bin \
        postgresql \
        python-gdal \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /scenariodt
COPY requirements.txt /scenariodt/
# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

ENV HOME=/home/app
ENV APP_HOME=/home/app/web
WORKDIR $APP_HOME

# copy project
COPY . .

