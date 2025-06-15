from maxbot.fsm import State


class FilterExpression:
    def __init__(self, attr: str, op: str = None, value: any = None):
        self.attr = attr
        self.op = op
        self.value = value

    def __eq__(self, other):
        return FilterExpression(self.attr, "eq", other)

    def check(self, data):
        value = data
        for part in self.attr.split("."):
            value = getattr(value, part, None)

        if self.op == "eq":
            return value == self.value

        return False


class FMeta:
    def __getattr__(self, item):
        return FilterExpression(item)

F = FMeta()


class StateFilter:
    def __init__(self, state: State):
        self.state = state.full_name()

    def check(self, data):
        user_id = data.user.id if hasattr(data, 'user') else data.sender.id
        state = data.dispatcher.storage.get_state(user_id)
        return state == self.state
    
    
class TextStartsFilter(FilterExpression):
    def __init__(self, prefix: str):
        self.prefix = prefix

    def check(self, update) -> bool:
        return getattr(update, "payload", "").startswith(self.prefix)
