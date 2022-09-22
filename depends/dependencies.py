# -*- coding: utf-8 -*-
import asyncio
import inspect

from acache import alru_cache

from .dependable import Dependable
from .depends import Depends


def create_cache():
    return alru_cache(None, make_key=lambda self: id(self))


class Dependencies:
    def __init__(self, f, args, kwargs):
        self.f = f
        self._setup_cache = create_cache()
        self._teardown_cache = create_cache()

        self._injection_args = self._make_injection_args(f, args, kwargs)

        self._dependables = {}
        self._create_dependables(f, kwargs)

    def _create_dependables(self, f, kwargs):
        fsig = inspect.signature(f)
        # for each parameter name: value (value is hopefully a Depends obj)
        for var_name, var_value in fsig.parameters.items():
            depends = var_value.default
            # we only want our depedencies
            if not isinstance(depends, Depends):
                continue

            # a dependable is unique based on its function, either we already
            # checked the function if it appears multiple times, or it is new,
            # then we convert it into a Dependable we convert it s.t. it
            # doesn't get cached with the next function call, since the
            # Dependency should then be again reinjected.
            # TODO check if it is cached without it
            key = id(depends.f)
            if key in self._dependables:
                dependable = self._dependables[key]
                # replace the Depends obj with the Dependable
                kwargs[var_name] = dependable
            else:
                dependable = Dependable(
                    depends,
                    self._injection_args,
                    self._setup_cache,
                    self._teardown_cache,
                )
                # replace the Depends obj with the Dependable
                kwargs[var_name] = dependable

                self._dependables[key] = dependable
                # recursively gather the dependencies for the Depends function
                self._create_dependables(dependable._f, dependable._kwargs)

    def _make_injection_args(self, f, args, kwargs):
        fsig = inspect.signature(f)

        # first build from the signature, those will have args where the
        # default value is empty
        res = {
            var_name: var_value.default
            for var_name, var_value in fsig.parameters.items()
            if not isinstance(var_value.default, Depends)
        }

        # update the dict with the kwargs provided to the injected function
        res.update(kwargs)

        # update the args with their corresponding name and provided value
        arg_names = inspect.getfullargspec(f).args
        res.update({arg_name: arg for arg_name, arg in zip(arg_names, args)})

        return res

    async def setup(self, kwargs):
        var_names, coros = [], []

        # We gather all the coros from each Dependable and then execute them
        # all in parallel due to the applied cache, we can be sure that each
        # dependency gets only executed once. Technically this is not true,
        # every Dependable gets called, but the first call is cached and
        # successive calls are just cached calls.
        for var_name, var_value in kwargs.items():
            if not isinstance(var_value, Dependable):
                continue

            var_names.append(var_name)

            dependable = var_value
            coros.append(dependable.setup())

        # store the results of the coros in our top-level function kwargs
        coros = await asyncio.gather(*coros)
        for var_name, res in zip(var_names, coros):
            kwargs[var_name] = res

    async def teardown(self):
        coros = [dependable.teardown() for dependable in self._dependables.values()]
        await asyncio.gather(*coros)
