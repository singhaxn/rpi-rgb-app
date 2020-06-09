var effects = null;

$(document).ready(
  function() {
    $("#cpkColor").change(anonymousColorSelected);
    $("#btnBack").click(function(event) {
      history.back();
    });
    $("#btnSave").click(saveColor);
    $("#btnDelete").click(deleteColor);

    reloadColors();
  }
)

function reloadColors() {
  var colorsContainer = $("#divColorSelect");
  colorsContainer.empty();
  $("#txtColor").val("");

  $.get({
    url: "/effects",
    dataType: "json",
    success: function (data) {
      console.log(data);
      var presets = data["effects"];
      effects = new Effects(presets);
      var effect = presets["effect"];
      var colors = presets["colors"];

      for (var ckey in colors) {
        var option = createColorOption(ckey, colors[ckey], effects, namedColorSelected);
        colorsContainer.append(option);
      }

      var effectType = effects.getType(effect);
      if (effectType == "solid") {
        var effectId = effects.getId(effect);
        if (effectId) {
          var radio = $("#" + effects.getControlId(effectId));
          radio.prop("checked", true);
          radio.next()[0].scrollIntoView();
          $("#txtColor").val(effectId[1]);
        }

        $("#cpkColor").val(toHtmlColor(effects.getColor(effect)));
      }
    }
  });
}

function saveColor(event) {
  var picker = $("#cpkColor");
  var color = parseColor(picker.val());
  var name = $("#txtColor").val().trim();

  if (name) {
    var data = { "colors": { [name]: color } };
    postJson("/colors", data).done(
      function() {
        var effect = { "id": ["colors", name] };
        applyEffect(effect).done(reloadColors);
      }
    );
  } else {
    alert("Invalid color name!");
  }
}

function deleteColor(event) {
  var name = $("#txtColor").val().trim();

  var sequences = effects.findColorReferences(name);
  var message;

  if(sequences.length > 0)
    message = "The color '" + name + "' is referenced in the following sequences:\n\n" + sequences.join(", ") +
      "\n\nAre you sure want to delete '" + name + "' and all associated sequences?";
  else
    message = "Are you sure want to delete the color '" + name + "'?";

  if(confirm(message)) {
    var picker = $("#cpkColor");
    var color = parseColor(picker.val());
    var data = {"colors": [name]};
    var delColorReq = {
      url: "/colors",
      method: "DELETE",
      data: JSON.stringify(data),
      dataType: "json",
      contentType: 'application/json',
      success: function() {
        applyAnonymousColor(color).done(reloadColors);
      }
    };

    if (sequences.length > 0) {
      //  Delete sequences then delete color
      $.ajax({
        url: "/sequences",
        method: "DELETE",
        data: JSON.stringify({"sequences": sequences}),
        dataType: "json",
        contentType: 'application/json',
        success: function() {
          $.ajax(delColorReq);
        }
      });
    } else {
      $.ajax(delColorReq);
    }
  }
}

function namedColorSelected(event) {
  applyColorById($(event.target).val());
}

function anonymousColorSelected(event) {
  applyAnonymousColor(parseColor($(event.target).val()));
}

function applyColorById(colorId) {
  var effect = { "id": ["colors", colorId] };
  $("#cpkColor").val(toHtmlColor(effects.getColor(effect)));
  $("#txtColor").val(colorId);
  return applyEffect(effect);
}

function applyAnonymousColor(color) {
  var effect = { "effecttype": "solid", "color": color };
  return applyEffect(effect);
}

function applyEffect(effect) {
  if (effect) {
    return postJson("/apply", {"effect": effect});
  }
  return null;
}
