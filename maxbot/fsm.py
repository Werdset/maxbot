# fsm.py

class State:
    def __init__(self, name: str = None):
        self.name = name
        self.group_name = None

    def full_name(self):
        return f"{self.group_name}:{self.name}" if self.group_name else self.name

    def __repr__(self):
        return f"<State {self.full_name()}>"

class StatesGroupMeta(type):
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        for key, value in namespace.items():
            if isinstance(value, State):
                value.name = key
                value.group_name = name
                setattr(cls, key, value)
        return cls

class StatesGroup(metaclass=StatesGroupMeta):
    pass


class FSMStorage:
    def __init__(self):
        self._states = {}
        self._data = {}

    def set_state(self, user_id: int, state: State):
        self._states[user_id] = state.full_name()
        self._data.setdefault(user_id, {})

    def get_state(self, user_id: int):
        return self._states.get(user_id)

    def reset_state(self, user_id: int):
        self._states.pop(user_id, None)
        self._data.pop(user_id, None)

    def update_data(self, user_id: int, **kwargs):
        self._data.setdefault(user_id, {}).update(kwargs)

    def get_data(self, user_id: int):
        return self._data.get(user_id, {})
