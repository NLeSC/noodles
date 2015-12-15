#!/bin/bash

#source .profile

export JAVA_HOME="/usr/lib/jvm/java-7-openjdk-amd64/"
cd ${HOME}/Code/workflow-engine
# echo $*
source ${HOME}/Code/workflow-engine/venv/bin/activate
python3.5 $* 2> errlog
deactivate
