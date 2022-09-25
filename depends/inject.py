# -*- coding: utf-8 -*-
import inspect
from functools import wraps

from .dependencies import Dependencies


def inject(f):

    if inspect.iscoroutinefunction(f):

        @wraps(f)
        async def async_wrapper(*args, **kwargs):
            dependencies = Dependencies(f, args, kwargs)

            try:
                await dependencies.setup(kwargs)
                res = await f(*args, **kwargs)
                return res
            except Exception:
                raise
            finally:
                await dependencies.teardown()

        return async_wrapper

    else:  # pragma: no cover

        # TODO not working atm
        @wraps(f)
        def sync_wrapper(*args, **kwargs):
            # dependencies.setup()
            res = f(*args, **kwargs)
            # dependencies.teardown()

            return res

        return sync_wrapper
