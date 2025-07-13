from typing import Callable, Union, List, Tuple
from .filters import FilterExpression

class Router:
    def __init__(self):
        self.bot_started_handlers: List[Tuple[Callable, Union[FilterExpression, None]]] = []
        self.message_handlers: List[Tuple[Callable, Union[FilterExpression, None]]] = []
        self.callback_handlers: List[Tuple[Callable, Union[FilterExpression, None]]] = []

    def message(self, filter: FilterExpression = None):
        def decorator(func):
            self.message_handlers.append((func, filter))
            return func
        return decorator

    def callback(self, filter: FilterExpression = None):
        def decorator(func):
            self.callback_handlers.append((func, filter))
            return func
        return decorator

    def bot_started(self, func):
        self.bot_started_handlers.append(func)
        return func
