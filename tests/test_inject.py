# -*- coding: utf-8 -*-
import asyncio
import time

import pytest

from depends import Depends, inject


class Stopwatch:
    def __init__(self):
        self.t = time.perf_counter()

    def __call__(self):
        now = time.perf_counter()
        passed = now - self.t
        self.t = now

        return passed


counter = 0


@pytest.fixture
def reset_counter():
    global counter

    counter = 0


@pytest.mark.asyncio
async def test_basic_nested_dependencies():
    async def d1():
        await asyncio.sleep(0.2)
        return "1"

    async def d2():
        await asyncio.sleep(0.2)
        return "2"

    async def d3(d1_=Depends(d1)):
        await asyncio.sleep(0.2)
        return f"3:{d1_}"

    @inject
    async def main(d1_=Depends(d1), d2_=Depends(d2), d3_=Depends(d3)):
        await asyncio.sleep(0.2)
        return f"4:{d1_}:{d2_}:{d3_}"

    sw = Stopwatch()
    res = await main()
    took = sw()

    assert "4:1:2:3:1" == res
    # if the dependencies weren't cached they would be triggered multiple times
    # hence the time should be way higher than the longest chain
    # the longest chain here is d1 -> d3 -> main, hence ~0.6s
    # it could be slower if you have a potato pc tho
    assert 0.7 > took


@pytest.mark.asyncio
async def test_main_args_are_injected():
    async def d1(a):
        return a

    # 'a' here is the same 'a' as in the dependency
    @inject
    async def main(a, d1_=Depends(d1)):
        return a, d1_

    assert (1, 1) == (await main(1))


@pytest.mark.asyncio
async def test_main_depends_args_and_kwargs_are_injected():
    async def d1(a, b=1):
        return a, b

    @inject
    async def main1(d1_=Depends(d1, 0)):
        return d1_

    assert (0, 1) == (await main1())

    @inject
    async def main2(d1_=Depends(d1, 2, 3)):
        return d1_

    assert (2, 3) == (await main2())

    @inject
    async def main3(d1_=Depends(d1, a=4, b=5)):
        return d1_

    assert (4, 5) == (await main3())


@pytest.mark.asyncio
async def test_main_kwargs_are_injected():
    async def d1(a):
        return a

    # 'a' here is the same 'a' as in the dependency
    @inject
    async def main(a=1, d1_=Depends(d1)):
        return a, d1_

    assert (1, 1) == (await main())
    assert (2, 2) == (await main(2))
    assert (3, 3) == (await main(a=3))


@pytest.mark.asyncio
async def test_calls_to_same_main_can_be_run_in_parallel():
    async def d1(a):
        await asyncio.sleep(0.2)
        return a

    async def d2(b):
        await asyncio.sleep(0.2)
        return b

    @inject
    async def main(a, b, d1_=Depends(d1), d2_=Depends(d2)):
        await asyncio.sleep(0.2)
        return d1_, d2_

    sw = Stopwatch()
    res = await asyncio.gather(
        main(1, 2), main(3, 4), main(5, 6), main(7, 8), main(9, 10)
    )
    took = sw()

    assert 0.45 > took
    assert [(1, 2), (3, 4), (5, 6), (7, 8), (9, 10)] == res


alive = False


@pytest.mark.asyncio
async def test_teardown_with_generator():
    global alive

    class CTXManaged:
        async def __aenter__(self):
            global alive

            alive = True

            return self

        async def __aexit__(self, *_):
            global alive

            alive = False

    async def d1():
        async with CTXManaged() as a:
            yield a

    @inject
    async def main(d1_=Depends(d1)):
        global alive

        assert alive

    assert not alive  # dead
    await main()  # alive
    assert not alive  # dead


@pytest.mark.asyncio
async def test_teardown_with_generator_with_error():
    global alive

    class CTXManaged:
        async def __aenter__(self):
            global alive

            alive = True

            return self

        async def __aexit__(self, *_):
            global alive

            alive = False

    async def d1():
        async with CTXManaged() as a:
            yield a

    @inject
    async def main(d1_=Depends(d1)):
        global alive

        raise Exception()

    assert not alive  # dead
    try:
        await main()  # alive
    except Exception:
        assert not alive  # dead
