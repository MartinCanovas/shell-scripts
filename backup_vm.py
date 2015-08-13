#!/usr/bin/env python
'''
This Python script creates a clone of VMs, and place it on a NFS mount share.
During this process, the VMs are pause and later resume. They are never
rebooted or shutdown.

In order to use and start one of the clone VMs, please follow these steps:
    - Copy the VM clone image and the VM clone XML file to your host
    - Edit the clone XML file to reflect the new location of the clone image file
    - E.g. <source file='/vms/win7-clone'/>
    - You might need to change the type of image to 'raw' if the image type is not qcow2
    - E.g. <driver name='qemu' type='raw'/>
    - Add clone vm to libvirt by running: virsh define <xml file>
    - Start the clone vm: virsh start <vm>
'''


import os
import subprocess
import time
import logging
from logging.handlers import RotatingFileHandler

BACKUP_DESTINATION = '/mnt/backup'
MOUNT_SOURCE = '10.0.2.10:/volume1/backup'
MAILTO = 'support@company.com'
LOG = '/var/log/backup_vm.log'


def pause_vm(vm):
    success = True
    logger.info('Pausing VM {0}'.format(vm))
    proc = subprocess.Popen("virsh suspend {0}".format(vm),
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.STDOUT,
                                                    shell=True)
    proc.communicate()
    if proc.returncode != 0:
        logger.error("Failed to pause VM {0}".format(vm))
        success = False

    return success

def resume_vm(vm):
    success = True
    logger.info('Resuming VM {0}'.format(vm))
    proc = subprocess.Popen("virsh resume {0}".format(vm),
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.STDOUT,
                                                    shell=True)
    proc.communicate()
    if proc.returncode != 0:
        logger.error("Failed to resume VM {0}".format(vm))
        success = False

    return success

def clone_vm(vm):
    success = True
    clone_vm = vm + '-clone'
    clone_img = BACKUP_DESTINATION + '/' + clone_vm
    clone_xml = clone_img + '.xml'
    logger.info('Cloning VM {0}'.format(vm))
    proc = subprocess.Popen("rm -f {0}".format(clone_img),
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.STDOUT,
                                                    shell=True)
    proc = subprocess.Popen("virt-clone -o {0} -n {1} -f {2}".format(vm, clone_vm, clone_img),
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.STDOUT,
                                                    shell=True)
    proc.communicate()
    if proc.returncode != 0:
        logger.error("Failed to clone VM {0}".format(vm))
        success = False

    with open(clone_xml, 'a+') as xml:
        proc = subprocess.Popen("virsh dumpxml {0}".format(clone_vm),
                                                    stdout=xml,
                                                    stderr=xml,
                                                    shell=True)

    return success

def undefine_vm(vm):
    success = True
    clone_vm = vm + '-clone'
    proc = subprocess.Popen("virsh undefine {0}".format(clone_vm),
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.STDOUT,
                                                    shell=True)
    proc.communicate()
    if proc.returncode != 0:
        logger.error("Failed to delete VM {0}".format(clone_vm))
        success = False

    return success

def checkMountPoint():
    if not os.path.exists(BACKUP_DESTINATION):
        logger.info('Mount point {0} does not exist. Creating one.'.format(BACKUP_DESTINATION))
        proc = subprocess.Popen(['mkdir -p /mnt/backup'], stdout=subprocess.PIPE, shell=True)
        proc.communicate()
        if proc.returncode != 0:
            logger.error("Failed to create {0}".format(BACKUP_DESTINATION))
        else:
            logger.info("Success creating {0}".format(BACKUP_DESTINATION))

    proc = subprocess.Popen(["mount | grep {0} | awk -F\" \" '{{print $1}}'".format(MOUNT_SOURCE)], stdout=subprocess.PIPE, shell=True)

    stdout = proc.communicate()[0].splitlines()

    if stdout == []:
        logger.info('Backup destination not mounted.')
        logger.info('Mounting {0}'.format(BACKUP_DESTINATION))
        proc = subprocess.Popen(['mount {0} {1}'.format(MOUNT_SOURCE, BACKUP_DESTINATION)], stdout=subprocess.PIPE, shell=True)
        proc.communicate()
        if proc.returncode != 0:
            logger.error("Failed to mount {0}".format(BACKUP_DESTINATION))
        else:
            logger.info("Success mounting {0}".format(BACKUP_DESTINATION))

#
# Main code starts here
#

if __name__ == "__main__":

    logger = logging.getLogger('backup_vm.log')
    logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler(LOG, backupCount=5)
    logger.addHandler(handler)
    logger.handlers[0].doRollover()

    logger.info('######## Backup Start at {0} ########'.format(time.ctime()))
    checkMountPoint()

    proc = subprocess.Popen("virsh list --all | awk '{print $2}'", stdout=subprocess.PIPE, shell=True)
    servers = proc.communicate()[0].splitlines()

    for vm in servers:

        if not(vm == 'Name' or vm == ''):
            proc = subprocess.Popen(["virsh list --all | grep {0} | awk '{{print $3}}'".format(vm)],
                                                                    stdout=subprocess.PIPE, shell=True)
            stdout = proc.communicate()[0].splitlines()[0]
            if stdout == 'running':
                pause_vm(vm)
                clone_vm(vm)
                resume_vm(vm)
                undefine_vm(vm)


    logger.info('######## Backup Finished at {0} ########'.format(time.ctime()))
    proc = subprocess.Popen(['cat {0} | mail -s "Backup Script Finished at {1}" {2}'.format(LOG, time.ctime(), MAILTO)],
                                                                                    stdout=subprocess.PIPE, shell=True)
