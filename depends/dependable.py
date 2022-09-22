# -*- coding: utf-8 -*-
import asyncio
import copy
import inspect


async def anext(agen):
    try:
        return await agen.__anext__()
    except StopAsyncIteration:
        return None


class Dependable:
    def __init__(self, depends, injection_args, setup_cache, teardown_cache):
        self._f = depends.f
        self._args = copy.deepcopy(depends.args)
        self._kwargs = copy.deepcopy(depends.kwargs)
        self._injection_args = injection_args
        self._called = None

        self._deco_setup = setup_cache(self._setup)
        self._deco_teardown = teardown_cache(self._teardown)

    async def setup(self):
        return await self._deco_setup(self)

    async def teardown(self):
        return await self._teardown(self)

    # TODO hack because else the wrapping of a classmethod does not inject the
    # self argument which we need for the key
    async def _setup(self, *_):
        # apply and gather all the Dependables of this Dependable
        # (Dependables can be build out of Dependables)
        # aka. using Depends in another function which also uses Depends
        args, coros = [], []
        for name, value in self._kwargs.items():
            if not isinstance(value, Dependable):
                continue

            args.append(name)
            coros.append(value.setup())

        coros = await asyncio.gather(*coros)
        for arg, res in zip(args, coros):
            self._kwargs[arg] = res

        # fill the args and kwargs for this dependable from our top level
        # injected function
        fsig = inspect.signature(self._f)
        for var_name in fsig.parameters.keys():
            if var_name not in self._injection_args:
                continue

            self._kwargs[var_name] = self._injection_args[var_name]

        self._called = self._f(*self._args, **self._kwargs)
        if inspect.isasyncgenfunction(self._f):
            return await anext(self._called)

        return await self._called

    async def _teardown(self, *_):
        if inspect.isasyncgenfunction(self._f):
            await anext(self._called)
