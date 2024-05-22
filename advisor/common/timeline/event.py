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

        return float(self.ts) <= float(event.ts) and float(self.ts) + float(self.dur) >= float(event.ts) + float(
            event.dur)