#!/bin/sh

/etc/init.d/slurmd start
/etc/init.d/slurmctld start
/etc/init.d/munge start

exec /usr/sbin/sshd -D

