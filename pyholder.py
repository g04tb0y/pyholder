#! /usr/bin/python

from picamera.array import PiRGBArray
from picamera import PiCamera
from pymailer.mailer import Mailer, MailerAgent
import argparse
import warnings
import datetime
from threading import Thread
import imutils
import json
import time
import cv2
import sys, os
import logging


def main():
    # Init logging
    logging.basicConfig(format='%(levelname)s - %(funcName)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'
                       , level=logging.INFO, filename=conf['log_file'])
    logging.info('Starting Pyholder...')
    logging.info('PiCamera warming up...')
    camera = PiCamera()
    camera.resolution = tuple(conf["resolution"])
    camera.framerate = conf["fps"]
    rawCapture = PiRGBArray(camera, size=tuple(conf["resolution"]))

    # allow the camera to warmup, then initialize the average frame, last
    # uploaded timestamp, and frame motion counter
    time.sleep(conf["camera_warmup_time"])
    avg = None
    lastUploaded = datetime.datetime.now()
    motionCounter = 0

    # Create a PID file
    # pid = str(os.getpid())
    # pidfile = conf["pid_file"]
    # logging.debug('PID file created: {}'.format(pidfile))
    # file(pidfile, 'w').write(pid)

    try:
        thread_magent = MailerAgent("PyHolder has been started!\n", conf["email_sender"], conf["email_recipient"], conf["email_pwd"], conf['log_file'])
        thread_magent.start()
        # capture frames from the camera
        for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            # grab the raw NumPy array representing the image and initialize the timestamp
            frame = f.array
            timestamp = datetime.datetime.now()
            detected = False

            # resize the frame, convert it to grayscale, and blur it
            frame2 = imutils.resize(frame, width=500)
            gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            # if the average frame is None, initialize it
            if avg is None:
                logging.debug('Init background model...')
                avg = gray.copy().astype("float")
                rawCapture.truncate(0)
                continue

            # accumulate the weighted average between the current frame and
            # previous frames, then compute the difference between the current
            # frame and running average
            cv2.accumulateWeighted(gray, avg, 0.5)
            frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

            # threshold the delta image, dilate the thresholded image to fill
            # in holes, then find contours on thresholded image
            thresh = cv2.threshold(frameDelta, conf["delta_thresh"], 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # loop over the contours
            for c in cnts:
                # if the contour is too small, ignore it
                if cv2.contourArea(c) < conf["min_area"]:
                    continue

                # Motion detected
                detected = True

            # Check if a motion was detected
            if detected:
                # Check if enough time has passed between uploads
                if (timestamp - lastUploaded).seconds >= conf["min_upload_seconds"]:
                    # increment the motion counter
                    motionCounter += 1

                    # Check if send mail is enable
                    if conf["send_mail"]:
                        # write the frame on file system
                        ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
                        path = "{base_path}/{timestamp}.jpg".format(base_path=conf["base_path"], timestamp=ts)
                        cv2.imwrite(path, frame)

                        logging.info('Motion detected! Sendig frame via email')
                        # Init Mailer Thread
                        thread_mailer = Mailer(path, conf["email_sender"], conf["email_recipient"], conf["email_pwd"], conf['log_file'])
                        t_msg_list.append(thread_mailer)
                        # thread_mailer.start()
                    else:
                        logging.info('Motion detected but not sending email')
                    # update the last uploaded timestamp and reset the motion counter
                    lastUploaded = timestamp
                    motionCounter = 0

            # otherwise no detection
            else:
                motionCounter = 0
            # flush the stream
            rawCapture.truncate(0)

    except Exception as e:
        thread_magent = MailerAgent("PyHolder has been terminated unexpectedly!\n{}".format(sys.exc_info())
                                    , conf["email_sender"], conf["email_recipient"],
                                    conf["email_pwd"], conf['log_file'])
        thread_magent.start()
        thread_mailer.join(timeout=1)
        logging.error('Pyholder shutting down unexpected!\n{}'.format(e))

    finally:
        thread_magent = MailerAgent("PyHolder has been shutdown!\n{}".format(sys.exc_info())
                                    , conf["email_sender"], conf["email_recipient"],
                                    conf["email_pwd"], conf['log_file'])
        thread_magent.start()
        thread_mailer.join(timeout=1)
        logging.info('Pyholder shutting down...bye!')


# Start thread from the list every 5 sec.
def sequencer():
    while True:
        if t_msg_list:
            msg = t_msg_list.pop()
            time.sleep(5)
            logging.debug(msg)
            msg.start()


if __name__ == "__main__":
    # argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--conf", required=True, help="path to the JSON configuration file")
    args = vars(ap.parse_args())

    # filter warnings, load the configuration
    warnings.filterwarnings("ignore")
    conf = json.load(open(args["conf"]))

    # Init the message list
    t_msg_list = []
    t_sequencer = Thread(target=sequencer, name='sequencer')
    try:
        t_sequencer.start()
    except Exception as e:
        logging.error('Error while starting sequencer\n{}'.format(e))
    main()
