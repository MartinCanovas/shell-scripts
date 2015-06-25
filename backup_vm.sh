#!/bin/bash
#
# Backup virtual machines (kvm) using rsync
# This script will stop and start a vm
#

TIMEOUT=240
START=`date +%s.%N`
#VM_DISK_LOCATION=/var/lib/libvirt/images
BACKUP_DESTINATION=/bkp/backups
PRG=`/usr/bin/basename $0`
LOGFILE="/var/log/${PRG}.log"


stop_vm()
{
  echo "Shutting down VM $1" >> $LOGFILE 2>&1
  virsh shutdown $1 >> $LOGFILE 2>&1
}

force_stop_vm()
{
  echo "Forcing shutdown down VM $1" >> $LOGFILE 2>&1
  virsh destroy $1 >> $LOGFILE 2>&1
}


start_vm()
{
  echo "Starting VM $1" >> $LOGFILE 2>&1
  virsh start $1 >> $LOGFILE 2>&1
}

backup_vm()
{
  if [[ $(virsh dumpxml $1 | grep "source file" | awk -F\' '{print $2}') != "" ]]
  then
     VM_DISK=$(virsh dumpxml $1 | grep "source file" | awk -F\' '{print $2}')
  else
     echo "Couldn't find image file for $1. No backup will be done for $1" >> $LOGFILE 2>&1
  fi

  echo "Backup in progress for VM $1 ..." >> $LOGFILE 2>&1
  rsync -av $VM_DISK $BACKUP_DESTINATION >> $LOGFILE 2>&1
}

#
# Main code start here
#

if [ ! -d $BACKUP_DESTINATION ]
then
   echo "Backup destination not detected, aborting" >> $LOGFILE 2>&1
   exit 1
fi

echo "######## ${PRG} starting at `date` ########" >> $LOGFILE 2>&1

for vm in $(virsh list --all | awk '{print $2}'|sort)
  do
    if [ $vm != 'Name' ]
    then
        if [ 'running' == $(virsh list --all | grep $vm | awk '{print $3}') ]
        then
           stop_vm $vm
	   while [ 'running' == $(virsh list --all | grep $vm | awk '{print $3}') ]
	   do
             sleep 1	
             (( TIMEOUT -= 1 ))
             if [ $TIMEOUT == 0 ]
             then
               force_stop_vm $vm
               TIMEOUT=240
             fi
	   done
           backup_vm $vm
           start_vm $vm
       
        else
      	   backup_vm $vm
        fi
    fi
  done

END=`date +%s.%N`
echo "######## ${PRG} finished at `date` ########" >> $LOGFILE 2>&1
printf "Runtime: %.3F\n" $( echo "${END} - ${START}" | bc ) >> $LOGFILE 2>&1
