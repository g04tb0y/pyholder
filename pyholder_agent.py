#!/usr/bin/env python
########################################################################
# Copyright (C) 2017  Alessandro "g04tb0y" Bosco                       #
#                                                                      #
# This program is free software: you can redistribute it and/or modify #
# it under the terms of the GNU General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or    #
# (at your option) any later version.                                  #
#                                                                      #
# Foobar is distributed in the hope that it will be useful,            #
# but WITHOUT ANY WARRANTY; without even the implied warranty of       #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        #
# GNU General Public License for more details.                         #
#                                                                      #
# You should have received a copy of the GNU General Public License    #
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.      #
########################################################################
import psutil
import argparse
import warnings
import json
import logging
import subprocess
import time
import os
import urllib2
from datetime import datetime
from subprocess import Popen
from pymailer.mailer import MailerAgent


def on_line():
    try:
        # Check if google.it is reachable
        urllib2.urlopen('http://216.58.205.227', timeout=1)
        return True
    except Exception as e:
        return False


def agent():

    time.sleep(args["delay"])
    # Check CPU temperature
    temp_cmd = '/usr/bin/vcgencmd measure_temp'
    temp = subprocess.check_output(temp_cmd, shell=True)
    log_cmd = 'tail -n40 {}'.format(conf["log_file"])
    log = subprocess.check_output(log_cmd, shell=True)
    space = str(psutil.disk_usage('/'))

    # Check if PyHolder is running
    for process in psutil.process_iter():
        if "pyholder.py" in str(process.cmdline()):
            logging.info('[AGENT] Pyholder instance found')
            msg = "PyHolder instance found:\n{}".format(process.cmdline())
            msg += "\nCreated at: {}".format(datetime.fromtimestamp(process.create_time()).strftime("%Y-%m-%d %H:%M:%S"))
            msg += "\nCPU usage: {}".format(psutil.cpu_percent(interval=1, percpu=True))
            msg += "\nCPU temp: {}".format(temp)
            msg += "\nDisk usage: {}".format(space)
            msg += "\nActive connection:\n{}".format(psutil.net_connections('inet4'))
            msg += "\nLast log entries:\n{}".format(log)
            thread_magent = MailerAgent(msg, conf["email_sender"], conf["email_recipient"],
                                        conf["email_pwd"], conf['log_file'])
            thread_magent.start()
            break

    else:
        logging.info('[AGENT] No Pyholder instance found')
        thread_magent = MailerAgent("No PyHolder running instance" + "\nCPU temp: {}\nDisk usage: {}".format(temp,space),
                                    conf["email_sender"],
                                    conf["email_recipient"],
                                    conf["email_pwd"], conf['log_file'])
        thread_magent.start()


def start():
    # Check if PyHolder is already running
    for process in psutil.process_iter():
        if "pyholder.py" in str(process.cmdline()):
            logging.info("[Starter] Process found. Terminating it.")
            process.terminate()
            break
    logging.info('[Starter] Starting PyHolder...')
    Popen(['python', '/home/watchtower/pyholder/pyholder.py', '-c', args["conf"]])


def stop():
    # Check if PyHolder is running and kill it
    for process in psutil.process_iter():
        if "pyholder.py" in str(process.cmdline()):
            logging.info('[TERMINATOR] Process found. Terminating it.')
            process.terminate()
            thread_magent = MailerAgent("PyHolder instance terminated:\n" + str(process.cmdline()),
                                        conf["email_sender"],
                                        conf["email_recipient"],
                                        conf["email_pwd"], conf['log_file'])
            thread_magent.start()
            break

    else:
        logging.info('[TERMINATOR] No PyHolder running instance')
        thread_magent = MailerAgent("No PyHolder running instance", conf["email_sender"],
                                    conf["email_recipient"],
                                    conf["email_pwd"], conf['log_file'])
        thread_magent.start()


if __name__ == "__main__":
    # argument parser
    ap = argparse.ArgumentParser(prog="PyHolder")
    ap.add_argument("-c", "--conf", required=True, help="path to the JSON configuration file")
    ap.add_argument('--start', action='store_true', dest="start", help="Start a %(prog)s instance.")
    ap.add_argument('--stop', action='store_true', dest="stop",
                    help="Stop any %(prog)s instance. will be ignored if the option --start is set")
    ap.add_argument('--agent', action='store_true', dest="agent",
                    help="Send information about any current %(prog)s instance running and general system information")
    ap.add_argument('-d', '--delay', type=int, default=0, dest="delay",
                    help="Set a delay for the agent, useful when the agent is scheduled at boot time and"
                         " a couples of minutes are needed before the connection is up")
    args = vars(ap.parse_args())

    # filter warnings, load the configuration
    warnings.filterwarnings("ignore")
    conf = json.load(open(args["conf"]))
    # Init logger
    logging.basicConfig(format='%(levelname)s - %(funcName)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'
                           , level=logging.INFO, filename=conf['log_file'])

    # Clean log file if is too big
    f_info = os.stat(conf['log_file'])
    if f_info.st_size > 1073741824:
        os.remove(conf['log_file'])

    # Check connection
    while not on_line():
        logging.error("No internet connection!")
        time.sleep(60)

    # Handle the input argument mutually exclusive
    if args["start"]:
        start()
    elif args["stop"]:
        stop()
    if args["agent"]:
        agent()
