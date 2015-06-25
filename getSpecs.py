#!/usr/bin/env python
import sys
import paramiko
from time import strftime

username = 'root'
password = 'PeaxyAdm1n'
hostname = 'hostname'
ram = 'cat /proc/meminfo | grep MemTotal'
cpu = 'grep proc /proc/cpuinfo | wc -l'
os_release = 'cat /etc/system-release'
filesystems = 'df -h'
uptime = "uptime | awk -F\" \" '{print $3, $4}'"

def usage():
    print "Usage: getSpecs.py <hostname | IP Address>"
    exit(1)

try:
    host = str(sys.argv[1])
except:
    usage()

for cmd in [hostname, uptime, os_release, ram, cpu, filesystems]:

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username, password=password)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read()
        output = output[:len(output)-1] #remove newline

        if cmd == hostname:
            print
            print "Hostname: " + str(output)
        elif cmd == uptime:
            print "Uptime: " + str(output)
        elif cmd == os_release:
            print "OS Release: " + str(output)
        elif cmd == ram:
            print str(output)
        elif cmd == cpu:
            print "Number of processors: " + str(output)
        else:
            print str(output)
            print

    except paramiko.AuthenticationException:
        print "Authentication failed when connecting to %s" % host
        sys.exit(1)
