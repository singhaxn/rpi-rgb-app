from threading import Thread, Condition
import re
from datetime import datetime as dt
from effects import ConfigEffectTransformer
import hardware

TIME_PATTERN = re.compile(r'^(?P<hour>\d\d):(?P<minute>\d\d)$')

def toSeconds(hour, min, sec=0, usec=0):
    return (hour * 60 + min) * 60 + sec + usec * 1e-6

def parseTime(tstr):
    m = TIME_PATTERN.match(tstr)
    return toSeconds(int(m.group("hour")), int(m.group("minute")))

class Renderer(Thread):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.transformer = ConfigEffectTransformer(config)
        settings = self.config.get()
        self.hardware = hardware.Hardware(settings["pins"])
        self.startTimeSec = None
        self.active = False
        self.lastEffectJson = None
        self.lastEffect = None
        self.lock = Condition()

    def run(self):
        self.lock.acquire()

        self.active = True
        while self.active:
            rapid = self._apply()

            self.lock.wait(0.1 if rapid else (65 - dt.now().second))

        self.lock.release()

    def stop(self):
        self.lock.acquire()

        self.active = False
        self.hardware.setColor(None, 0)

        self.lock.notify_all()
        self.lock.release()

        self.join()

    def transformEffect(self, effectJson):
        if self.lastEffectJson != effectJson:
            self.lastEffectJson = effectJson
            self.lastEffect = self.transformer.transform(effectJson)
        return self.lastEffect

    def applySettings(self, resetEffect=True):
        self.lock.acquire()

        if resetEffect:
            self.startTimeSec = None

        self.lock.notify_all()
        self.lock.release()

    def _apply(self):
        settings = self.config.get()
        color, rapid = None, False

        if settings["on"]:
            if settings["mode"] == "manual":
                now = dt.now()
                nowSec = toSeconds(now.hour, now.minute, now.second, now.microsecond)

                if self.startTimeSec is None:
                    self.startTimeSec = nowSec

                if nowSec < self.startTimeSec:
                    nowSec += toSeconds(24, 0, 0)

                effect = self.transformEffect(settings["effect"])
                color, rapid = effect.evaluate(nowSec - self.startTimeSec)
            else:
                self.startTimeSec = None
                schedule = settings["schedule"]

                onSec = parseTime(schedule["on"])
                offSec = parseTime(schedule["off"])
                if offSec < onSec:
                    offSec += toSeconds(24, 0, 0)

                now = dt.now()
                nowSec = toSeconds(now.hour, now.minute, now.second, now.microsecond)
                if nowSec < onSec:
                    nowSec += toSeconds(24, 0, 0)

                if nowSec >= onSec and nowSec < offSec:
                    effect = self.transformEffect(settings["effect"])
                    # Stretch an EffectSequence to match the schedule
                    effect.duration = offSec - onSec
                    color, rapid = effect.evaluate(nowSec - onSec)

            if color is not None:
                self.hardware.setColor(color, settings["brightness"])
            else:
                self.hardware.setColor(None, 0)
        else:
            self.hardware.setColor(None, 0)

        return rapid
