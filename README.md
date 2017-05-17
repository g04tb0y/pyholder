# PyHolder
A surveillance system with e-mail notification in python for Raspberry Pi using OpenCV and Gmail.
## Getting Started
PyHolder is developed for the Raspberry Pi 3 and his camera module, but should work with any camera compatible with OpenCV and with appropriate library instead of picamera.
The core part, the motion detection code, is taken from [pysearchimage.com](http://www.pyimagesearch.com/) where you can find any additional information about motion detection and OpenCV in general. 

### Prerequisites

In order to run pyholder, you need OpenCV and some python modules.
Using your distro packet manager, for e.g. apt:

```
$ sudo apt-get install libopencv-dev python-opencv

```
then all the python modules using pip:
```
$ sudo pip install picamera argparse imutils smtplib email psutil json
```

### Installing

I strongly suggest you to create a new user that run pyholder and set the privileges to the json config file to something like ```750``` because the email and password are stored in clear text.

You can change the base path using the using the json config file:

```
{
	"send_mail": true,
	"email_sender": "YOUREMAIL",
	"email_recipient": "RECIPEMAIL",
	"email_pwd": "EMAILPASSWORD",
	"base_path": "/home/watchtower/pyholder",
	"log_file": "/home/watchtower/pyholder/log",
	"min_upload_seconds": 1.5,
	"min_motion_frames": 8,
	"camera_warmup_time": 2.5,
	"delta_thresh": 10,
	"resolution": [1920, 1600],
	"fps": 5,
	"min_area": 5000
}
```
The other parameters are pretty clear, i think.
For the parameters of the camera you can find more info here [pysearchimage.com](http://www.pyimagesearch.com/).

PyHolder can be scheduled with a task scheduler like cron, so here an example of crontab configuration:
```markdown
$ crontab -l

00 10 * * 7 /home/watchtower/pyholder/pyholder_agent.py -c /home/watchtower/pyholder/conf.json --start
00 18 * * 7 /home/watchtower/pyholder/pyholder_agent.py -c /home/watchtower/pyholder/conf.json --stop
00 12 * * * /home/watchtower/pyholder/pyholder_agent.py -c /home/watchtower/pyholder/conf.json --agent
00 17 * * * /home/watchtower/pyholder/pyholder_agent.py -c /home/watchtower/pyholder/conf.json --agent


```
In this example the pyholder agent start pyholder every Sunday at 10 am and stop the instance at 6 pm. Then, in agent mode, check if pyholder is running and send an email with the status every day at 12 am and 5 pm.
### 

## Authors

* **Alessandro Bosco**
## License

This project is licensed under the GPLv3 - [www.gnu.org](http://www.gnu.org/licenses/)

## Acknowledgments

* [pysearchimage.com](http://www.pyimagesearch.com/)

