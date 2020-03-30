from abc import ABC, abstractmethod
import copy

effect_registry = {}
BLACK_COLOR = [0, 0, 0]
WHITE_COLOR = [255, 255, 255]

def register_effect(c):
    if c.effectType() in effect_registry:
        raise Exception(f"{effect_registry[c.effectType()]} is registered as '{c.effectType()}' in the effect registry. Cannot register {c} with the same name. You must the override the effectType() staticmethod.")
    effect_registry[c.effectType()] = c
    return c

class Effect(ABC):
    def __init__(self):
        super().__init__()
        self.prev = None
        self.next = None
        self._duration = None

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, value):
        self._duration = value

    @property
    def startColor(self):
        return self.evaluate(0)

    @property
    def endColor(self):
        return self.evaluate(self.duration - 1)

    @staticmethod
    def compositeKey():
        return None

    @staticmethod
    @abstractmethod
    def effectType():
        return None

    @abstractmethod
    def _evaluate(self, offset):
        pass

    @abstractmethod
    def _loadJSON(self, json):
        pass

    @abstractmethod
    def _toJSON(self):
        pass

    def loadJSON(self, json):
        if "duration" in json:
            self._duration = json["duration"]
        self._loadJSON(json)

    def toJSON(self):
        json = self._toJSON()
        json["effecttype"] = self.effectType()
        json["duration"] = self.duration
        return json

    def evaluate(self, offset):
        offset = max(offset, 0)
        # print(self.effectType(), offset, self.duration)
        if self.duration is None or self.duration == 0 or offset < self.duration:
            return self._evaluate(offset)
        else:
            return None, False

@register_effect
class SolidEffect(Effect):
    def __init__(self, color=None):
        super().__init__()
        self.color = color

    @staticmethod
    def effectType():
        return "solid"

    def _evaluate(self, offset):
        return self.color, not (self.duration is None or (self.duration - offset) > 60)

    def _loadJSON(self, json):
        self.color = json["color"]

    def _toJSON(self):
        return {"color": self.color}

@register_effect
class TransitionEffect(Effect):
    def __init__(self):
        super().__init__()

    @staticmethod
    def effectType():
        return "transition"

    def _evaluate(self, offset):
        start_color = self.prev.endColor[0] if self.prev is not None else BLACK_COLOR
        end_color = self.next.startColor[0] if self.next is not None else BLACK_COLOR
        position = offset / self.duration

        return [round(start_color[i] * (1 - position) + end_color[i] * position) for i in range(3)], True

    def _loadJSON(self, json):
        pass

    def _toJSON(self):
        return {}

@register_effect
class OffEffect(Effect):
    def __init__(self):
        super().__init__()

    @staticmethod
    def effectType():
        return "off"

    def _evaluate(self, offset):
        return BLACK_COLOR, False

    def _loadJSON(self, json):
        pass

    def _toJSON(self):
        return {}

@register_effect
class EffectSequence(Effect):
    def __init__(self):
        super().__init__()
        self.effects = None
        self.sequenceDuration = None

    @property
    def duration(self):
        return self.sequenceDuration if self._duration is None else self._duration

    @duration.setter
    def duration(self, value):
        self._duration = value

    @staticmethod
    def effectType():
        return "sequence"

    @staticmethod
    def compositeKey():
        return "effects"

    def _evaluate(self, offset):
        eidx = 0
        start = 0
        offset *= (self.sequenceDuration / self.duration)
        neffects = len(self.effects)

        for effect in self.effects:
            if start + effect.duration > offset:
                return effect.evaluate(offset - start)
            start += effect.duration

        return None, False

    def _loadJSON(self, json):
        self.effects = []
        duration = 0
        prev = None
        for ej in json[self.compositeKey()]:
            e = effect_registry[ej["effecttype"]]()
            e.loadJSON(ej)
            e.prev = prev
            if prev:
                prev.next = e
            self.effects.append(e)
            duration += e.duration
            prev = e

        self.sequenceDuration = duration

    def _toJSON(self):
        jeffects = []
        for e in self.effects:
            jeffects.append(e.toJSON())
        return { self.compositeKey(): jeffects }

@register_effect
class LoopedEffectSequence(Effect):
    def __init__(self):
        super().__init__()
        self.sequence = None

    @staticmethod
    def effectType():
        return "loop"

    @staticmethod
    def compositeKey():
        return "sequence"

    def _evaluate(self, offset):
        return self.sequence.evaluate(offset % self.sequence.duration)

    def _loadJSON(self, json):
        self.sequence = EffectSequence()
        self.sequence.loadJSON(json[self.compositeKey()])

    def _toJSON(self):
        return { self.compositeKey(): self.sequence.toJSON() }

class ConfigEffectTransformer:
    class Namespace:
        def __init__(self, effectType, fromId=lambda c: c):
            self.effectType = effectType
            self.fromId = fromId

    class Reference:
        def __init__(self, key, namespace):
            self.key = key
            self.namespace = namespace

    def __init__(self, config):
        self.config = config
        self.namespaces = {
            "colors": ConfigEffectTransformer.Namespace(
                effectType=SolidEffect.effectType(),
                fromId=lambda c: SolidEffect(c).toJSON()
            ),
            "sequences": ConfigEffectTransformer.Namespace(
                effectType=EffectSequence.effectType()
            )
        }
        self.references = {
            LoopedEffectSequence.effectType(): ConfigEffectTransformer.Reference(
                key="sequence",
                namespace="sequences"
            ),
            SolidEffect.effectType(): ConfigEffectTransformer.Reference(
                key="color",
                namespace="colors"
            )
        }

    def transform(self, effectConfig):
        expandedConfig = self._expand(copy.deepcopy(effectConfig), copy.deepcopy(self.config.get()))
        effect = effect_registry[expandedConfig["effecttype"]]()
        effect.loadJSON(expandedConfig)

        return effect

    def _expand(self, effectConfig, settings):
        effect = None

        if "id" in effectConfig:
            # eg. { "id": ["colors", "white"], duration: 10 }
            eid = effectConfig["id"]
            v = settings[eid[0]][eid[1]]
            effect = self.namespaces[eid[0]].fromId(v)
            if "duration" in effectConfig:
                effect["duration"] = effectConfig["duration"]
        else:
            effect = effectConfig

        etype = effect["effecttype"]
        if etype in self.references:
            eref = self.references[etype]
            if isinstance(effect[eref.key], str):
                effect[eref.key] = settings[eref.namespace][effect[eref.key]]

        ckey = effect_registry[etype].compositeKey()
        if ckey is not None:
            if isinstance(effect[ckey], list):
                effect[ckey] = [self._expand(e, settings) for e in effect[ckey]]
            else:
                effect[ckey] = self._expand(effect[ckey], settings)

        return effect


# class ScheduledEffectSequence(EffectSequence):
#     def __init__(self):
#         super().__init__()
#
#     def evaluate(self, offset):
#         pass
