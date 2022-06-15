import lgpio
import logging

def logger():
    return logging.getLogger(__name__)

class Hardware:
    def __init__(self, pins):
        self.pins = pins
        logger().info(f"Acquiring GPIO...")
        # open the gpio chip and set the LED pin as output
        self.handle = lgpio.gpiochip_open(0)
        logger().debug(f"Got handle {self.handle}")
        self.last = [0, 0, 0]
        ret = lgpio.group_claim_output(self.handle, self.pins, lFlags=lgpio.SET_ACTIVE_LOW)
    
    def __del__(self):
        if self.handle > 0:
            logger().info(f"Releasing GPIO...")
            lgpio.gpiochip_close(self.handle)
            logger().debug(f"Closed handle {self.handle}.")
            self.handle = 0

    def setColor(self, color, brightness):
        if color is None:
            color = [0, 0, 0]
        brightness /= 100.

        for p, c, l in zip(self.pins, color, self.last):
            if l != c:
                # Correct when the SET_ACTIVE_LOW is not specified
                # pwm = int((255 - round(c * brightness)) / 255 * 100)
                pwm = int(round(c * brightness) / 255 * 100)
                logger().debug(f"{p}: {c}")
                lgpio.tx_pwm(self.handle, p, 100, pwm)
        
        self.last = color