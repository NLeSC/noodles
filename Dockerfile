FROM debian:testing
MAINTAINER Johan Hidding <j.hidding@esciencecenter.nl>

# base system
RUN apt-get update && apt-get install -y wget git python3.5 python3.5-venv default-jre
ENV JAVA_HOME="/usr/lib/jvm/default-java"

# install pip
RUN wget -q -P /tmp https://bootstrap.pypa.io/get-pip.py && \
    python3.5 /tmp/get-pip.py

# install gcc
RUN apt-get install gcc

# install noodles
COPY . /tmp/noodles
RUN cd /tmp/noodles && \
    pip install Cython && \
    pip install -r requirements.txt && \
    pip install .


# create the user
RUN useradd -ms /bin/bash joe
USER joe
WORKDIR /home/joe

# create a Python virtualenv
# RUN pyvenv-3.5 $HOME/venv && . $HOME/venv/bin/activate
