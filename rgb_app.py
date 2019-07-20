from flask import Flask, render_template, request
import json
from rgb_util import *

app = Flask(__name__)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/')
def index():
    settings = load_settings()
    # if not "schedule" in settings:
    #     settings["schedule"] = DEFAULT_SETTINGS["schedule"]
    return render_template("index.html.j2", settings=settings)

@app.route('/apply', methods=["POST"])
def apply_rgb():
    data = request.get_json()
    app.logger.debug(data)
    settings = load_settings()
    settings["color"] = [trim_range(c, 0, 255) for c in data["color"]]
    apply_color(settings)
    save_settings(settings)

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/brightness', methods=["POST"])
def apply_brightness():
    data = request.get_json()
    app.logger.debug(data)
    settings = load_settings()
    settings["brightness"] = trim_range(data["brightness"], 0, 100)
    apply_color(settings)
    save_settings(settings)

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/power', methods=["POST"])
def power_rgb():
    data = request.get_json()
    app.logger.debug(data)
    settings = load_settings()
    if settings["on"] != data["on"]:
        settings["on"] = data["on"]
        apply_color(settings)
        save_settings(settings)

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/preset', methods=["GET", "POST", "DELETE"])
def preset():
    status = None
    settings = load_settings()

    if request.method == 'GET':
        status = {
            "success": True,
            "presets": settings["presets"] if "presets" in settings else {}
        }
    else:
        data = request.get_json()
        app.logger.debug(data)

        if request.method == 'POST':
            if not "presets" in settings:
                settings["presets"] = {}
            settings["presets"][data["preset"]] = [
                trim_range(c, 0, 255) for c in data["color"]
            ]
            save_settings(settings)
            status = {'success': True}
        elif request.method == "DELETE":
            if data["preset"] in settings["presets"]:
                del settings["presets"][data["preset"]]
                save_settings(settings)

    return json.dumps(status), 200, {'ContentType':'application/json'}

@app.route('/schedule', methods=["POST"])
def apply_schedule():
    data = request.get_json()
    app.logger.debug(data)
    settings = load_settings()
    props = ["enabled", "on", "off"]
    for p in props:
        if p in data:
            settings["schedule"][p] = data[p]
    apply_color(settings)
    save_settings(settings)

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

if __name__ == "__main__":
    try:
        start_scheduler()
        app.logger.info("Scheduler started.")
        settings = load_settings()
        app.run(host=settings["bind-addr"], port=settings["bind-port"])
    finally:
        app.logger.info("Waiting for scheduler to quit...")
        stop_scheduler()
