#!/bin/bash

logfiles=(`ls -l1 /var/log/myscript*.log`)

length=${#logfiles[@]}

rotateLog()
{
 rm -f ${logfiles[0]}
 logfiles=(${logfiles[@]:1})
 length=${#logfiles[@]}
} 

while [ $length -gt 5 ]; do
   rotateLog
done
