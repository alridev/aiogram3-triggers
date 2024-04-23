
#  *-+-+-+-+ +-+-+ +-+-+-+-+-+-+-+-+-+-* #
#  |S|o|f|t| |b|y| |@|z|c|x|w|_|l|o|l|z| #
#  *-+-+-+-+ +-+-+ +-+-+-+-+-+-+-+-+-+-* #


import asyncio
import inspect
from dataclasses import dataclass
from typing import *

from aiogram import Bot, Dispatcher, Router
from aiogram.dispatcher.event.event import CallbackType, EventObserver
from aiogram.dispatcher.event.handler import CallableObject
from aiogram.handlers import BaseHandler


@dataclass
class TriggerHandlerObject(CallableObject):
    run_on_start: bool = False
    seconds: int | float = 1000

    def __post_init__(self) -> None:
        super(TriggerHandlerObject, self).__post_init__()
        callback = inspect.unwrap(self.callback)
        if inspect.isclass(callback) and issubclass(callback, BaseHandler):
            self.awaitable = True

    async def check(self, *args: Any, **kwargs: Any) -> Tuple[bool, Dict[str, Any]]:
        if not self.filters:
            return True, kwargs
        for event_filter in self.filters:
            check = await event_filter.call(*args, **kwargs)
            if not check:
                return False, kwargs
            if isinstance(check, dict):
                kwargs.update(check)
        print(1)
        return True, kwargs


class TriggerEvent(EventObserver):
    def register(
        self,
        callback: CallbackType,
        seconds: int | float, run_on_start: bool = False,
    ) -> CallbackType:
        """
        Register event handler
        """

        self.handlers.append(
            TriggerHandlerObject(
                callback=callback,
                run_on_start=run_on_start,
                seconds=seconds,
            )
        )

        return callback

    def __call__(
        self,
        seconds: int | float, run_on_start: bool = False,
        **kwargs: Any,
    ) -> Callable[[CallbackType], CallbackType]:
        """
        Decorator for registering event handlers
        """

        def wrapper(callback: CallbackType) -> CallbackType:
            self.register(callback, seconds, run_on_start, **kwargs)
            return callback

        return wrapper


class TriggerHandler:
    handlers: Dict[str, CallableObject] = {}

    def append(self, handler: CallableObject, seconds: int | float, run_on_start: bool = False,
               ):
        self.handlers[hex(id(handler))] = dict(
            handler=handler,
            seconds=seconds,
            run_on_start=run_on_start,
        )

    async def _task(self, handler, seconds: int | float, bot: Bot, dispatcher: Dispatcher, run_on_start: bool = False):
        status = 'created'
        while True:
            if status == 'created' and run_on_start:
                await handler(dispatcher, bot)
                status = 'running'
                await asyncio.sleep(seconds)
                continue
            status = 'running'
            await handler(dispatcher, bot)
            await asyncio.sleep(seconds)

    async def _emit_trigger(self, bot: Bot, dispatcher: Dispatcher, *args, **kwargs):
        loop = asyncio.get_event_loop()
        [
            loop.create_task(
                self._task(
                    **handler,
                    bot=bot,
                    dispatcher=dispatcher
                )
            )
            for handler in self.handlers.values()
        ]

    def __call__(self, seconds: int | float, run_on_start: bool = False,):
        def wrapper(func):
            self.append(func, seconds, run_on_start)
        return wrapper


class TRouter(Router):
    def __init__(self, *, name: str = None):
        super(TRouter, self).__init__(name=name)
        self.triggers_handler = TriggerHandler()
        self.emit_startup = self.triggers_handler._emit_trigger



