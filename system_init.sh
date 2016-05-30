#!/bin/bash
if [[ $EUID -ne 0 ]]; then
  echo "You must be a root user or ´sudo system_init.sh´" 2>&1
  exit 1
fi

apt-get install python-setuptools python-dev libffi-dev
easy_install pip
pip install pubnub
pip install tweepy
pip install twilio
pip install sleekxmpp dnspython pyasn1 pyasn1_modules
pip install requests
pip install requests[security]

git config --global user.email "steve.hebert@gmail.com"
git config --global user.name "Steve Hebert"

