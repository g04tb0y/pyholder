#!/usr/bin/env python
import smtplib, time, sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import socket
import threading
import os
import logging


# Send an email with file attached
class Mailer(threading.Thread):
    def __init__(self, path, sender, recip, passwd, log_file):
        threading.Thread.__init__(self)
        self.path = path
        self.sender = sender
        self.recip = recip
        self.passwd = passwd
        self.log_file = log_file

    def run(self):
        sendmail(self.path, self.sender, self.recip, self.passwd , self.log_file)
        logging.debug('Starting thread...')


# Send an email with message only
class MailerAgent(threading.Thread):
    def __init__(self, msg, sender, recip, passwd, log_file):
        threading.Thread.__init__(self)
        self.msg = msg
        self.sender = sender
        self.recip = recip
        self.passwd = passwd
        self.log_file = log_file

    def run(self):
        sendmail_agent(self.msg, self.sender, self.recip, self.passwd, self.log_file)
        logging.debug('Starting thread...')


def sendmail(path, sender, recip, passwd, log_file):
    logging.basicConfig(format='%(levelname)s - %(funcName)s:%(threadName)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'
                        , level=logging.INFO, filename=log_file)
    logging.info('Starting mailer...')

    # Initializing th message
    msg = MIMEMultipart()

    msg['From'] = sender
    msg['To'] = recip
    msg['Subject'] = "PyHolder Intrusion Detected %s" % datetime.now()

    body = "Snapshot detected\n %s \n%s\n" % (path, datetime.now())

    # Attachment
    msg.attach(MIMEText(body, 'plain'))

    filename = path.split('/')[-1]
    try:
        attachment = open(path, "rb")
    except Exception as e:
        logging.error('Enable to open file {}\n{}'.format(path, e))
        return

    logging.debug('Opened file {} in {}'.format(filename, path))
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)

    msg.attach(part)
    timeout = 30

    while True:
        try:
            logging.debug('SSL connection to google smtp...')
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            logging.debug('EHLO')
            server.ehlo()
            logging.debug('Login...')
            server.login(sender, passwd)
            text = msg.as_string()
            logging.debug('Sending to {}...'.format(recip))
            server.sendmail(sender, recip, text)
            logging.info('Email sent to {}'.format(recip))
            server.quit()
            break
        except (smtplib.SMTPException, socket.timeout) as e:
            # Catch a connection error and wait for another try
            logging.error('Connection to google.com failed, wait and retry:\n{}'.format(e))
            time.sleep(timeout)
            timeout = timeout * 2
            continue
        except Exception as e:
            logging.error('Error while sending mail:\n{}'.format(e))

    os.remove(path)


# Send an email with a text message
def sendmail_agent(amsg, sender, recip, passwd, log_file):
    logging.basicConfig(format='%(levelname)s - %(funcName)s:%(threadName)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'
                        , level=logging.INFO, filename=log_file)
    logging.debug('Starting mailer agent...')

    # Initializing th message
    msg = MIMEMultipart()

    msg['From'] = sender
    msg['To'] = recip
    msg['Subject'] = "PyHolder Agent %s" % datetime.now()

    body = "\n%s\n%s\n" % (amsg, datetime.now())
    msg.attach(MIMEText(body, 'plain'))
    timeout = 30

    while True:
        try:
            logging.debug('SSL connection to google smtp...')
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            logging.debug('EHLO')
            server.ehlo()
            logging.debug('Login...')
            server.login(sender, passwd)
            text = msg.as_string()
            logging.debug('Sending to {}...'.format(recip))
            server.sendmail(sender, recip, text)
            logging.info('Email sent to {}'.format(recip))
            server.quit()
            break
        except (smtplib.SMTPException, socket.timeout) as e:
            # Catch a connection error and wait for another try
            logging.error('Connection to google.com failed, wait and retry:\n{}'.format(e))
            time.sleep(timeout)
            timeout = timeout * 2
            continue
        except Exception as e:
            logging.error('Error while sending mail:\n{}'.format(e))
