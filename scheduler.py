from threading import Thread
import time
from datetime import datetime as dt
import effects
# from effects import ConfigEffectTransformer

TIME_PATTERN = re.compile(r'^(?P<hour>\d\d):(?P<minute>\d\d)$')

def toSeconds(hour, min, sec=0):
    return (hour * 60 + min) * 60 + sec

def parseTime(tstr):
    m = TIME_PATTERN.match(tstr)
    return toSeconds(int(m.group("hour")), int(m.group("minute")))

class Scheduler:
    def __init__(self, config, transformer, hardware):
        super().__init__()
        self.config = config
        self.transformer = transformer
        self.hardware = hardware
        self.active = False

    def start(self):
        def runThread(self):
            self.active = True

            while self.active:
                self.config.freeze()

                settings = self.config.get()
                schedule = settings["schedule"]

                onSec = parseTime(schedule["on"])
                offSec = parseTime(schedule["off"])
                if offSec < onSec:
                    offSec += toSeconds(24, 0, 0)
                now = dt.now()
                nowSec = toSeconds(now.hour, now.minute, now.second)
                if nowSec < onSec:
                    nowSec += toSeconds(24, 0, 0)

                rapidMode = False
                if nowSec >= onSec and nowSec < offSec:
                    effect = self.transformer.transform(settings["effect"])
                    color, rapid = effect.evaluate(nowSec - onSec)
                    rapidMode = rapid
                    self.hardware.setColor(color, settings["brightness"])
                else:
                    self.hardware.setColor(effects.BLACK_COLOR, 0)

                self.config.unfreeze()

                time.sleep(1 if rapidMode else (65 - dt.now().second))

        Thread(target=runThread, args=(self,)).start()

    def stop(self):
        self.active = False
