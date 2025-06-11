from pytest import mark
from asyncio import sleep
from unittest.mock import AsyncMock
from pydepends.depends import inject, Depends, Provider 

provider = Provider()
 
async def left_leaf_dependency():
    await sleep(0.01)
    return 2
    
async def right_leaf_dependency():
    await sleep(0.01)
    return 3
 
async def right_node_dependency(leaf = Depends(right_leaf_dependency)):
    await sleep(0.01)
    return leaf * 5

async def root_dependency(
    left = Depends(left_leaf_dependency), 
    right = Depends(right_node_dependency)
):
    await sleep(0.01)
    return left * right * 7
 
@inject(provider)
async def handle_dependency(root = Depends(root_dependency)):
    await sleep(0.01)
    return root * 11

async def test_handle_nested_async_depends():
    value = await handle_dependency()
    assert value == 2 * 3 * 5 * 7 * 11

    # Test dependency override
    provider.dependency_overrides[right_node_dependency] = lambda: 13
    value = await handle_dependency()
    assert value == 2 * 7 * 11 * 13





    
 
open_mock = AsyncMock()
close_mock = AsyncMock()

async def async_generator_dependency():
    await open_mock()
    try:
        yield 42
    finally:
        await close_mock()

@inject(provider)
async def async_generator_function(dependency = Depends(async_generator_dependency)):
    return dependency

@mark.asyncio
async def test_async_generator_dependency():
    result = await async_generator_function()
    assert result == 42
    open_mock.assert_awaited_once()
    close_mock.assert_awaited_once()
 
override_open_mock = AsyncMock()
override_close_mock = AsyncMock()

async def override_async_generator():
    await override_open_mock()
    try:
        yield 43
    finally:
        await override_close_mock()

@mark.asyncio
async def test_async_dependency_override():
    provider.dependency_overrides[async_generator_dependency] = override_async_generator
    result = await async_generator_function()
    assert result == 43
    override_open_mock.assert_awaited_once()
    override_close_mock.assert_awaited_once()