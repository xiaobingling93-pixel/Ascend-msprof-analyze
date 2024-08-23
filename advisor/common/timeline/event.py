from decimal import Decimal


class AdvisorDict(dict):
    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)

    def __getattr__(self, key: str):
        if key not in self:
            return {}

        value = self[key]
        if isinstance(value, dict):
            value = AdvisorDict(value)
        return value


class TimelineEvent(AdvisorDict):

    def ts_include(self, event):
        self_ts = self.ts
        event_ts = event.ts

        if not self_ts or not event_ts:
            return False

        self_dur = self.dur if self.dur else 0.0
        event_dur = event.dur if event.dur else 0.0

        return Decimal(self_ts) <= Decimal(event_ts) and Decimal(self_ts) + Decimal(self_dur) >= Decimal(
            event_ts) + Decimal(event_dur)
