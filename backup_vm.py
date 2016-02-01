#!/usr/bin/env python

import os
import subprocess
import time
import logging
from logging.handlers import TimedRotatingFileHandler

TIMEOUT = 30
BACKUP_DESTINATION = '/mnt/backup'
MOUNT_SOURCE = '10.0.2.10:/volume1/backup'
MAILTO = 'admin@company.com'
LOG_PATH = '/var/log/backup_vm.log'


def shutdownLinuxVM(vm):
    success = True
    logger.info('Shutting down linux VM {0}'.format(vm))
    proc = subprocess.Popen("ssh {0} shutdown -h now".format(vm),
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.STDOUT,
                                                    shell=True)
    proc.communicate()
    if proc.returncode != 0:
        logger.error("Failed to shutdown linux VM {0}".format(vm))
        success = False

    return success


def shutdownWindowsVM(vm):
    success = True
    logger.info('Shutting down Windows VM {0}'.format(vm))
    proc = subprocess.Popen("virsh shutdown {0}".format(vm),
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.STDOUT,
                                                    shell=True)
    proc.communicate()
    if proc.returncode != 0:
        logger.error("Failed to shutdown Windows VM {0}".format(vm))
        success = False

    return success

def forceShutdownWindowsVM(vm):
    success = True
    logger.info('Forcing shutdown Windows VM {0}'.format(vm))
    proc = subprocess.Popen("/root/scripts/remote_shutdown.py {0}".format(vm),
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.STDOUT,
                                                    shell=True)
    proc.communicate()
    if proc.returncode != 0:
        logger.error("Failed to shutdown Windows VM {0}".format(vm))
        success = False

    return success

def startVM(vm):
    success = True
    logger.info('Starting VM {0}'.format(vm))
    proc = subprocess.Popen("virsh start {0}".format(vm),
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.STDOUT,
                                                    shell=True)
    proc.communicate()
    if proc.returncode != 0:
        logger.error("Failed to start VM {0}".format(vm))
        success = False

    return success

def backupVM(vm):
    proc = subprocess.Popen(["virsh dumpxml {0} | grep 'source file' | awk -F\\' '{{print $2}}'".format(vm)],
                                                                        stdout=subprocess.PIPE, shell=True)
    stdout = proc.communicate()[0].splitlines()[0]
    if stdout != "":
        vmDisk = stdout
        logger.info('Backup in progress for VM {0}'.format(vm))
        proc = subprocess.Popen(['rsync -av {0} {1}'.format(vmDisk, BACKUP_DESTINATION)], stdout=subprocess.PIPE, shell=True)
        stdout = proc.communicate()[0].splitlines()[0]
        logger.info('Output: {0}'.format(stdout))
    else:
        logger.info("Couldn't find image file for {0}. No backup will be done for {0}".format(vm))

def waitForShutdown(vm):
    while TIMEOUT != 1:
        proc = subprocess.Popen(["virsh list --all | grep {0} | awk '{{print $3}}'".format(vm)], stdout=subprocess.PIPE, shell=True)
        stdout = proc.communicate()[0].splitlines()[0]
        if stdout == 'running':
            time.sleep(1)
            TIMEOUT -= 1
        else:
            TIMEOUT = 1

    TIMEOUT = 30

def checkMountPoint():
    if not os.path.exists(BACKUP_DESTINATION):
        logger.info('Mount point {0} does not exist. Creating one.'.format(BACKUP_DESTINATION))
        proc = subprocess.Popen(['mkdir -p /mnt/backup'], stdout=subprocess.PIPE, shell=True)
        stdout = proc.communicate()[0].splitlines()[0]
        logger.info('Output: {0}'.format(stdout))

    proc = subprocess.Popen(["mount | grep {0} | awk -F' ' '{{print $1}}'".format(MOUNT_SOURCE)],
                                                            stdout=subprocess.PIPE, shell=True)
    stdout = proc.communicate()[0].splitlines()[0]
    logger.info('Output: {0}'.format(stdout))

    if stdout != MOUNT_SOURCE:
        logger.info('Backup destination not mounted.')
        logger.info('Trying to mount {0}'.format(BACKUP_DESTINATION))
        proc = subprocess.Popen(['mount {0} {1}'.format(MOUNT_SOURCE, BACKUP_DESTINATION)], stdout=subprocess.PIPE, shell=True)
        stdout = proc.communicate()[0].splitlines()[0]
        logger.info('Output: {0}'.format(stdout))
        time.sleep(5)
        proc = subprocess.Popen(["mount | grep {0} | awk -F' ' '{{print $1}}'".format(MOUNT_SOURCE)],
                                                            stdout=subprocess.PIPE, shell=True)
        stdout = proc.communicate()[0].splitlines()[0]
        logger.info('Output: {0}'.format(stdout))

        if stdout != MOUNT_SOURCE:
            logger.info('Failed to mount {0}'.format(BACKUP_DESTINATION))
            proc = subprocess.Popen(['cat {0} | mail -s "Failed to mount {1} {2}"'.format(LOG_PATH, BACKUP_DESTINATION. MAILTO)],
                                                                                    stdout=subprocess.PIPE, shell=True)
            stdout = proc.communicate()[0].splitlines()[0]
            logger.info('Output: {0}'.format(stdout))
            exit(1)


#
# Main code starts here
#

if __name__ == "__main__":

    logger = logging.getLogger('backup_vm_log')
    logger.setLevel(logging.DEBUG)
    handler = TimedRotatingFileHandler(LOG_PATH, backupCount=5)
    logger.addHandler(handler)

    logger.info('######## {0} Start at {1} ########'.format(PRG, time.ctime()))
    checkMountPoint()

    proc = subprocess.Popen("virsh list --all | awk '{print $2}'", stdout=subprocess.PIPE, shell=True)
    servers = proc.communicate()[0].splitlines()

    for vm in servers:

        if not(vm == 'Name' and vm == ''):

            proc = subprocess.Popen(["virsh list --all | grep {0} | awk '{{print $3}}'".format(vm)],
                                                                    stdout=subprocess.PIPE, shell=True)
            stdout = proc.communicate()[0].splitlines()
            if stdout == 'running':
                proc = subprocess.Popen('ssh {0} hostname'.format(vm),
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.STDOUT,
                                                    shell=True)
                proc.communicate()
                if proc.returncode == 0:
                    shutdownLinuxVM(vm)
                else:
                    shutdownWindowsVM(vm)

                waitForShutdown(vm)

                proc = subprocess.Popen(["virsh list --all | grep {0} | awk '{{print $3}}'".format(vm)],
                                                                        stdout=subprocess.PIPE, shell=True)
                stdout = proc.communicate()[0].splitlines()
                if stdout == 'running':
                    forceShutdownWindowsVM(vm)
                    waitForShutdown(vm)

                    proc = subprocess.Popen(["virsh list --all | grep {0} | awk '{{print $3}}'".format(vm)],
                                                                            stdout=subprocess.PIPE, shell=True)
                    stdout = proc.communicate()[0].splitlines()
                    if stdout == 'running':
                        logger.info('Failed to shutdown {0}'.format(vm))
                        proc = subprocess.Popen(['cat {0} | mail -s "Failed to shutdown {1}" {2}'.format(LOG_PATH, vm, MAILTO)],
                                                                                            stdout=subprocess.PIPE, shell=True)
                        stdout = proc.communicate()[0]
                        logger.info('Output: {0}'.format(stdout))
                    else:
                        backupVM(vm)
                        startVM(vm)

                else:
                    backupVM(vm)
                    startVM(vm)

            else:
                backupVM(vm)
                startVM(vm)

    logger.info('######## {0} Finished at {1} ########'.format(PRG, time.ctime()))
    proc = subprocess.Popen(['cat logger | mail -s "Backup Script Finished at {0}" {1}'.format(time.ctime(), MAILTO)],
                                                                                    stdout=subprocess.PIPE, shell=True)
    stdout = proc.communicate()[0]
    logger.info('Output: {0}'.format(stdout))
