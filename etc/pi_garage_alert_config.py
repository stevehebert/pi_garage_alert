#!/usr/bin/python2.7

##############################################################################
# Global settings
##############################################################################

# Describes all the garage doors being monitored
GARAGE_DOORS = [
    {
        'pin': 16,
        'name': "Small Garage Door",
        'alerts': [
            {
                'state': 'open',
                'time': 120,
                'recipients': [ 'sms:+16512700143', 'sms:+6514970027']
            },
            {
                'state': 'open',
                'time': 600,
                'recipients': [ 'sms:+16512700143', 'sms:+6514970027']
            }
        ]
    },

    {
        'pin': 15,
        'name': "Main Garage Door",
        'alerts': [
            {
                'state': 'open',
                'time': 120,
                'recipients': [ 'sms:+16512700143', 'sms:+6514970027']
            },
            {
                'state': 'open',
                'time': 600,
                'recipients': [ 'sms:+16512700143', 'sms:+6514970027']
            }
        ]
    }
]

# All messages will be logged to stdout and this file
LOG_FILENAME = "/var/log/pi_garage_alert.log"

##############################################################################
# Email settings
##############################################################################

SMTP_SERVER = 'localhost'
SMTP_PORT = 25
SMTP_USER = ''
SMTP_PASS = ''
EMAIL_FROM = 'Garage Door <user@example.com>'

##############################################################################
# Twitter settings
##############################################################################

# Follow the instructions on http://talkfast.org/2010/05/31/twitter-from-the-command-line-in-python-using-oauth/
# to obtain the necessary keys

TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET = ''
TWITTER_ACCESS_KEY = ''
TWITTER_ACCESS_SECRET = ''

##############################################################################
# Twilio settings
##############################################################################

# Sign up for a Twilio account at https://www.twilio.com/
# then these will be listed at the top of your Twilio dashboard

TWILIO_ACCOUNT = ''
TWILIO_TOKEN = ''

# SMS will be sent from this phone number
TWILIO_PHONE_NUMBER = '+11234567890'

##############################################################################
# Jabber settings
##############################################################################

# Jabber ID and password that status updates will be sent from
# Leave this blank to disable Jabber support

JABBER_ID = ''
JABBER_PASSWORD = ''

# Uncomment to override the default server specified in DNS SRV records

#JABBER_SERVER = 'talk.google.com'
#JABBER_PORT = 5222

# List of Jabber IDs allowed to perform queries

JABBER_AUTHORIZED_IDS = []

##############################################################################
# Google Cloud Messaging settings
##############################################################################

GCM_KEY = ''
GCM_TOPIC = ''