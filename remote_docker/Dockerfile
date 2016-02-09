FROM debian:testing
MAINTAINER Johan Hidding <j.hidding@esciencecenter.nl>

RUN apt-get update && \
    apt-get install -y --no-install-recommends git python3.5 python3-numpy \
    python3-scipy ca-certificates python3-setuptools openssh-server \
    openssh-sftp-server slurm
    
RUN cd /tmp && \
    git clone https://github.com/NLeSC/noodles.git && \
    cd noodles && \
    git checkout devel && \
    python3.5 setup.py install

EXPOSE 22
    
RUN mkdir /var/run/sshd

RUN useradd -ms /bin/sh -p $(openssl passwd sixpack) joe

USER joe
RUN mkdir /home/joe/.ssh
ADD id_rsa.pub /home/joe/.ssh/authorized_keys

USER root

ADD welcome.txt /etc/motd

CMD ["/usr/sbin/sshd", "-D"]

