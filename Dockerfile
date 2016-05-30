FROM debian:testing
MAINTAINER Johan Hidding <j.hidding@esciencecenter.nl>

# base system
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential git python3 python3-virtualenv virtualenv \
    default-jdk python3-numpy python3-nose python3-pip vim cython3 \
    python3-six python3-wheel

ENV JAVA_HOME="/usr/lib/jvm/default-java"

RUN apt-get install --no-install-recommends -y \
    python3-dev openssl

COPY ./patches /tmp/patches

## install noodles
COPY . /tmp/noodles
RUN cd /tmp/noodles && \
    python3 setup.py install

RUN apt-get install -y openssh-client

## create the user
RUN useradd -ms /bin/bash joe
USER joe
WORKDIR /home/joe

