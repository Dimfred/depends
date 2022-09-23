# python-depends

A [FastAPI](https://pypi.org/project/fastapi/) like dependecy injector

## Install

```
# stable
pip3 install python-depends

# latest
pip3 install git+https://github.com/Dimfred/depends.git
```

## Examples

```python
from depends import Depends, inject

async def d1():
    # do some stuff, which takes long
    return "some stuff"

async def d2():
    # do some other stuff, which also takes long
    return "some other stuff"

# inject the dependency into a function
@inject
async def main(d1_=Depends(d1), d2_=Depends(d2)):
    print(d1_)  # some stuff
    print(d2_)  # some other stuff
```

Nested dependencies

```python
from depends import Depends, inject

async def d1():
    # do some stuff, which takes long
    return "some stuff"

async def d2(d1_=Depends(d1)):
    # do some other stuff, which also takes long
    # you can work with d2_ here
    return "some other stuff"

# d1 was called only once and is cached during the whole call
@inject
async def main(d1_=Depends(d1), d2_=Depends(d2)):
    print(d1_)  # some stuff
    print(d2_)  # some other stuff
```

You can also use parameters in your injected function which will be forwarded to your dependencies. The detection is done by name, no type checking is applied here.

```python
from depends import Depends, inject

async def d1(a):
    return a


# d1 was called only once and is cached during the whole call
@inject
async def main(a, d1_=Depends(d1)):
    return a, d1_

assert (await main(1)) == (1, 1)
```

Another cool thing is that you can use context managed objects inside an injected function. Like for example a database session.

```python
from depends import Depends, inject

async def get_db():
    async with Session() as db:
        yield db

@inject
async def main(db=Depends(get_db)):
    # do stuff with your async db connection
    # after the exit the connection will be teared down
```

## TODO

- [ ] support sync dependencies (only async rn)
- [ ] replace the caching mechanism with maybe the correct dependency tree
