#!/usr/bin/python

import os
import sys
import logging
import logging.handlers
import signal
import dbus
import dbus.service
import dbus.mainloop.glib

try:
    import gobject
except ImportError:
    from gi.repository import GObject as gobject

LOG_NAME = 'connection-detector'
#LOG_LEVEL = logging.INFO
LOG_LEVEL = logging.DEBUG
LOG_FORMAT = '%(name)s[%(process)d]: %(message)s'

# Add allowed MAC address of trusted devices,
# MACs must be formated with underscores between bytes
MAC_WHITELIST = ["AA_BB_CC_DD_EE_FF"]

# Paths to smartplug control scripts
PATH_TO_SMARTPLUG_TURNON = '/root/bluetooth_speaker/kasa/turnon.sh'
PATH_TO_SMARTPLUG_TURNOFF = '/root/bluetooth_speaker/kasa/turnoff.sh'

# Song titles requiring sound to be muted (Ads)
BLACKLISTED_TITLES = ["Advertisement", "Spotify", ""]

def shutdown(signum, frame):
    mainloop.quit()

def get_current_volume():
    # Parses amixer output to retrieve current volume
    return os.popen('amixer | grep -Po "[0-9]*%"').read()[:-2]

def set_volume(volume):
    # Uses amixer to set current volume
    os.system('amixer set PCM {}%'.format(volume))

def is_path_containing_whitelisted_mac(path):
    for mac in MAC_WHITELIST:
        if mac in path:
            return True
    return False

def device_property_changed(interface, properties, invalidated, path):
    global current_volume, last_song_was_an_ad
    """ Check for changes in org.bluez object tree

    Check for Volume change event and State = active event
    Retrieve the volume value and set pulseaudio source accordingly

    Args:
        interface(string) : name of the dbus interface where changes occured
        properties(dict) : list of all parameters changed and their new value
        invalidated(array) : list of properties invalidated
        path(string) : path of the dbus object that triggered the call
    """

    if interface == 'org.bluez.Device1' and is_path_containing_whitelisted_mac(path):
        if 'Connected' in properties:
            connected = properties['Connected']
            logger.debug("connected" + str(bool(connected)))
            if bool(connected):
                os.system(PATH_TO_SMARTPLUG_TURNON)
            else:
                os.system(PATH_TO_SMARTPLUG_TURNOFF)
    if interface == 'org.bluez.MediaPlayer1':
        if 'Track' in properties:
            logger.debug("TRACK TITLE")
            try:
                title = properties['Track']['Title']
            except:
                logger.debug("No title could be found, probably an ad")
                title = ""
            logger.debug(title)
            if title in BLACKLISTED_TITLES:
                logger.debug("Ad detected, cutting volume")
                if not last_song_was_an_ad:
                    current_volume = get_current_volume()
                last_song_was_an_ad = True
                set_volume(10)
            else:
                logger.debug("Not an ad, volume up")
                last_song_was_an_ad = False
                set_volume(current_volume)

if __name__ == '__main__':
    # Get base volume at the start of the script
    current_volume = get_current_volume()
    last_song_was_an_ad = False
    # shut down on a TERM signal
    signal.signal(signal.SIGTERM, shutdown)

    # Create logger
    logger = logging.getLogger(LOG_NAME)
    logger.setLevel(LOG_LEVEL)

    # Choose between /var/log/syslog or current stdout
#    ch = logging.handlers.SysLogHandler(address = '/dev/log')
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(fmt=LOG_FORMAT))
    logger.addHandler(ch)
    logger.info('Started')

    # Get the system bus
    try:
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SystemBus()
    except Exception as ex:
        logger.error('Unable to get the system dbus: "{0}". Exiting. Is dbus running?'.format(ex.message))
        sys.exit(1)

    # listen for PropertyChanged signal on org.bluez
    bus.add_signal_receiver(
        device_property_changed,
        bus_name='org.bluez',
        signal_name='PropertiesChanged',
        dbus_interface='org.freedesktop.DBus.Properties',
        path_keyword='path'
        )

    try:
        mainloop = gobject.MainLoop()
        mainloop.run()
    except KeyboardInterrupt:
        pass
