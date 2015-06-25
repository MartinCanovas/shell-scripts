#!/usr/bin/env python
import sys
import paramiko
from time import strftime

iplist = open('/home/martin/iplist.txt', 'r')
report = open('/home/martin/report.txt', 'w')
username = 'root'
password = 'PeaxyAdm1n'

hostname = 'hostname'
ram = 'cat /proc/meminfo | grep MemTotal'
cpu = 'grep proc /proc/cpuinfo | wc -l'
os_release = 'cat /etc/system-release'
filesystems = 'df -h'
uptime = "uptime | awk -F\" \" '{print $3, $4}'"

i = 1
date = strftime("%d-%m-%Y")
time = strftime("%H:%M:%S")
print >> report, date, time

for data in iplist:

    host = data

    for cmd in [hostname, uptime, os_release, ram, cpu, filesystems]:

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=username, password=password)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output = stdout.read()
            output = output[:len(output)-1] #remove newline

            if cmd == hostname:
                print >> report
                print >> report, "-------------------------"
                print >> report, "Hostname: " + str(output)
            elif cmd == uptime:
                print >> report, "Uptime: " + str(output)
            elif cmd == os_release:
                print >> report, "OS Release: " + str(output)
            elif cmd == ram:
                print >> report, str(output)
            elif cmd == cpu:
                print >> report, "Number of processors: " + str(output)
            else:
                print >> report, str(output)

        except paramiko.AuthenticationException:
            print "Authentication failed when connecting to %s" % host
            sys.exit(1)
        except:
            print "Could not SSH to %s, waiting for it to start" % host
            i += 1
            time.sleep(2)

        if i == 10:
            print "Could not connect to %s. Giving up" % host
            sys.exit(1)



report.close()
iplist.close()
