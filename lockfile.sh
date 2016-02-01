#!/bin/bash

LOCKFILE=/tmp/lock-`whoami`
if [ -e ${LOCKFILE} ] && kill -0 `cat ${LOCKFILE}`; then
    echo "Already running!"
    exit 1
fi
trap "rm -f ${LOCKFILE}; exit" INT TERM EXIT
echo $$ > ${LOCKFILE}
