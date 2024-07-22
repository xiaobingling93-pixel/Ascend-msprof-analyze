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
        return Decimal(self.ts) <= Decimal(event.ts) and Decimal(self.ts) + Decimal(self.dur) >= Decimal(
            event.ts) + Decimal(
            event.dur)