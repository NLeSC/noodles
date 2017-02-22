FROM phusion/baseimage:0.9.19
MAINTAINER Johan Hidding <j.hidding@esciencecenter.nl>

RUN rm -f /etc/service/sshd/down
RUN /etc/my_init.d/00_regen_ssh_host_keys.sh

RUN apt-get update \
 && apt-get install -y --no-install-recommends git python3.5 python3-numpy \
        python3-scipy ca-certificates python3-setuptools \
        slurmd slurm-client slurm-wlm
# && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN apt-get install -y python3-pip
RUN pip3 install noodles

EXPOSE 22

RUN useradd -ms /bin/bash -p $(openssl passwd sixpack) joe

USER joe
RUN mkdir /home/joe/.ssh
ADD id_rsa.pub /home/joe/.ssh/authorized_keys

USER root

ADD munge.key /etc/munge/munge.key
ADD service /etc/service
# Key was generated with openssl genrsa -out slurm.key 1024 && openssl rsa -in slurm.key -pubout -out slurm.cert
ADD etc /etc/slurm-llnl

RUN mkdir /var/run/munge \
 && mkdir -p /var/spool/slurmctld/state \
 && mkdir -p /var/spool/slurmd.node-0 \
 && mkdir -p /var/spool/slurmd.node-1 \
 && mkdir -p /var/spool/slurmd.node-2 \
 && mkdir -p /var/spool/slurmd.node-3 \
 && mkdir -p /var/spool/slurmd.node-4 \
 && chmod 600 /etc/munge/munge.key \
 && chown root.root /var/lib/munge /etc/munge \
 && touch /var/spool/slurmctld/accounting.txt \
 && chown slurm /var/spool/slurmctld/accounting.txt \
 && chown slurm /var/spool/slurmctld/state \
 && chown slurm /etc/slurm-llnl/slurm.key

ADD welcome.txt /etc/motd
CMD ["/sbin/my_init"]
