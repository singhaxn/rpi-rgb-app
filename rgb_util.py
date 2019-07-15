import json
import threading
import time
import pigpio
import os
import re
from datetime import datetime as dt

pi = pigpio.pi()
settings_lock = threading.RLock()
scheduler_active = False
scheduler_thread = None

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

def apply_color(settings):
    global settings_lock
    settings_lock.acquire()

    color = settings["color"] if settings["on"] else [0, 0, 0]
    brightness = settings["brightness"] / 100.0

    if settings["schedule"]["enabled"]:
        match_on = TIME_PATTERN.match(settings["schedule"]["on"]["time"])
        match_off = TIME_PATTERN.match(settings["schedule"]["off"]["time"])

        if match_on and match_off:
            on_min = int(match_on.group("hour")) * 60 + int(match_on.group("minute"))
            off_min = int(match_off.group("hour")) * 60 + int(match_off.group("minute"))
            on_duration = (off_min if off_min >= on_min else (24 * 60 + off_min)) - on_min

            now = dt.now()
            now_min = now.hour * 60 + now.minute
            now_offset = (now_min if now_min >= on_min else (24 * 60 + now_min)) - on_min

            if now_offset <= on_duration:
                on_trans = settings["schedule"]["on"]["transition"]
                off_trans = settings["schedule"]["off"]["transition"]
                on_ratio = 1 - max(on_trans - now_offset, 0) / float(on_trans)
                off_ratio = 1 - max(off_trans - (on_duration - now_offset), 0) / float(off_trans)
                brightness *= min(on_ratio, off_ratio)

                print("[{3}:{4}] on_ratio = {0}, off_ratio = {1}, brightness={2}".format(on_ratio, off_ratio, brightness, now.hour, now.minute))
            else:
                brightness = 0.0

    for p, c in zip(settings["pins"], color):
        pi.set_PWM_dutycycle(p, 255 - round(c * brightness))

    settings_lock.release()

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
        apply_color(settings)
        time.sleep(60)

    # Turn off lights
    print("Turning the lights off...")
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
