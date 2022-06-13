import lgpio

class Hardware:
    def __init__(self, pins):
        self.pins = pins
        # open the gpio chip and set the LED pin as output
        self.handle = lgpio.gpiochip_open(0)
        self.last = [0, 0, 0]
        print(f"{__name__}: Got handle {self.handle}")
        ret = lgpio.group_claim_output(self.handle, self.pins, lFlags=lgpio.SET_ACTIVE_LOW)
    
    def __del__(self):
        if self.handle > 0:
            lgpio.gpiochip_close(self.handle)
            print(f"{__name__}: Closed handle {self.handle}.")
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
                lgpio.tx_pwm(self.handle, p, 100, pwm)
        
        self.last = color