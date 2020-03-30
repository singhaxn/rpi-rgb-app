class Effects {
  constructor(effectsJson) {
    this.effects = effectsJson;
    this.controlId = {
      "colors": {},
      "sequences": {}
    }
  }

  fromId(id) {
    return this.effects[id[0]][id[1]];
  }

  getEffectAttribute(effect, attribute, fail=null) {
    var id = this.getId(effect);
    var value = null;
    if (id)
      value = this.fromId(id);
    else if (attribute in effect && effect[attribute])
      value = effect[attribute];

    return value || fail;
  }

  getColor(effect, fail=null) {
    var id = this.getId(effect);
    var color = null;
    if (id)
      color = this.fromId(id);
    else if ("color" in effect && effect["color"])
      color = effect["color"];

    return color || fail;
  }

  getSequence(effect, fail=null) {
    var sequence = null;
    if(effect["effecttype"] == "sequence" && "effects" in effect)
      sequence = effect;
    else {
      var id = this.getId(effect);
      if (id)
        sequence = this.fromId(id);
      else if("sequence" in effect && effect["sequence"])
        sequence = effect["sequence"];
    }

    return sequence || fail;
  }

  getType(effect) {
    if ("effecttype" in effect)
      return effect["effecttype"];
    else {
      var id = this.getId(effect);
      if (id)
        return id[0] == "colors" ? "solid" : "sequence";
    }

    return null;
  }

  getId(effect) {
    if ("id" in effect)
      return effect["id"];
    else if ("color" in effect && typeof(effect["color"]) == "string")
      return ["colors", effect["color"]]
    else if ("sequence" in effect && typeof(effect["sequence"]) == "string")
      return ["sequences", effect["sequence"]]
    return null;
  }

  saveControlId(effect_id, control_id) {
    this.controlId[effect_id[0]][effect_id[1]] = control_id;
  }

  getControlId(effect_id) {
    return this.controlId[effect_id[0]][effect_id[1]];
  }

  findColorReferences(colorId) {
    var sequences = this.effects["sequences"];
    var references = [];

    for (var sid in sequences) {
      var seq = sequences[sid];
      for (var eid=0; eid<seq.effects.length; eid++) {
        var effectColorId = this.getId(seq.effects[eid]);
        console.debug(effectColorId, seq.effects[eid]);
        if (effectColorId && effectColorId[0] == "colors" && effectColorId[1] == colorId) {
          references.push(sid);
          break;
        }
      }
    }

    return references;
  }
}

function sanitizeId(id) {
  return id.replace(/ /g, "_");
}

function padLeft(value, len, pad) {
  var result = "" + value;
  var npad = len - result.length;
  if (npad > 0)
    result = ("" + pad).repeat(npad) + result;

  return result;
}

function clone(effect) {
  return JSON.parse(JSON.stringify(effect));
}

function parseColor(htmlColor) {
  var color = [0, 0, 0];
  for (var i = 0; i < 3; i++) {
    var start = 1 + i*2;
    if (start + 2 <= htmlColor.length)
      color[i] = parseInt(htmlColor.substring(start, start+2), 16);
  }

  return color;
}

function toHtmlColor(color) {
  var htmlColor = "#";
  for(var i = 0; i < color.length; i++)
    htmlColor += padLeft(color[i].toString(16), 2, 0);
  return htmlColor
}

function secondsToTime(sec) {
  var tsec = sec;
  var s = sec % 60;
  sec = Math.floor(sec / 60);
  var m = sec % 60;
  var h = Math.floor(sec / 60);
  var t = [h, m, s];

  while (t[0] == 0)
    t.shift();

  if (t.length > 0) {
    for (var i=0; i<t.length; i++)
      t[i] = padLeft(t[i], 2, 0);

    return t.join(":");
  }

  return 0;
}

const TIME_PATTERNS = [ /^(?:(?<hours>\d+):)?(?<minutes>\d\d?):(?<seconds>\d\d?)$/, /^(?<seconds>\d+)$/ ];

function parseTime(timeStr) {
  var match = null;
  for (var i=0; !match && i<TIME_PATTERNS.length; i++) {
    match = TIME_PATTERNS[i].exec(timeStr);
  }

  var time = null;
  if (match) {
    time = {};

    function toInt(m, key) {
      return (key in m && m[key]) ? parseInt(m[key]) : 0;
    }

    var keys = ["hours", "minutes", "seconds"];
    for (var k=0; k<keys.length; k++) {
      var key = keys[k];
      time[key] = toInt(match.groups, key);
    }

    console.log("parseTime(" + timeStr + ") =", time);

    if ((time["minutes"] > 0 || time["hours"] > 0) && (time["minutes"] > 59 || time["seconds"] > 59))
      time = null;
  }

  return time;
}

function createColorOption(name, color, effects, applyColor) {
  var template = $("#tmpColorOption")[0];
  var option = $(template.innerHTML);
  var radio = option.find('input[type="radio"]');
  var preview = option.find("span");
  var label = option.find("label");
  var radioId = "rdo_color_" + sanitizeId(name);

  effects.saveControlId(["colors", name], radioId);

  radio.attr("id", radioId);
  radio.val(name);
  radio.change(applyColor);
  preview.css("background-color", "rgb(" + color.join(",") + ")");
  label.attr("for", radioId);
  label.append(name);

  return option;
}

function createSequenceOption(name, seqEffect, effects, applySequence) {
  var template = $("#tmpSequenceOption")[0];
  var option = $(template.innerHTML);
  var radio = option.find("input");
  var preview = option.find(".seq-item-preview");
  var label = option.find("label");
  var labelText = option.find(".seq-item-name");
  var radioId = "rdo_seq_" + sanitizeId(name);
  var seq = seqEffect["effects"]
  var duration = buildSequencePreview(seq, effects, preview);

  effects.saveControlId(["sequences", name], radioId);

  radio.attr("id", radioId);
  radio.val(name);
  radio.change(applySequence);
  label.attr("for", radioId);
  labelText.append(name + " (" + secondsToTime(duration) + ")");

  return option;
}

function buildSequencePreview(seq, effects, preview) {
  var duration = 0;
  var n0 = 0;

  for(var ei = 0; ei < seq.length; ei++) {
    var d = seq[ei]["duration"];
    if (d == 0)
      n0++;
    duration += d;
  }

  var black = [0, 0, 0];
  preview.empty();
  for(var ei = 0; ei < seq.length; ei++) {
    var e = seq[ei];
    var span = $("<span/>");
    span.addClass("seq-subeffect");
    // span.css("width", Math.floor(e["duration"] / duration * (100 - n0)) + "%");
    span.css("width", (e["duration"] / duration * (100 - n0)) + "%");
    if("effecttype" in e) {
      if(e["effecttype"] == "solid") {
        var color = effects.getColor(e) || black;
        span.css("background-color", "rgb(" + color.join(",") + ")");
      } else if (e["effecttype"] == "transition") {
        var prev = ei > 0 ? effects.getColor(seq[ei-1], black) : black;
        var next = (ei < seq.length - 1) ? effects.getColor(seq[ei+1], black) : black;
        span.css("background-image", "linear-gradient(to right, rgb(" +
            prev.join(",") + "), rgb(" + next.join(",") + "))");
      } else
        span.css("background-color", "rgb(0, 0, 0)");
    }
    preview.append(span);
  }

  return duration;
}

function navigateTo(url) {
  return function(event) {
    window.location.href = url;
  }
}

function postJson(url, data) {
  console.log("Post:", url, data);

  return $.post({
    url: url,
    data: JSON.stringify(data),
    dataType: "json",
    contentType: 'application/json'
  });
}
