# RGB Strip controller for Raspberry Pi

This app allows you to control an RGB strip, connected to your Raspberry Pi through GPIO, through a web browser. On Chrome for Android, specifically, you can create a shortcut to the controller page on your home screen, and use it like any other RGB controller app.

## How does it work?

This is a `Flask` application that uses the `pigpio` library to set the GPIO signals that control the LED strip. An RGB amplifier is used to convert the 3.3V GPIO signals to 12V as required by a 5050 RGB strip.

Although this app has only been tested with a 12V strip, with an appropriate amplifier, this may even work with 5V strips.

## Setting it up

Here, we assume that you already have Raspbian installed on a Raspberry Pi and you have a working network connection, ideally with a static IP address, on the Pi. If you intend to run only this app on your Raspberry Pi, the Lite image on a Raspberry Pi Zero, should suffice.

The following instructions assume that the red, green and blue channels are being controlled by GPIO23, GPIO24 and GPIO25, respectively. Please make adjustments as appropriate for your environment.

![alt text](./connections.png "Connections")

Install prerequisites
```
sudo apt-get install pigpiod python3 python3-pigpio python3-flask git
```
Start the pigpiod daemon
```
sudo service pigpiod start
```
Make sure pigpio works (use the correct GPIO ids)
```
pigs pwm 23 0 pwm 24 0 pwm 25 0
```
You should now see your led strip light up white. If the above command does nothing, or tells you that the pigpiod daemon is not running, please see the Troubleshooting section below.

Turn the LEDs off with:
```
pigs pwm 23 255 pwm 24 255 pwm 25 255
```
Enable the pigpiod daemon to get it to start automatically on boot.
```
sudo update-rc.d pigpiod enable
```
Clone this repository
```
git clone --recurse-submodules <TODO>
```
Determine the LAN IP address of your Raspberry Pi:
```
ifconfig
```
See the App Configuration section below and make any changes that may be required for your environment.

Edit `rgb-app.service` and specify the correct absolute path to your repository, under `WorkingDirectory` and `ExecStart`.

Copy the service file to `/etc/systemd/system`
```
sudo cp rgb-app.service /etc/systemd/system/
```
Start the service
```
sudo service rgb-app start
```

In a web browser, on any device on your local network (same network as the Pi), open the page `http://<Pi_IP_Address>:5000/`. Replace `<Pi_IP_Address>` with the actual IP address of your Pi.

![alt text](rgb-app-ui.png "UI")

To get the RGB app to start up automatically at boot, add the following line to your `/etc/rc.local`, before the `exit 0` line.
```
service rgb-app start
```

## App Configuration

The default app configuration is stored in `settings/default.json`. The first time you run the app, these settings are copied over to the live configuration file, `settings/rgb.json`. If you ever want to revert back to the default settings, simply delete `settings/rgb.json`. This section describes modifications to `settings/rgb.json`. However, the same description applies to `settings/default.json` _when `settings/rgb.json` does not exist_.

If you do need to edit the live configuration file, remember to stop the `rgb-app` service first:
```
sudo service rgb-app stop
```
and start it up again afterwards
```
sudo service rgb-app start
```

### Common Modifications
1. Specify the correct IP address of your Pi under `bind-address`. Ideally, this should be a static IP address.
2. If you're using different pins than the default GPIO23, GPIO24 and GPIO25 for the red, green and blue channels, respectively, specify the correct GPIO IDs under `pins`. The sequence is `[R, G, B]`. Please note that these are GPIO ids and not physical pin numbers.

## Troubleshooting
1. ### `pigs` does not work
In my case, I discovered that the pigpiod server was listening on the default ipv6 address instead of ipv4. I got it to work by modifying `ExecStart` line the pigpiod service definition in `/lib/systemd/system/pigpiod.service` to
```
ExecStart=/usr/bin/pigpiod -l -n 127.0.0.1
```
Restart the pigpiod service and try to turn the strip on again.

2. ### `http://<Pi_IP_Address>:5000/` returns an ERR_CONNECTION_REFUSED error
Make sure you have specified the correct bind address as described in the App Configuration section above.

3. ### `pigs` works but you can't control your LED strip from the web interface
Make sure you have specified the correct GPIO pin numbers as described in the App Configuration section above.
