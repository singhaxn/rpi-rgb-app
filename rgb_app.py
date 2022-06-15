import os
import sys
import json
import signal

# To enable debug logging: export FLASK_ENV=development
# os.environ["FLASK_ENV"] = "development"

import logging
loglevel = logging.DEBUG if os.getenv("FLASK_ENV", "production") == "development" else logging.INFO
logging.basicConfig(stream=sys.stdout, level=loglevel)

from flask import Flask, render_template, request
app = Flask(__name__)
app.app_context().push()

from config import Config
from renderer import Renderer

config = Config("config/settings.json")
renderer = Renderer(config)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/')
def index():
    return render_template("index.html.j2", settings=config.get())

@app.route('/coloreditor')
def color_editor():
    return render_template("edit_color.html.j2", settings=config.get())

@app.route('/sequenceeditor')
def sequence_editor():
    return render_template("edit_sequence.html.j2", settings=config.get())

@app.route('/power', methods=["POST"])
def set_power():
    data = request.get_json()
    settings = config.get()
    app.logger.debug(f"set_power: {data}, {settings['on']}")
    if settings["on"] != data["on"]:
        config.setOn(data["on"])
        renderer.applySettings()

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/mode', methods=["POST"])
def set_mode():
    data = request.get_json()
    app.logger.debug(data)
    settings = config.get()
    if settings["mode"] != data["mode"]:
        config.setMode(data["mode"])
        renderer.applySettings()

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/schedule', methods=["POST"])
def set_schedule():
    data = request.get_json()
    app.logger.debug(data)
    config.setSchedule(data["schedule"])
    renderer.applySettings()

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/brightness', methods=["POST"])
def apply_brightness():
    data = request.get_json()
    app.logger.debug(data)
    config.setBrightness(data["brightness"])
    renderer.applySettings(resetEffect=False)

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/effects', methods=["GET"])
def effects():
    settings = config.get()
    effects = { key: (settings[key] if key in settings else []) for key in ["colors", "sequences", "effect"] }
    status = {
        "success": True,
        "effects": effects
    }

    return json.dumps(status), 200, {'ContentType':'application/json'}

@app.route('/colors', methods=["POST", "DELETE"])
def edit_colors():
    data = request.get_json()
    app.logger.debug(data)
    if request.method == 'POST':
        for key, value in data["colors"].items():
            config.setColor(key, value);
    else:
        for key in data["colors"]:
            config.deleteColor(key);

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/sequences', methods=["POST", "DELETE"])
def edit_sequences():
    data = request.get_json()
    app.logger.debug(data)
    if request.method == 'POST':
        for key, value in data["sequences"].items():
            config.setSequence(key, value);
    else:
        for key in data["sequences"]:
            config.deleteSequence(key);

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/apply', methods=["POST"])
def apply_effect():
    data = request.get_json()
    settings = config.get()
    app.logger.debug(data)
    config.setEffect(data["effect"])
    renderer.applySettings()

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

if __name__ == "__main__":
    def sigtermReceived(signum, frame):
        app.logger.info("Received SIGTERM")
        sys.exit(0)

    try:
        renderer.start()
        signal.signal(signal.SIGTERM, sigtermReceived)
        app.logger.info("Renderer started")
        settings = config.get()
        app.run(host=settings["bind-addr"], port=settings["bind-port"], use_reloader=False)
        app.logger.info("App stopped")
    finally:
        app.logger.info("Waiting for renderer to quit...")
        renderer.stop()
