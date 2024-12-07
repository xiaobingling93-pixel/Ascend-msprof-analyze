class Singleton(object):
    def __init__(self, cls):
        self._cls = cls
        self._instance = {}

    def __call__(self, args=None):
        if self._cls not in self._instance:
            self._instance[self._cls] = self._cls(args)
        return self._instance[self._cls]
