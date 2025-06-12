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