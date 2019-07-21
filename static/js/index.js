var CHANNELS = [
  {"range": "#rngR", "text": "#txtR"},
  {"range": "#rngG", "text": "#txtG"},
  {"range": "#rngB", "text": "#txtB"}
];
var PRESET_NAME_PATTERN = /^[a-zA-Z][a-zA-Z0-9_-]*$/;
var TIME_PATTERN = /^(\d\d):(\d\d)$/;
var MINUTES_PATTERN = /^\d+$/;

var presets = {};

$(document).ready(
  function() {
    //  Power button
    initializeToggleButton($("#btnPower"), "#settings-container", "on", "/power");

    //  Schedule button
    initializeToggleButton($("#btnSchedule"), ".schedule", "enabled", "/schedule");

    //  Colors
    $("input[type='range'].channel").each(
      function(index, element) {
        updateChannel($(element));
      }
    );
    $("input[type='range'].channel").change(
      function(event) {
        updateChannel($(event.target));
      }
    );
    $("#btnApply").click(apply);

    //  Brightness
    $("#rngBrightness").change(
      function(event) {
        updateBrightness($(event.target));
      }
    )

    //  Presets
    $("#selPresets").change(presetSelected);
    $("#btnSave").click(savePreset);
    $("#btnDelete").click(deletePreset);

    $.get({
      url: "/preset",
      dataType: "json",
      success: function (data) {
        var selPresets = $("#selPresets");
        presets = data["presets"];
        for(p in presets) {
          selPresets.append(createPresetOption(p, presets[p]));
        }
      }
    });

    //  Save Schedule
    $("#btnSaveSchedule").click(saveSchedule);
  }
)

function postJson(url, data) {
  console.log("Post:", url, data);

  $.post({
    url: url,
    data: JSON.stringify(data),
    dataType: "json",
    contentType: 'application/json'
  });
}

function createPresetOption(name, color) {
  var option = $(new Option(name, name));
  option.css("background-color", "rgb(" + color.join(",") + ")");
  option.addClass("preset");
  return option;
}

function getColor() {
  var color = [0, 0, 0];
  $("input[type='range'].channel").each(
    function(index, element) {
      var jelement = $(element);
      color[parseInt(jelement.data("index"))] = parseInt(jelement.val());
    }
  );

  return color;
}

function updateChannel(target) {
  var index = parseInt(target.data("index"));
  var channel = CHANNELS[index];
  var value = target.val();
  var color = getColor();

  $(channel["text"]).val(value);
  $(".preview").css("background-color", "rgb(" + color.join(",") + ")");
}

function updateBrightness(target) {
  var value = parseInt(target.val());

  $("#txtBrightness").val(value);
  postJson("/brightness", {brightness: value});
}

function apply(event) {
  var color = getColor();

  var data = {
    color: color
  };
  postJson("/apply", data);
}

function initializeToggleButton(btn, selector, key, url) {
  var enabled = (btn.data("checked").toLowerCase() == "true");

  if(enabled) {
    btn.addClass("toggle-on");
    $(selector).css('display', "block");
  } else {
    btn.addClass("toggle-off");
    $(selector).css('display', "none");
  }
  btn.data("checked", enabled);
  btn.click(
    function(event) {
      toggle($(this), selector, key, url);
    }
  );
}

function toggle(btn, selector, key, url) {
  var enabled = btn.data("checked");
  var data = {};
  data[key] = !enabled;

  if(enabled) {
    btn.removeClass("toggle-on").addClass("toggle-off");
    $(selector).css("display", "none");
  } else {
    btn.removeClass("toggle-off").addClass("toggle-on");
    $(selector).css("display", "block");
  }

  btn.data("checked", !enabled);
  postJson(url, data);
}

function presetSelected(event) {
  var value = $(this).val();
  var preset = presets[value];
  console.log(value, preset);

  $("input[type='range'].channel").each(
    function(index, element) {
      var jelement = $(element);
      jelement.val(preset[parseInt(jelement.data("index"))]).change();
    }
  );

  $("#txtPreset").val(value);
  apply();
}

function savePreset(event) {
  var name = $("#txtPreset").val();

  if(!name.match(PRESET_NAME_PATTERN))
    alert("Error: Profile name must match the pattern " + PRESET_NAME_PATTERN);
  else {
    var color = getColor();
    var data = {
      "preset": name,
      "color": color
    };
    var selPresets = $("#selPresets");

    if (name in presets) {
      presets[name] = color;
      var option = selPresets.children('[value="' + name + '"]');
      option.css("background-color", "rgb(" + color.join(",") + ")");
    } else {
      presets[name] = color;
      selPresets.append(createPresetOption(name, color));
    }

    postJson("/preset", data);
  }
}

function deletePreset(event) {
  var name = $("#txtPreset").val();

  if(name in presets) {
    delete presets[name];
    var data = {
      "preset": name
    };

    $("#selPresets").children('[value="' + name + '"]').remove();

    console.log(data);

    $.ajax({
      url: "/preset",
      method: "DELETE",
      data: JSON.stringify(data),
      dataType: "json",
      contentType: 'application/json'
    });
  } else
    alert("Error: Unknown preset '" + name + "'");
}

function isValidTime(t) {
  var match = TIME_PATTERN.exec(t);
  if(match) {
    var h = parseInt(match[1]);
    var m = parseInt(match[2]);

    return isValidNumber(match[1], 0, 23) && isValidNumber(match[2], 0, 59);
  }

  return false;
}

function isValidNumber(t, min, max) {
  var match = MINUTES_PATTERN.exec(t);

  if(match) {
    var m = parseInt(t);

    return (!min || m >= min) && (!max || m <= max);
  }

  return false;
}

function allValid(validation) {
  for(var i=0; i<validation.length; i++) {
    if(!validation[i][0]) {
      alert("Invalid " + validation[i][1] + "!");
      return false;
    }
  }

  return true;
}

function saveSchedule(event) {
  var onTime = $("#txtOnTime").val();
  var onTransition = $("#txtOnTransition").val();
  var offTime = $("#txtOffTime").val();
  var offTransition = $("#txtOffTransition").val();
  var validation = [
      [isValidTime(onTime), "on time"],
      [isValidTime(offTime), "off time"],
      [isValidNumber(onTransition, 0, 480), "on transition"],
      [isValidNumber(offTransition, 0, 480), "off transition"],
    ];

  if(!allValid(validation))
    return;

  var data = {
    "on": {
      "time": onTime,
      "transition": parseInt(onTransition)
    },
    "off": {
      "time": offTime,
      "transition": parseInt(offTransition)
    }
  };

  postJson("/schedule", data);
}
