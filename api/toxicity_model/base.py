from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or {}
        self._ready = False

    @abstractmethod
    def load(self) -> None:
        ...

    @abstractmethod
    def infer(self, batch):
        ...

    def health(self) -> dict:
        return {"ready": self._ready}
