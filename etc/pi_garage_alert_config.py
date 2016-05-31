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
                'recipients': [ 'sms:+16512700143', 'sms:+6514970027', 'PiBusHub']
            },
            {
                'state': 'open',
                'time': 600,
                'recipients': [ 'sms:+16512700143', 'sms:+6514970027', 'PiBusHub']
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
                'recipients': [ 'sms:+16512700143', 'sms:+6514970027', 'PiBusHub']
            },
            {
                'state': 'open',
                'time': 600,
                'recipients': [ 'sms:+16512700143', 'sms:+6514970027', 'PiBusHub']
            }
        ]
    }
]

# All messages will be logged to stdout and this file
LOG_FILENAME = "/var/log/pi_garage_alert.log"

##############################################################################
# PiBus settings
##############################################################################

PUBNUB_PUBLISH_KEY = 'pub-c-94d584c4-5413-472c-b3e8-92d273338c8e'
PUBNUB_SUBSCRIBE_KEY = 'sub-c-29c58bda-2651-11e6-9a17-0619f8945a4f'
PUBNUB_CHANNEL_KEY = 'Mongo'

##############################################################################
# Twilio settings
##############################################################################

# Sign up for a Twilio account at https://www.twilio.com/
# then these will be listed at the top of your Twilio dashboard

TWILIO_ACCOUNT = 'AC4f4d140a4bbd4952c254502989aeab5a'
TWILIO_TOKEN = '9ff609d40eaee5378dd6cdb6f732729f'

# SMS will be sent from this phone number
TWILIO_PHONE_NUMBER = '+17639511653'
