#!/bin/bash
if [[ $EUID -ne 0 ]]; then
  echo "You must be a root user or ´sudo system_init.sh´" 2>&1
  exit 1
fi

cp bin/pi_garage_alert.py /usr/local/sbin/
cp etc/pi_garage_alert_config.py /usr/local/etc/
cp init.d/pi_garage_alert /etc/init.d/
chown pi /usr/local/etc/pi_garage_alert_config.py