# Bluetooth speaker

Convert a regular speaker as a smart Bluetooth Speaker using a raspberrypi.

Turns on and off the power to the speaker upon bluetooth connection and disconnection.

Automatically mute sounds when Spotify Ads are detected.

## Setup

This project uses the following hardware:
* Raspberrypi B with raspbian OS
* A TpLink smart plug supporting the Kasa API (for example: HS100)
* Any regular speaker, plugged via 3.5mm Jack to the Raspberrypi and powered through the smart plug


Setting the raspberry as a speaker is done following this tutorial: https://forums.raspberrypi.com/viewtopic.php?t=235519

##  This project adds two scripts run as services:

### avrcp-volume-watcher
This script is needed for better volume control when pressing volume buttons on the emitting device.

It watches A2DP bluetooth properties through dbus and applies volume changes to the raspberrypi main volume using `amixer`

**Service file**

`/etc/systemd/system/avrcp-volume-watcher.service`
```
[Unit]
Description=Bluetooth AVRCP Volume Watcher Agent
After=bluetooth.service
PartOf=bluetooth.service

[Service]
Type=simple
KillSignal=SIGINT
ExecStart=/usr/bin/python /root/bluetooth_speaker/avrcp_volume_watcher.py

[Install]
WantedBy=default.target
```

**Starting service**

```
systemctl enable avrcp-volume-watcher
systemctl start avrcp-volume-watcher
systemctl status avrcp-volume-watcher
```

### dbus-conn-watcher
This is the smart part of the project:
* Mutes the audio if the music played is a Spotify Ad (Configure with `BLACKLISTED_TITLES`)
* Turns on and off the smart plug when a device is connected and disconnected, this avoids keeping the speaker on at all times (Configure paths with `PATH_TO_SMARTPLUG_TURN..`)
* Only turn on when the MAC of the connecting device is in a whitelist (Configure with `MAC_WHITELIST`)


**Service file**

`/etc/systemd/system/dbus-conn-watcher.service`
```
[Unit]
Description=Dbus connection watcher, launches smartplug
After=bluetooth.service
PartOf=bluetooth.service

[Service]
Type=simple
KillSignal=SIGINT
ExecStart=/usr/bin/python /root/bluetooth_speaker/connection_watcher.py

[Install]
WantedBy=default.target
```

**Starting service**

```
systemctl enable dbus-conn-watcher
systemctl start dbus-conn-watcher
systemctl status dbus-conn-watcher
```

### Library requirements
The code is run with `python2.7`, kasa scripts are run with `python3.8`

`python-dbus` is needed in order to parse Dbus events `sudo apt install python-dbus`

`python-kasa` is used to communicate with the smart plug https://github.com/python-kasa/python-kasa
