# import os

# os.environ["GPIOZERO_PIN_FACTORY"] = "pigpio"

import gpiozero
import logging

def logger():
    return logging.getLogger(__name__)

class Hardware:
    def __init__(self, pins):
        self.pins = pins
        self.last = [0, 0, 0]
        logger().info(f"Acquiring GPIO...")
        self.pwmleds = [gpiozero.PWMLED(p, active_high=False, frequency=160) for p in pins]

    def setColor(self, color, brightness):
        if color is None:
            color = [0, 0, 0]
        brightness /= 100.

        for p, c, l in zip(self.pwmleds, color, self.last):
            if l != c:
                logger().debug(f"{p}: {c}")
                p.value = (c * brightness) / 255.
        
        self.last = color