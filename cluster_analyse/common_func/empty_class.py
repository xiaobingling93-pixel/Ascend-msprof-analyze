class EmptyClass:

    def __init__(self: any, info: str = "") -> None:
        self._info = info

    @classmethod
    def __bool__(cls: any) -> bool:
        return False

    @classmethod
    def __str__(cls: any) -> str:
        return ""

    @property
    def info(self: any) -> str:
        return self._info

    @staticmethod
    def is_empty() -> bool:
        return True
