from enum import Enum

ROOM_STATE = Enum("RoomState", ["open", "close", "done"])
PROCESS_STATE = Enum("ProcessState", ["none", "started", "finished", "done"])
PURCHASE_STATE = Enum("PurchaseState", ["incoming", "received"])
PRODUCT_STATE = Enum("ProductState", ["initial", "queue", "done"])


class State(object):
    def __init__(self, states: Enum) -> None:
        self.states = states
        self.active = 1

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
            or self.states[next_state].value <= self.active  # noqa: W503
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
            or self.states[previous_state].value <= self.active  # noqa: W503
        ):
            raise ValueError(
                f"You must rollback to a previous state than {self} ({existing_states})"
            )
        self.active = self.states[previous_state].value
