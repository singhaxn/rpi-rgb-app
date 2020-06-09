var effects = null;
var activeSequence = null;

class SequenceItem {
  constructor(parent, effect=null) {
    if (effect) {
      this.effectType = effect["effecttype"];
      this.duration = effect["duration"];
      this.color = this.effectType == "solid" ? effect["color"] : null;
    } else {
      this.effectType = "solid";
      this.duration = 0;
      this.color = "";
    }
    this.parent = parent;

    this.createPanel();
  }

  createPanel() {
    var template = $("#tmpEffect")[0];
    var panel = $(template.innerHTML);
    var txtDuration = panel.find(".effect-duration");
    var selType = panel.find(".effect-type");
    var selColor = panel.find(".effect-color");
    var btnDelete = panel.find('input[name="delete"]');

    panel.data("sequence-item", this);

    txtDuration.keyup(this.durationKeyUp.bind(this));
    txtDuration.change(this.durationChanged.bind(this));
    txtDuration.val(secondsToTime(this.duration));

    selType.change(this.typeChanged.bind(this));
    selType.val(this.effectType);

    selColor.change(this.colorChanged.bind(this));

    var colors = effects.effects["colors"];

    // var option = $(new Option("", ""));
    // selColor.append(option);
    for (var cname in colors) {
      var option = $(new Option(cname, cname));
      option.css("background-color", "rgb(" + colors[cname].join(",") + ")");
      selColor.append(option);
    }

    if (this.effectType == "solid") {
      if (this.color)
        selColor.val(this.color);
      else
        this.color = selColor.val();
      selColor.css("background-color", "rgb(" + colors[this.color].join(",") + ")");
      selColor.show();
    } else {
      selColor.hide();
    }

    btnDelete.click(this.deleteClicked.bind(this));

    this.panel = panel;
    this.txtDuration = txtDuration;
    this.selType = selType;
    this.selColor = selColor;
    this.btnDelete = btnDelete;
  }

  durationKeyUp(event) {
    var txt = $(event.target);
    var time = parseTime(txt.val().trim());

    if (time) {
      txt.css("background-color", "");
    } else {
      txt.css("background-color", "#ffcccc");
    }
  }

  durationChanged(event) {
    var txt = $(event.target);
    var time = parseTime(txt.val().trim());

    if (time) {
      this.duration = (time["hours"] * 60 + time["minutes"]) * 60 +
          time["seconds"];
    }

    txt.val(secondsToTime(this.duration));
    this.parent.durationChanged(this);
  }

  typeChanged(event) {
    var sel = $(event.target);
    this.effectType = sel.val();

    if (this.effectType == "solid") {
      if (!this.color)
        this.color = this.selColor.val();
      var carr = effects.effects["colors"][this.color];
      this.selColor.css("background-color", "rgb(" + carr.join(",") + ")");
      this.selColor.show();
    } else
      this.selColor.hide();

    this.parent.typeChanged(this);
  }

  colorChanged(event) {
    var sel = $(event.target);
    this.color = sel.val();
    var carr = this.color ? effects.effects["colors"][this.color] : [0, 0, 0];
    sel.css("background-color", "rgb(" + carr.join(",") + ")");
    this.parent.colorChanged(this);
  }

  deleteClicked(event) {
    this.panel.remove();
    this.parent.deleteClicked(this);
  }

  toJSON() {
    var result = {
      "effecttype": this.effectType,
      "duration": this.duration
    };

    if (this.effectType == "solid")
      result["color"] = this.color;

    return result;
  }
}

class ActiveSequence {
  constructor(divPreview, divSequence, sequence=null) {
    this.effects = [];
    this.divPreview = divPreview;
    this.divSequence = divSequence;
    this.divSequence.empty();

    if (sequence) {
      var seq = effects.getSequence(sequence);
      seq = seq["effects"];
      for (var si=0; si<seq.length; si++) {
        this.addEffect(seq[si]);
      }
    } else {
      this.divSequence.text("Empty Sequence");
    }

    this.updateDisplay();
  }

  addEffect(effect=null) {
    var item = new SequenceItem(this, effect);
    if (this.effects.length == 0)
      this.divSequence.empty();
    this.effects.push(item);
    this.divSequence.append(item.panel);
    return item;
  }

  durationChanged(item) {
    this.updateDisplay();
  }

  typeChanged(item) {
    this.updateDisplay();
  }

  colorChanged(item) {
    this.updateDisplay();
  }

  deleteClicked(item) {
    var index = this.effects.indexOf(item);
    this.effects.splice(index, 1);
    if (this.effects.length == 0)
      this.divSequence.text("Empty Sequence");
    this.updateDisplay();
  }

  moved(itemContainer) {
    var item = itemContainer.data("sequence-item");
    this.effects.splice(this.effects.indexOf(item), 1);

    var prevContainer = itemContainer.prev();
    if (prevContainer.length > 0) {
      var prev = prevContainer.data("sequence-item");
      this.effects.splice(this.effects.indexOf(prev) + 1, 0, item);
    } else {
      this.effects.unshift(item);
    }

    this.updateDisplay();
  }

  updateDisplay() {
    var seq = this.toJSON();
    if (seq)
      seq = seq["effects"];
    else
      seq = [];

    buildSequencePreview(seq, effects, this.divPreview);
  }

  validate() {
    var errors = [];
    var prev = null;
    for (var ei=0; ei<this.effects.length; ei++) {
      var effect = this.effects[ei];
      if (effect.effectType == "solid") {
        if (!effect.color)
          errors.push([ei, "Color not specified"]);
      } else {
        if(prev && prev.effectType == "transition")
          errors.push([ei, "Consecutive transitions are not allowed"]);
      }

      prev = effect;
    }

    if (errors.length > 0) {
      console.error(errors);
      alert(errors);
      return false;
    }

    return true;
  }

  toJSON() {
    if (this.effects.length == 0)
      return null;

    var elist = [];
    for (var ei=0; ei<this.effects.length; ei++) {
      elist.push(this.effects[ei].toJSON());
    }

    var result = {"effecttype": "sequence", "effects": elist};
    console.info(result);

    return result;
  }
}

$(document).ready(
  function() {
    $("#btnBack").click(function(event) {
      history.back();
    });

    $("#btnNew").click(newSequence);
    $("#btnSave").click(saveSequence);
    $("#btnDelete").click(deleteSequence);
    $("#btnPlay").click(playSequence);
    $("#btnAddEffect").click(addEffect);
    $("#divSequence").sortable({
      handle: ".handle",
      stop: function(event, ui) {
        activeSequence.moved(ui.item);
      }
    });

    reloadSequences();
  }
)

function reloadSequences() {
  var squencesContainer = $("#divSequenceSelect");
  squencesContainer.empty();
  $("#txtSequence").val("");

  $.get({
    url: "/effects",
    dataType: "json",
    success: function (data) {
      console.log(data);
      var presets = data["effects"];
      effects = new Effects(presets);

      var sequences = presets["sequences"];
      var effect = presets["effect"];

      for(var skey in sequences) {
        var option = createSequenceOption(skey, sequences[skey], effects, namedSequenceSelected);
        squencesContainer.append(option);
      }

      var effectType = effects.getType(effect);
      if (effectType == "sequence" || effectType == "loop") {
        var effectId = effects.getId(effect);
        if (effectId) {
          var radio = $("#" + effects.getControlId(effectId));
          radio.prop("checked", true);
          radio.next()[0].scrollIntoView();
          $("#txtSequence").val(effectId[1]);
          loadSequenceById(effectId[1]);
        } else {
          loadSequence(effect);
        }

        $("#chkLoop").prop("checked", effectType == "loop");
      } else {
        loadSequence(null);
      }
    }
  });
}

function loadSequenceById(sequenceId) {
  loadSequence(effects.effects["sequences"][sequenceId]);
}

function loadSequence(sequence) {
  activeSequence = new ActiveSequence($("#divPreview"), $("#divSequence"), sequence);
  $("#chkLoop").prop("checked", false);
}

function playSequence(event) {
  if (activeSequence.validate()) {
    var effect = activeSequence.toJSON();
    if($("#chkLoop").prop("checked"))
      effect = {"effecttype": "loop", "sequence": effect};
    return applyEffect(effect);
  }
  return null;
}

function newSequence(event) {
  loadSequence(null);
  $("#txtSequence").val("");
  $('input[name="grpSequence"]').prop("checked", false);
}

function saveSequence(event) {
  if (activeSequence.validate()) {
    var key = $("#txtSequence").val();
    var value = activeSequence.toJSON()
    postJson("/sequences", {"sequences": {[key]: value}}).done(
      function() {
        applySequenceById(key).done(reloadSequences);
      }
    );
  }
}

function deleteSequence(event) {
  var name = $("#txtSequence").val().trim();

  if(confirm("Are you sure want to delete the sequence '" + name + "'?")) {
    var data = {"sequences": [name]};

    $.ajax({
      url: "/sequences",
      method: "DELETE",
      data: JSON.stringify(data),
      dataType: "json",
      contentType: 'application/json',
      success: function() {
        var t = playSequence(null);
        if(t)
          t.done(reloadSequences);
        else
          reloadSequences();
      }
    });
  }
}

function addEffect(event) {
  activeSequence.addEffect();
  $('#divSequence').scrollTop($('#divSequence')[0].scrollHeight);
}

function namedSequenceSelected(event) {
  applySequenceById($(event.target).val());
}

function applySequenceById(sequenceId) {
  var effect = { "id": ["sequences", sequenceId] };
  loadSequenceById(sequenceId);
  $("#txtSequence").val(sequenceId);
  return applyEffect(effect);
}

function applyEffect(effect) {
  if (effect) {
    return postJson("/apply", {"effect": effect});
  }
  return null;
}
