import json
import os
import threading
from datetime import datetime as dt
import copy
import logging

def logger():
    return logging.getLogger(__name__)

class Config:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.settings = None
        self.loadTime = None

    def get(self):
        if not os.path.exists(self.path):
            self.save(Config._getDefaultSettings())
        elif self.loadTime is None or self.loadTime < os.path.getmtime(self.path):
            self.lock.acquire()

            with open(self.path, "r") as sfile:
                self.settings = json.load(sfile)

            self.loadTime = os.path.getmtime(self.path)

            self.lock.release()

        return self.settings

    def save(self, settings):
        self.lock.acquire()

        if not os.path.exists(self.path):
            dirname = os.path.dirname(self.path)
            if dirname:
                os.makedirs(dirname, mode=0o744, exist_ok=True)

        self.settings = settings
        with open(self.path, "w") as sfile:
            json.dump(self.settings, sfile, sort_keys=True, indent=4)

        self.loadTime = os.path.getmtime(self.path)

        self.lock.release()

    def updateSetting(self, updateFunc, *args):
        self.lock.acquire()
        settings = copy.deepcopy(self.settings)
        updateFunc(settings, *args)
        self.save(settings)
        self.lock.release()

    def setOn(self, value):
        logger().debug(f"Config.setOn: {value}")
        def update(settings, value):
            settings["on"] = value
        self.updateSetting(update, value)

    def setMode(self, value):
        def update(settings, value):
            settings["mode"] = value
        self.updateSetting(update, value)

    def setEffect(self, value):
        def update(settings, value):
            settings["effect"] = value
        self.updateSetting(update, value)

    def setBrightness(self, value):
        def update(settings, value):
            settings["brightness"] = value
        self.updateSetting(update, value)

    def setSchedule(self, value):
        def update(settings, value):
            settings["schedule"] = value
        self.updateSetting(update, value)

    def setColor(self, key, value):
        def update(settings, key, value):
            settings["colors"][key] = value
        self.updateSetting(update, key, value)

    def deleteColor(self, key):
        def update(settings, key):
            if key in settings["colors"]:
                del settings["colors"][key]
        self.updateSetting(update, key)

    def setSequence(self, key, value):
        def update(settings, key, value):
            settings["sequences"][key] = value
        self.updateSetting(update, key, value)

    def deleteSequence(self, key):
        def update(settings, key):
            if key in settings["sequences"]:
                del settings["sequences"][key]
        self.updateSetting(update, key)

    @staticmethod
    def _getDefaultSettings():
        return {
            "on": False,
            "mode": "manual",   # "manual" or "schedule"
            "effect": { "effecttype": "solid", "duration": None, "color": "white" },
            # unnamed color effect
            # "effect": { "effecttype": "solid", "duration": None, "color": [255, 255, 255] },
            # loop effect
            # "effect": { "effecttype": "loop", "duration": None, "sequence": "rainbow" },
            # sequence effect by id
            # "effect": { "id": ["sequences", "rainbow"] },
            # color effect by id
            # "effect": { "id": ["colors", "white"] },

            "brightness": 100,  # 0 - 100

            "colors": { # "name": [r, g, b]
              "red": [255, 0, 0],
              "green": [0, 255, 0],
              "blue": [0, 0, 255],
              "white": [255, 255, 255]
            },

            "sequences": {
                "rainbow": {
                    "effecttype": "sequence",
                    "duration": None,
                    "effects": [
                        { "effecttype": "solid", "duration": 0, "color": "blue" },
                        { "effecttype": "transition", "duration": 10 },
                        { "effecttype": "solid", "duration": 0, "color": "green" },
                        { "effecttype": "transition", "duration": 10 },
                        { "effecttype": "solid", "duration": 0, "color": "red" },
                        { "effecttype": "transition", "duration": 10 },
                        { "effecttype": "solid", "duration": 0, "color": "blue" }
                    ]
                }
            },

            "schedule": {
                "on": "00:00",
                "off": "00:00"
            },

            "pins": [23, 24, 25],
            # "bind-addr": "127.0.0.1",
            "bind-addr": "0.0.0.0",
            "bind-port": 5000
        }
