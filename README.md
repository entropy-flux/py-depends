# PyDepends

A lightweight Python dependency injection library that simplifies managing dependencies in both synchronous and asynchronous code, using decorators in a FastAPI-like style.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
---

## Features

- Dependency injection with support for synchronous and asynchronous dependencies.
- Dependency overrides via a provider for easy testing and configuration.
- Context-managed dependency lifecycles with support for generators and async generators.
- Simple API with decorators and wrappers for clean, maintainable code.

---

## Installation

```bash
pip install pydepends
```


## Quickstart

Define dependencies in a simple way.

``` python
from asyncio import run
from pydepends import inject, Depends, Provider

async def dependency() -> int:
    return 5

provider = Provider()

@inject(provider)
async def main(x: int, y: int, z: int = Depends(dependency)) -> int:
    return x + y + z

assert run(main(1, 2)) == 8
```

Here’s a simple example showing how to define dependencies as a dependency tree:

``` python
from pydepends import inject, Depends 
 
def left_leaf_dependency():
    return 2

async def right_leaf_dependency():
    yield 3 #generators supported
 
async def right_node_dependency(leaf = Depends(right_leaf_dependency)):
    return leaf * 5
 
async def root_dependency(left: int = Depends(left_leaf_dependency), right: int = Depends(right_node_dependency)) -> int:
    return left * right * 7
```

Inject the dependencies in a sync function:

```python 
from pydepends import Provider
 
provider = Provider()

@inject(provider)
def handle_dependency(root: int = Depends(root_dependency)) -> int:
    return root * 11
 
value = handle_dependency()

assert value == 2 * 3 * 5 * 7 * 11
print(f"Computed value: {value}")  # Output: Computed value: 2310
```

Or inject them in an async function. Sync dependencies are put into an asyncio thread to avoid blocking the event loop. 

```python
@inject(provider)
async def async_handle_dependency(root: int = Depends(root_dependency)):
    return root*11

async def main():
    value = await async_handle_dependency()
    assert value == 2*3*5*7*11 
    print(f"Computed value: {value}")  # Output: Computed value: 2310


import asyncio
asyncio.run(main())
```

How it works
- `Depends` wraps a callable into a Dependency object.
- Provider allows overriding dependencies (useful for testing or different environments).
- The @inject decorator resolves and injects dependencies based on the provider.
- Supports both synchronous and asynchronous callables, managing contexts as needed.


## License

This project is licensed under the Apache License, Version 2.0 — see the [LICENSE](LICENSE) file for details.

© 2025 Eric Hermosis. All rights reserved.

---

## Contributing

Contributions are welcome! Please open issues or pull requests for bugs, features, or enhancements.

---
