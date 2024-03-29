from __future__ import annotations
from enum import Enum, auto
from typing import Dict, Any
from importlib import import_module

Payload = Dict[str, Any]


class RoomState(Enum):
    open = auto()
    close = auto()
    done = auto()
    
class ProcessState(Enum):
    none = auto()
    started = auto()
    finished = auto()
    done = auto()
    
class PurchaseState(Enum):
    incoming = auto()
    received = auto()

class ProductState(Enum):
    initial = auto()
    scanned = auto()
    done = auto()



class State(object):
    def __init__(self, states: Enum, active:int = 1) -> None:
        self.states = states
        self.active = active

    def __repr__(self) -> str:
        return str(self.states(self.active))

    def current(self) -> str:
        return self.states(self.active).name

    def bump(self):
        if self.active == len(list(self.states)):
            raise ValueError(f"{self} inexistant next state")
        self.active += 1

    def bump_to(self, next_state: str):
        existing_state = [x.name for x in list(self.states)]
        if (
            next_state not in existing_state
            or self.states[next_state].value < self.active  # noqa: W503
        ):
            raise ValueError(f"You must bump to a further state than {self}")
        self.active = self.states[next_state].value

    def rollback(self):
        if self.active == 1:
            raise ValueError(f"{self} inexistant previous state")
        self.active -= 1

    def rollback_to(self, previous_state: str):
        existing_states = [x.name for x in list(self.states)]
        if (
            previous_state not in existing_states
            or self.states[previous_state].value > self.active  # noqa: W503
        ):
            raise ValueError(
                f"You must rollback to a previous state than {self} ({existing_states})"
            )
        self.active = self.states[previous_state].value

    def is_passed(self, state: str) -> bool:
        return self.states[state].value <= self.active
    
    def take_max(self, other: State) -> None:
        self.active = max(self.active, other.active)
    