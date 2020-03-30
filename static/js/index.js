const TIME_PATTERN = /^(\d\d):(\d\d)$/;
const MINUTES_PATTERN = /^\d+$/;
var effects = null;

$(document).ready(
  function() {
    var animation = {
      duration: 0,
      easing: "swing"
    };
    //  Power button
    initializeToggleButton($("#btnPower"), ["#settings-container", "#btnSchedule"], "on", "/power", {false: false, true: true}, animation);

    //  Schedule button
    initializeToggleButton($("#btnSchedule"), [".schedule"], "mode", "/mode", {false: "manual", true: "schedule"}, animation);

    //  Brightness
    $("#rngBrightness").change(updateBrightness);

    //  Save Schedule
    $("#btnSaveSchedule").click(saveSchedule);

    //  Color
    $("#rdoColor").change(
      function(event) {
        $(".color").slideDown(animation);
        $(".sequence").slideUp(animation);
        applyEffect($(event.target).data("active"), $(event.target));
      }
    );

    $("#btnColorEdit").click(navigateTo("/coloreditor"));
    $("#btnSequenceEdit").click(navigateTo("/sequenceeditor"));

    //  Sequence
    $("#rdoSequence").change(
      function(event) {
        $(".color").slideUp(animation);
        $(".sequence").slideDown(animation);
        var effect = $(event.target).data("active");
        applyEffect(effect, $(event.target));

        if (effect && effects.getType(effect) == "loop")
          $("#chkLoop").prop("checked", true);
      }
    );

    $("#chkLoop").change(
      function(event) {
        var rdoSequence = $("#rdoSequence");
        var sequence = $('input[name="grpSequence"]:checked');
        var effect = null;

        if (sequence.length > 0) {
          if ($(event.target).prop("checked"))
            effect = { "effecttype": "loop", "sequence": sequence[0].value };
          else
            effect = { "id": ["sequences", sequence[0].value] };

          applyEffect(effect, rdoSequence);
        }
      }
    );

    $.get({
      url: "/effects",
      dataType: "json",
      success: function (data) {
        console.log(data);
        var presets = data["effects"];
        effects = new Effects(presets);

        var colors = presets["colors"];
        var sequences = presets["sequences"];
        var effect = presets["effect"];
        var rdoColor = $("#rdoColor");
        var rdoSequence = $("#rdoSequence");
        var colorsContainer = $("#divColorSelect");
        var sequencesContainer = $("#divSequenceSelect");

        for(var ckey in colors) {
          var option = createColorOption(ckey, colors[ckey], effects, applyColor);
          colorsContainer.append(option);
        }

        for(var skey in sequences) {
          var option = createSequenceOption(skey, sequences[skey], effects, applySequence);
          sequencesContainer.append(option);
        }

        var effectType = effects.getType(effect);
        var typeRadio = (effectType == "solid") ? rdoColor : rdoSequence;
        typeRadio.prop("checked", true).change();

        var effectId = effects.getId(effect);
        if (effectId) {
          var listname = typeRadio.data("listname");
          var effectRadios = $('input[name="' + listname + '"]');

          for(var ei = 0; ei < effectRadios.length; ei++) {
            if (effectRadios[ei].value == effectId[1]) {
              $(effectRadios[ei]).prop("checked", true);
              break;
            }
          }
        }

        $("#chkLoop").prop("checked", effectType == "loop");

        applyEffect(effect, typeRadio, false);

        animation.duration = 500;
      }
    });
  }
)

function initializeToggleButton(btn, selector, key, url, values, animation) {
  var enabled = (btn.data("checked").toLowerCase() == "true");

  if(enabled) {
    btn.addClass("toggle-on");
    for (var i=0; i<selector.length; i++)
      $(selector[i]).slideDown(animation);
  } else {
    btn.addClass("toggle-off");
    for (var i=0; i<selector.length; i++)
      $(selector[i]).slideUp(animation);
  }
  btn.data("checked", enabled);
  btn.click(
    function(event) {
      toggle($(this), selector, key, url, values, animation);
    }
  );
}

function toggle(btn, selector, key, url, values, animation) {
  var enabled = btn.data("checked");
  var data = {};
  data[key] = values[!enabled];

  if(enabled) {
    btn.removeClass("toggle-on").addClass("toggle-off");
    for (var i=0; i<selector.length; i++)
      $(selector[i]).slideUp(animation);
  } else {
    btn.removeClass("toggle-off").addClass("toggle-on");
    for (var i=0; i<selector.length; i++)
      $(selector[i]).slideDown(animation);
  }

  btn.data("checked", !enabled);
  postJson(url, data);
}

function updateBrightness(event) {
  var target = $(event.target);
  var value = parseInt(target.val());

  $("#txtBrightness").val(value);
  postJson("/brightness", {brightness: value});
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
  var offTime = $("#txtOffTime").val();
  var validation = [
      [isValidTime(onTime), "on time"],
      [isValidTime(offTime), "off time"],
    ];

  if(!allValid(validation))
    return;

  var data = {
    "schedule": {
      "on": onTime,
      "off": offTime,
    }
  };

  postJson("/schedule", data);
}

function applyColor(event) {
  var radio = $(event.target);
  var effect = { "id": ["colors", radio.val()] };
  applyEffect(effect, $("#rdoColor"));
}

function applySequence(event) {
  var radio = $(event.target);
  var loop = $("#chkLoop").prop("checked");
  var effect;

  if (loop === true) {
    effect = { "effecttype": "loop", "sequence": radio.val() };
  } else {
    effect = { "id": ["sequences", radio.val()] };
  }

  applyEffect(effect, $("#rdoSequence"));
}

function applyEffect(effect, control, post=true) {
  if (effect) {
    control.data("active", effect);
    if (post)
      postJson("/apply", {"effect": effect});
  }
}
