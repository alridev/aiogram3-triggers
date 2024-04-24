
#  *-+-+-+-+ +-+-+ +-+-+-+-+-+-+-+-+-+-* #
#  |S|o|f|t| |b|y| |@|z|c|x|w|_|l|o|l|z| #
#  *-+-+-+-+ +-+-+ +-+-+-+-+-+-+-+-+-+-* #
import json
import pytz
import asyncio
import inspect
import datetime
import os
from dataclasses import dataclass
from typing import Any, Tuple, Dict, Callable

from aiogram import Bot, Dispatcher, Router
from aiogram.dispatcher.event.event import CallbackType, EventObserver
from aiogram.dispatcher.event.handler import CallableObject
from aiogram.handlers import BaseHandler


@dataclass
class TriggerHandlerObject(CallableObject):
    run_on_start: bool = False
    value: int | float = 1000

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
        return True, kwargs


class TriggerEvent(EventObserver):
    def register(
        self,
        callback: CallbackType,
        value: int | float, run_on_start: bool = False,
    ) -> CallbackType:
        """
        Register event handler
        """

        self.handlers.append(
            TriggerHandlerObject(
                callback=callback,
                run_on_start=run_on_start,
                value=value,
            )
        )

        return callback

    def __call__(
        self,
        value: int | float, run_on_start: bool = False,
        **kwargs: Any,
    ) -> Callable[[CallbackType], CallbackType]:
        """
        Decorator for registering event handlers
        """

        def wrapper(callback: CallbackType) -> CallbackType:
            self.register(callback, value, run_on_start, **kwargs)
            return callback

        return wrapper


class TriggerHandler:
    handlers: Dict[str, CallableObject] = {}

    def __init__(self, datetime_timezone: str, func_get_param: Callable, func_save_param: Callable) -> None:
        self.datetime_timezone = pytz.timezone(datetime_timezone)

        _now = datetime.datetime.now(self.datetime_timezone)
        self._default_params = {
            'minute': _now.minute,
            'second': _now.second,
            'day': _now.day,
            'month': _now.month,
            'year':  _now.year,
        }
        if func_get_param and func_save_param:
            self.get_param = func_get_param
            self.save_param = func_save_param
        else:
            self.get_param = self.default_get_param
            self.save_param = self.default_save_param
            self.default_save_param(False, False, **self._default_params)

    def append(self, handler: CallableObject, value: int | float, run_on_start: bool = False,):
        self.handlers[hex(id(handler))] = dict(
            handler=handler,
            value=value,
            run_on_start=run_on_start,
        )

    @staticmethod
    def _default_read_atrange():
        with open('.atrange', 'r+', encoding='utf-8', errors='ignore') as atrange_fp:
            return atrange_fp.read()

    @staticmethod
    def default_get_param(type: str):
        with open('.atrange', 'r+', encoding='utf-8', errors='ignore') as atrange_fp:
            return json.loads(atrange_fp.read())[type]

    @staticmethod
    def default_save_param(type: str, value: int, **default_data):
        if type and value:
            old_data = json.loads(TriggerHandler._default_read_atrange())
            old_data[type] = value
            with open('.atrange', 'w+', encoding='utf-8', errors='ignore') as atrange_fp:
                json.dump(old_data, atrange_fp, ensure_ascii=False)
        else:
            with open('.atrange', 'w+', encoding='utf-8', errors='ignore') as atrange_fp:
                json.dump(default_data, atrange_fp, ensure_ascii=False)

    async def _task(self, handler, value: int | float | str, bot: Bot, dispatcher: Dispatcher, run_on_start: bool = False):
        status = 'created'
        if isinstance(value, float) or isinstance(value, int):
            while True:
                if status == 'created' and run_on_start:
                    await handler(dispatcher, bot)
                    status = 'running'
                    await asyncio.sleep(value)
                    continue

                status = 'running'
                await handler(dispatcher, bot)
                await asyncio.sleep(value)

        elif isinstance(value, str):
            if value not in ['day', 'year', 'month', 'second', 'minute']:
                raise Exception('Value interval allowed only: day, year, month, minute, second')
            while True:
                if status == 'created' and run_on_start:
                    await handler(dispatcher, bot)
                    status = 'running'
                    continue
                now = datetime.datetime.now(self.datetime_timezone)  # .date()
                if value == 'day' and now.day != self.get_param('day'):
                    await handler(dispatcher, bot)
                    self.save_param('day', now.day)

                elif value == 'minute' and now.minute != self.get_param('minute'):
                    await handler(dispatcher, bot)
                    self.save_param('minute', now.minute)

                elif value == 'second' and now.second != self.get_param('second'):
                    await handler(dispatcher, bot)
                    self.save_param('second', now.second)

                elif value == 'month' and now.month != self.get_param('month'):
                    await handler(dispatcher, bot)
                    self.save_param('month', now.month)

                elif value == 'year' and now.year != self.get_param('year'):
                    await handler(dispatcher, bot)
                    self.save_param('year', now.year)

                await asyncio.sleep(1)
        else:
            raise Exception('Value is not float, int, str')

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

    def __call__(self, value: int | float | str, run_on_start: bool = False,):
        """
            value - seconds or day,mouth,year
            example:
                value = 10 # 10seconds
                value = 42.13 # 42.13 seconds
                value = "day" # on new day [req: get_param,save_param else save to file .atrange]
                value = "mouth" # on new month [req: get_param,save_param else save to file .atrange] 
                value = "year" # on new year [req: get_param,save_param else save to file .atrange] 
                value = "second" # on new second [req: get_param,save_param else save to file .atrange] 
                value = "minute" # on new minute [req: get_param,save_param else save to file .atrange] 

        """
        def wrapper(func):
            self.append(func, value, run_on_start)
        return wrapper


class TRouter(Router):
    def __init__(
            self, *, name: str = None, datetime_timezone: str = "Europe/Moscow", func_get_param: Callable = None,
            func_save_param: Callable = None):
        """
            timezone = "Europe/Moscow"
            func_get_param = function(key: str) -> int
            func_save_param = function(key: str, value: int) -> None
        """
        super(TRouter, self).__init__(name=name)
        self.triggers_handler = TriggerHandler(datetime_timezone, func_get_param, func_save_param)
        self.emit_startup = self.triggers_handler._emit_trigger
