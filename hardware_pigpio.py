import pigpio

class Hardware:
    def __init__(self, pins):
        self.pins = pins
        self.pi = pigpio.pi()
        for p in self.pins:
            self.pi.set_PWM_range(p, 255)
            self.pi.set_PWM_dutycycle(p, 255)
    
    def __del__(self):
        self.pi.stop()

    def setColor(self, color, brightness):
        if color is None:
            color = [0, 0, 0]
        brightness /= 100.

        for p, c in zip(self.pins, color):
            pwm = 255 - round(c * brightness)
            if self.pi.get_PWM_dutycycle(p) != pwm:
                self.pi.set_PWM_dutycycle(p, pwm)
