#!/usr/bin/python2.7
""" Pi Garage Alert

Author: Richard L. Lynch <rich@richlynch.com>

Description: Emails, tweets, or sends an SMS if a garage door is left open
too long.

Learn more at http://www.richlynch.com/code/pi_garage_alert
"""

##############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) 2013-2014 Richard L. Lynch <rich@richlynch.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
##############################################################################

import time
from time import strftime
import subprocess
import re
import sys
import json
import logging
from datetime import timedelta
import smtplib
import ssl
import traceback
from email.mime.text import MIMEText

import requests
import tweepy
import RPi.GPIO as GPIO
import httplib2
import sleekxmpp
from sleekxmpp.xmlstream import resolver, cert
from twilio.rest import TwilioRestClient
from twilio.rest.exceptions import TwilioRestException
from pubnub import Pubnub

sys.path.append('/usr/local/etc')
import pi_garage_alert_config as cfg

##############################################################################
# PiBusHub Support
##############################################################################
class PiBusHub(object):
  def __init__(self):
    self.logger = logging.getLogger(__name__)
    if not hasattr(cfg, 'PUBNUB_CHANNEL_KEY'):
      self.logger.debug("PubNub[ChannelKey] not defined - PubNub support disabled")
    if not hasattr(cfg, 'PUBNUB_PUBLISH_KEY'):
      self.logger.debug("PubNub[PublishKey] not defined - PubNub support disabled")
      return
    if cfg.PUBNUB_PUBLISH_KEY == '':
      self.logger.debug("PubNub[PublishKey] not configured - PubNub support disabled")
      return

    if not hasattr(cfg, 'PUBNUB_SUBSCRIBE_KEY'):
      self.logger.debug("PubNub[SubscribeKey] not defined - PubNub support disabled")
      return

    self.logger.debug("PubNub registering: " +cfg.PUBNUB_PUBLISH_KEY + " : " + cfg.PUBNUB_SUBSCRIBE_KEY)

    self.pubnub = Pubnub(publish_key=cfg.PUBNUB_PUBLISH_KEY, subscribe_key=cfg.PUBNUB_SUBSCRIBE_KEY)
    
    
    if cfg.PUBNUB_SUBSCRIBE_KEY != '':
      self.logger.info("PubNub subscribing: " + cfg.PUBNUB_CHANNEL_KEY)
      self.pubnub.subscribe(channels=cfg.PUBNUB_CHANNEL_KEY, callback=self.callback, error=self.error, connect=self.connect, reconnect=self.reconnect, disconnect=self.disconnect)


  def callback(self, message, channel):
    print("CALLBACK: " + message +":" + channel)
  
  
  def error(message):
    print("ERROR : " + str(message))
  
  
  def connect(self, channel):
    print("CONNECTED: " +channel)
    self.pubnub.publish(channel='Mongo', message='Hello from the PubNub Python SDK')
  
  
  
  def reconnect(message):
    print("RECONNECTED:" + message)
  
  
  def disconnect(message):
    print("DISCONNECTED:" + message)

  def publish(self, message):
    print("PUBLISH:" + message)
    self.pubnub.publish(channel=cfg.PUBNUB_CHANNEL_KEY, message=message)
  
  


##############################################################################
# Twilio support
##############################################################################

class Twilio(object):
    """Class to connect to and send SMS using Twilio"""

    def __init__(self):
        self.twilio_client = None
        self.logger = logging.getLogger(__name__)

    def send_sms(self, recipient, msg):
        """Sends SMS message to specified phone number using Twilio.

        Args:
            recipient: Phone number to send SMS to.
            msg: Message to send. Long messages will automatically be truncated.
        """

        # User may not have configured twilio - don't initialize it until it's
        # first used
        if self.twilio_client is None:
            self.logger.info("Initializing Twilio")

            if cfg.TWILIO_ACCOUNT == '' or cfg.TWILIO_TOKEN == '':
                self.logger.error("Twilio account or token not specified - unable to send SMS!")
            else:
                self.twilio_client = TwilioRestClient(cfg.TWILIO_ACCOUNT, cfg.TWILIO_TOKEN)

        if self.twilio_client != None:
            self.logger.info("Sending SMS to %s: %s", recipient, msg)
            try:
                self.twilio_client.sms.messages.create(
                    to=recipient,
                    from_=cfg.TWILIO_PHONE_NUMBER,
                    body=truncate(msg, 140))
            except TwilioRestException as ex:
                self.logger.error("Unable to send SMS: %s", ex)
            except httplib2.ServerNotFoundError as ex:
                self.logger.error("Unable to send SMS - internet connectivity issues: %s", ex)
            except:
                self.logger.error("Exception sending SMS: %s", sys.exc_info()[0])


##############################################################################
# Sensor support
##############################################################################

def get_garage_door_state(pin):
    """Returns the state of the garage door on the specified pin as a string

    Args:
        pin: GPIO pin number.
    """
    if GPIO.input(pin): # pylint: disable=no-member
        state = 'open'
    else:
        state = 'closed'

    return state

def get_uptime():
    """Returns the uptime of the RPi as a string
    """
    with open('/proc/uptime', 'r') as uptime_file:
        uptime_seconds = int(float(uptime_file.readline().split()[0]))
        uptime_string = str(timedelta(seconds=uptime_seconds))
    return uptime_string

def get_gpu_temp():
    """Return the GPU temperature as a Celsius float
    """
    cmd = ['vcgencmd', 'measure_temp']

    measure_temp_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output = measure_temp_proc.communicate()[0]

    gpu_temp = 'unknown'
    gpu_search = re.search('([0-9.]+)', output)

    if gpu_search:
        gpu_temp = gpu_search.group(1)

    return float(gpu_temp)

def get_cpu_temp():
    """Return the CPU temperature as a Celsius float
    """
    cpu_temp = 'unknown'
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as temp_file:
        cpu_temp = float(temp_file.read()) / 1000.0

    return cpu_temp

def rpi_status():
    """Return string summarizing RPi status
    """
    return "CPU temp: %.1f, GPU temp: %.1f, Uptime: %s" % (get_gpu_temp(), get_cpu_temp(), get_uptime())

##############################################################################
# Logging and alerts
##############################################################################

def send_alerts(logger, alert_senders, recipients, subject, msg, state):
    """Send subject and msg to specified recipients

    Args:
        recipients: An array of strings of the form type:address
        subject: Subject of the alert
        msg: Body of the alert
        state: The state of the door
    """
    for recipient in recipients:
        if recipient[:8] == 'PiBusHub':
            alert_senders['PiBusHub'].publish(msg)
        elif recipient[:4] == 'sms:':
            alert_senders['Twilio'].send_sms(recipient[4:], msg)
        else:
            logger.error("Unrecognized recipient type: %s", recipient)

##############################################################################
# Misc support
##############################################################################

def truncate(input_str, length):
    """Truncate string to specified length

    Args:
        input_str: String to truncate
        length: Maximum length of output string
    """
    if len(input_str) < (length - 3):
        return input_str

    return input_str[:(length - 3)] + '...'

def format_duration(duration_sec):
    """Format a duration into a human friendly string"""
    days, remainder = divmod(duration_sec, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    ret = ''
    if days > 1:
        ret += "%d days " % (days)
    elif days == 1:
        ret += "%d day " % (days)

    if hours > 1:
        ret += "%d hours " % (hours)
    elif hours == 1:
        ret += "%d hour " % (hours)

    if minutes > 1:
        ret += "%d minutes" % (minutes)
    if minutes == 1:
        ret += "%d minute" % (minutes)

    if ret == '':
        ret += "%d seconds" % (seconds)

    return ret


##############################################################################
# Main functionality
##############################################################################
class PiGarageAlert(object):
    """Class with main function of Pi Garage Alert"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def main(self):
        """Main functionality
        """

        try:
            # Set up logging
            log_fmt = '%(asctime)-15s %(levelname)-8s %(message)s'
            log_level = logging.DEBUG

            if sys.stdout.isatty():
                # Connected to a real terminal - log to stdout
                logging.basicConfig(format=log_fmt, level=log_level)
            else:
                # Background mode - log to file
                logging.basicConfig(format=log_fmt, level=log_level, filename=cfg.LOG_FILENAME)

            # Banner
            self.logger.info("==========================================================")
            self.logger.info("Pi Garage Alert starting")

            # Use Raspberry Pi board pin numbers
            self.logger.info("Configuring global settings")
            GPIO.setmode(GPIO.BOARD)

            # Configure the sensor pins as inputs with pull up resistors
            for door in cfg.GARAGE_DOORS:
                self.logger.info("Configuring pin %d for \"%s\"", door['pin'], door['name'])
                GPIO.setup(door['pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Last state of each garage door
            door_states = dict()

            # time.time() of the last time the garage door changed state
            time_of_last_state_change = dict()

            # Index of the next alert to send for each garage door
            alert_states = dict()

            # Create alert sending objects
            alert_senders = {
                "PiBusHub": PiBusHub(),
                "Twilio": Twilio()
            }

            # Read initial states
            for door in cfg.GARAGE_DOORS:
                name = door['name']
                state = get_garage_door_state(door['pin'])

                door_states[name] = state
                time_of_last_state_change[name] = time.time()
                alert_states[name] = 0

                self.logger.info("Initial state of \"%s\" is %s", name, state)

            status_report_countdown = 5
            while True:
                for door in cfg.GARAGE_DOORS:
                    name = door['name']
                    state = get_garage_door_state(door['pin'])
                    time_in_state = time.time() - time_of_last_state_change[name]

                    # Check if the door has changed state
                    if door_states[name] != state:
                        door_states[name] = state
                        time_of_last_state_change[name] = time.time()
                        self.logger.info("State of \"%s\" changed to %s after %.0f sec", name, state, time_in_state)

                        # Reset alert when door changes state
                        if alert_states[name] > 0:
                            # Use the recipients of the last alert
                            recipients = door['alerts'][alert_states[name] - 1]['recipients']
                            send_alerts(self.logger, alert_senders, recipients, name, "%s is now %s" % (name, state), state)
                            alert_states[name] = 0

                        # Reset time_in_state
                        time_in_state = 0

                    # See if there are more alerts
                    if len(door['alerts']) > alert_states[name]:
                        # Get info about alert
                        alert = door['alerts'][alert_states[name]]

                        # Has the time elapsed and is this the state to trigger the alert?
                        if time_in_state > alert['time'] and state == alert['state']:
                            send_alerts(self.logger, alert_senders, alert['recipients'], name, "%s has been %s for %d seconds!" % (name, state, time_in_state), state)
                            alert_states[name] += 1

                # Periodically log the status for debug and ensuring RPi doesn't get too hot
                status_report_countdown -= 1
                if status_report_countdown <= 0:
                    status_msg = rpi_status()

                    for name in door_states:
                        status_msg += ", %s: %s/%d/%d" % (name, door_states[name], alert_states[name], (time.time() - time_of_last_state_change[name]))

                    self.logger.info(status_msg)

                    status_report_countdown = 600

                # Poll every 1 second
                time.sleep(1)
        except KeyboardInterrupt:
            logging.critical("Terminating due to keyboard interrupt")
        except:
            logging.critical("Terminating due to unexpected error: %s", sys.exc_info()[0])
            logging.critical("%s", traceback.format_exc())

        GPIO.cleanup() # pylint: disable=no-member

if __name__ == "__main__":
    PiGarageAlert().main()
