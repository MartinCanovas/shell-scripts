#!/usr/bin/env python

############################################
# Program:   getSpecs.py
# Author:    Martin Canovas
# Date:      August, 2015
# License:   Public Domain
############################################

DESCRIPTION = """A Python script that remotely connects to linux servers via SSH
                 to get server information and generte a report.
                 The information gather are:
                 - Hostname
                 - Uptime
                 - Total Memomory RAM
                 - Number of CPUs
                 - OS Release Version
                 - Filysystems disk space

                 Make sure all the remote servers have SSH key configured so that
                 this script can connect to them without prompting for password.
              """

import os
import sys
import time
import paramiko
import argparse

source_file = '/home/martin/iplist.txt'
report_file = '/home/martin/report.txt'
date = time.strftime("%d-%m-%Y")
hour = time.strftime("%H:%M:%S")

class linuxCommands():
    def __init__(self):
        self.__hostname = 'hostname'
        self.__uptime = "uptime | awk -F\" \" '{print $3, $4}'"
        self.__ram = 'cat /proc/meminfo | grep MemTotal'
        self.__cpu = 'grep proc /proc/cpuinfo | wc -l'
        self.__os_release = 'cat /etc/system-release'
        self.__filesystems = 'df -h'

    def __str__(self): return self.name

    def getHostname(self): return self.__hostname

    def getUptime(self): return self.__uptime

    def getRam(self): return self.__ram

    def getCpu(self): return self.__cpu

    def getOsRelease(self): return self.__os_release

    def getFilesystem(self): return self.__filesystems

def connectToServer(host, c):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    privatekeyfile = os.path.expanduser('~/.ssh/id_rsa')
    mykey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
    ssh.connect(host, username='root', pkey=mykey)
    stdin, stdout, stderr = ssh.exec_command(c)
    output = stdout.read()
    output = output[:len(output)-1]  # remove newline

    return output

def writeToFile(c, output):
    if c == cmd.getHostname():
        report.write('\n')
        report.write('-------------------------\n')
        report.write('Hostname: ' + str(output) + '\n')
        report.write('\n')
    elif c == cmd.getUptime():
        report.write('Uptime: ' + str(output) + '\n')
    elif c == cmd.getOsRelease():
        report.write('OS Release: ' + str(output) + '\n')
    elif c == cmd.getRam():
        report.write(str(output) + '\n')
    elif c == cmd.getCpu():
        report.write('Number of processors: ' + str(output) + '\n')
    else:
        report.write(str(output) + '\n')

def formatOutput(c, output):
    if c == cmd.getHostname():
        print
        print "Hostname: " + str(output)
    elif c == cmd.getUptime():
        print "Uptime: " + str(output)
    elif c == cmd.getOsRelease():
        print "OS Release: " + str(output)
    elif c == cmd.getRam():
        print str(output)
    elif c == cmd.getCpu():
        print "Number of processors: " + str(output)
    else:
        print
        print str(output)
        print

def getOptions(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description="Parses command.")
    parser.add_argument("-i", "--input", help="Your input file.")
    parser.add_argument("-o", "--output", help="Your destination output file.")
    parser.add_argument("--ip", type=str, help="IP address.")
    args = parser.parse_args(args)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    if args.input:
        if not os.path.exists(args.input):
            print "The file %s does not exist." % args.input
            print
            exit(1)

    return args


# Main code starts here
if __name__ == "__main__":

    cmd = linuxCommands()
    commands = (cmd.getHostname(), cmd.getUptime(), cmd.getOsRelease(),
                cmd.getRam(), cmd.getCpu(), cmd.getFilesystem())

    args = getOptions(sys.argv[1:])

    if args.ip:
        try:
            for command in commands:
                output = connectToServer(args.ip, command)
                formatOutput(command, output)

        except paramiko.AuthenticationException:
            print "Authentication failed when connecting to %s" % args.ip
            sys.exit(1)
        except:
            print "Could not SSH to %s, trying again." % args.ip

    else:

        with open(args.output, 'w') as report:
            report.write(date + ' ' + hour + '\n')

            with open(args.input, 'r') as iplist:
                for server in iplist:
                    server = server[:len(server)-1]
                    print 'Connecting to ', server
                    counter = 1
                    while counter != 5:
                        try:
                            for command in commands:
                                output = connectToServer(server, command)
                                writeToFile(command, output)

                            counter = 5   # reset counter for the next server

                        except paramiko.AuthenticationException:
                            print "Authentication failed when connecting to %s" % server
                            sys.exit(1)
                        except:
                            print "Could not SSH to %s, trying again." % server
                            counter += 1  # try to connect to server until counter = 5
                            time.sleep(2)
                            if counter == 5:
                                print "Could not connect to %s. Giving up" % server
