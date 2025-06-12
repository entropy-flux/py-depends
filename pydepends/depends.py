# Copyright 2025 Eric Cardozo
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You can obtain a copy of the License at:
# 
#     http://www.apache.org/licenses/LICENSE-2.0
#
# This software is distributed "AS IS," without warranties or conditions.
# See the License for specific terms.  
 
from asyncio import run, to_thread
from contextlib import ExitStack, AsyncExitStack
from contextlib import contextmanager, asynccontextmanager
from functools import wraps
from typing import Generator, AsyncGenerator, Generic, TypeVar
from collections.abc import Callable
from inspect import BoundArguments
from inspect import signature, iscoroutinefunction, isasyncgenfunction

 

class Provider:
    """Manages dependency overrides for dependency injection.

    Attributes:
        dependency_overrides (dict): A mapping of original dependencies to their overrides.
    """

    def __init__(self):
        """Initializes an empty dictionary for dependency overrides."""
        self.dependency_overrides = dict()
    
    def override(self, dependency: Callable, override: Callable):
        """Overrides a given dependency with a new callable.

        Args:
            dependency (Callable): The original dependency to override.
            override (Callable): The new callable to use instead of the original.
        """
        self.dependency_overrides[dependency] = override


T = TypeVar('T')
class Dependency(Generic[T]):
    """Represents a dependency wrapping a callable that returns a value of type T.

    Attributes:
        callable (Callable[..., T]): The callable that provides the dependency.
    """

    def __init__(self, callable: Callable[..., T]) -> None:
        """Initializes the dependency with the provided callable.

        Args:
            callable (Callable[..., T]): The callable to wrap as a dependency.
        """
        self.callable: Callable[..., T] = callable


def Depends(callable: Callable):
    """Creates a Dependency instance wrapping the given callable.

    Args:
        callable (Callable): The callable to wrap as a dependency.

    Returns:
        Dependency: An instance of Dependency wrapping the callable.
    """
    return Dependency(callable)


# ---------- Context Managers ----------

@contextmanager
def _managed_dependency(generator: Generator):
    try:
        value = next(generator)
        yield value
    finally:
        try:
            next(generator, None)
        except StopIteration:
            pass

@asynccontextmanager
async def _async_managed_dependency(generator: AsyncGenerator):
    try:
        value = await generator.__anext__()
        yield value
    finally:
        try:
            await generator.aclose()
        except StopAsyncIteration:
            pass
        except RuntimeError as e:
            if "cannot reuse already awaited" not in str(e):
                raise

# ---------- Utility ----------

def _get_overridden_callable(callable: Callable, provider: Provider) -> Callable:
    return provider.dependency_overrides.get(callable, callable)

# ---------- Sync Resolution ----------

def _resolve_sync_dependency(dependency: Callable, provider: Provider, exit_stack: ExitStack):
    dep_args, dep_stack = sync_resolve(dependency, provider)
    with dep_stack:
        instance = dependency(*dep_args.args, **dep_args.kwargs)
        if isinstance(instance, Generator):
            return exit_stack.enter_context(_managed_dependency(instance))
        return instance

def _handle_async_dependency_sync(dependency: Callable, provider: Provider):
    return run(_resolve_async_dependency(dependency, provider))

def sync_resolve(function: Callable, provider: Provider, *args, **kwargs):
    parameters = signature(function).parameters
    bounded = signature(function).bind_partial(*args, **kwargs)
    exit_stack = ExitStack()

    for name, parameter in parameters.items():
        if name in bounded.arguments or not isinstance(parameter.default, Dependency):
            continue

        dependency = _get_overridden_callable(parameter.default.callable, provider)

        if iscoroutinefunction(dependency) or isasyncgenfunction(dependency):
            bounded.arguments[name] = _handle_async_dependency_sync(dependency, provider)
        else:
            bounded.arguments[name] = _resolve_sync_dependency(dependency, provider, exit_stack)

    return bounded, exit_stack

# ---------- Async Resolution ----------

async def _resolve_async_dependency(dependency: Callable, provider: Provider):
    if isasyncgenfunction(dependency):
        async with _async_managed_dependency(dependency()) as value:
            return value
    else:
        dep_args, dep_stack = await async_resolve(dependency, provider)
        async with dep_stack:
            return await dependency(*dep_args.args, **dep_args.kwargs)

async def _resolve_async_bound_dependency(dependency: Callable, provider: Provider, name: str, bounded: BoundArguments, exit_stack: AsyncExitStack):
    dep_args, dep_stack = await async_resolve(dependency, provider)
    async with dep_stack:
        if isasyncgenfunction(dependency):
            gen = dependency(*dep_args.args, **dep_args.kwargs)
            bounded.arguments[name] = await exit_stack.enter_async_context(_async_managed_dependency(gen))
        else:
            bounded.arguments[name] = await dependency(*dep_args.args, **dep_args.kwargs)

async def _resolve_sync_bound_dependency(dependency: Callable, provider: Provider, name: str, bounded: BoundArguments, exit_stack: AsyncExitStack):
    dep_args, dep_stack = sync_resolve(dependency, provider)
    with dep_stack:
        instance = await to_thread(dependency, *dep_args.args, **dep_args.kwargs)
        if isinstance(instance, Generator):
            context = _managed_dependency(instance)
            bounded.arguments[name] = exit_stack.enter_context(context)
        else:
            bounded.arguments[name] = instance

async def async_resolve(function: Callable, provider: Provider, *args, **kwargs):
    parameters = signature(function).parameters
    bounded = signature(function).bind_partial(*args, **kwargs)
    exit_stack = AsyncExitStack()

    for name, parameter in parameters.items():
        if name in bounded.arguments or not isinstance(parameter.default, Dependency):
            continue

        dependency = _get_overridden_callable(parameter.default.callable, provider)

        if iscoroutinefunction(dependency) or isasyncgenfunction(dependency):
            await _resolve_async_bound_dependency(dependency, provider, name, bounded, exit_stack)
        else:
            await _resolve_sync_bound_dependency(dependency, provider, name, bounded, exit_stack)

    return bounded, exit_stack
 


def inject(provider: Provider):    
    """Decorator to inject dependencies into a function based on a provider.

    This decorator supports both synchronous and asynchronous functions.
    It resolves dependencies using the provided `provider`, manages
    the context with an exit stack, and calls the original function
    with the injected arguments.

    Args:
        provider (Provider): An instance responsible for providing dependencies.

    Returns:
        Callable: A decorator that wraps the target function, injecting dependencies.

    Examples:
        ```python
        @inject(my_provider)
        def my_function(dep1, dep2):
            ...
        ```
    """
    def decorator(function: Callable):
        if iscoroutinefunction(function) or isasyncgenfunction(function):
            @wraps(function)
            async def async_wrapper(*args, **kwargs):
                bounded, exit_stack = await async_resolve(function, provider, *args, **kwargs)
                async with exit_stack:
                    return await function(*bounded.args, **bounded.kwargs)
            return async_wrapper

        else:
            @wraps(function)
            def sync_wrapper(*args, **kwargs):
                bounded, exit_stack = sync_resolve(function, provider, *args, **kwargs)
                with exit_stack:
                    return function(*bounded.args, **bounded.kwargs)
            return sync_wrapper
    return decorator