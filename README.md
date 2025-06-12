# PyDepends

A lightweight Python dependency injection library designed to simplify managing dependencies in synchronous and asynchronous code using decorators and type-safe wrappers. 

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

Here’s a simple example showing how to define dependencies as a dependency tree:

``` python
from pydepends.depends import inject, Depends 
 
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
from pydepends.depends import Provider
 
provider = Provider()

@inject(provider)
def handle_dependency(root: int = Depends(root_dependency)) -> int:
    return root * 11
 
value = handle_dependency()

assert value == 2 * 3 * 5 * 7 * 11
print(f"Computed value: {value}")  # Output: Computed value: 2310
```

Or inject them in an async function. Sync dependencies are put into an asyncio thread to avoid blocking
the event loop. 

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

License

This project is licensed under the Apache License 2.0 — see the LICENSE file for details.
Contributing

Contributions, issues, and feature requests are welcome! Feel free to check issues page or submit a pull request.
