class FilterExpression:
    def __init__(self, attr: str):
        self.attr = attr
        self.op = None
        self.value = None

    def __eq__(self, other):
        self.op = "eq"
        self.value = other
        return self

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
