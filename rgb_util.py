import json
import threading
import time
import pigpio
import os
import re
from datetime import datetime as dt
import logging

pi = pigpio.pi()
settings_lock = threading.RLock()
scheduler_active = False
scheduler_thread = None
logger = logging.getLogger()

TIME_PATTERN = re.compile(r'^(?P<hour>\d\d):(?P<minute>\d\d)$')
SETTINGS_FILE = "settings/rgb.json"
DEFAULT_SETTINGS_FILE = "settings/default.json"

def load_settings():
    global settings_lock
    settings_lock.acquire()

    settings = None
    if not os.path.exists(SETTINGS_FILE):
        with open(DEFAULT_SETTINGS_FILE, "r") as defaults_file:
            save_settings(json.load(defaults_file));

    with open(SETTINGS_FILE, "r") as sfile:
        settings = json.load(sfile)

    settings_lock.release()

    return settings

def save_settings(settings):
    global settings_lock
    settings_lock.acquire()

    if not os.path.exists(SETTINGS_FILE):
        dirname = os.path.dirname(SETTINGS_FILE)
        if dirname:
            os.makedirs(dirname, mode=0o744, exist_ok=True)

    with open(SETTINGS_FILE, "w") as sfile:
        json.dump(settings, sfile, sort_keys=True, indent=4)

    settings_lock.release()

def to_seconds(hour, min, sec=0):
    return (hour * 60 + min) * 60 + sec

def to_offset(start, target):
    return (target if target >= start else (24 * 60 * 60 + target)) - start

def apply_color(settings):
    global settings_lock
    settings_lock.acquire()

    color = settings["color"] if settings["on"] else [0, 0, 0]
    brightness = settings["brightness"] / 100.0
    state = {"in_transition": False}

    if settings["schedule"]["enabled"]:
        match_on = TIME_PATTERN.match(settings["schedule"]["on"]["time"])
        match_off = TIME_PATTERN.match(settings["schedule"]["off"]["time"])

        if match_on and match_off:
            on_sec = to_seconds(int(match_on.group("hour")), int(match_on.group("minute")))
            off_sec = to_seconds(int(match_off.group("hour")), int(match_off.group("minute")))
            on_duration = to_offset(on_sec, off_sec)

            now = dt.now()
            now_sec = to_seconds(now.hour, now.minute, now.second)
            now_offset = to_offset(on_sec, now_sec)

            if now_offset <= on_duration:
                on_trans = settings["schedule"]["on"]["transition"] * 60
                off_trans = settings["schedule"]["off"]["transition"] * 60
                on_ratio = 1 - max(on_trans - now_offset, 0) / float(on_trans)
                off_ratio = 1 - max(off_trans - (on_duration - now_offset), 0) / float(off_trans)
                ratio = min(on_ratio, off_ratio)
                if ratio < 1.0:
                    state["in_transition"] = True
                brightness *= ratio

                logger.debug("[{3}:{4}] on_ratio = {0}, off_ratio = {1}, brightness={2}".format(on_ratio, off_ratio, brightness, now.hour, now.minute))
            else:
                brightness = 0.0

    for p, c in zip(settings["pins"], color):
        pi.set_PWM_dutycycle(p, 255 - round(c * brightness))

    settings_lock.release()
    return state

def trim_range(value, min, max):
    if value < min:
        return min
    if value > max:
        return max
    return value

def scheduler_thread():
    global scheduler_active

    while scheduler_active:
        settings = load_settings()
        state = apply_color(settings)
        time.sleep((65 - dt.now().second) if not state["in_transition"] else 5)

    # Turn off lights
    logger.info("Turning the lights off...")
    settings = load_settings()
    settings["brightness"] = 0
    apply_color(settings)

def start_scheduler():
    global scheduler_active, scheduler_thread

    scheduler_active = True
    scheduler_thread = threading.Thread(target=scheduler_thread)
    scheduler_thread.start()

def stop_scheduler():
    global scheduler_active, scheduler_thread

    scheduler_active = False
    scheduler_thread.join()
