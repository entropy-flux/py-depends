from pydepends.depends import inject, Depends
from pydepends.depends import Provider, Dependency

provider = Provider()

def left_leaf_dependency() -> int:
    return 2
    
async def right_leaf_dependency() -> int:
    return 3

async def right_node_dependency(leaf: int = Depends(right_leaf_dependency)) -> int:
    return leaf*5

async def root_dependency(left: int = Depends(left_leaf_dependency), right: int = Depends(right_node_dependency)):
    return left*right*7

@inject(provider)
def sync_handle_dependency(root: int = Depends(root_dependency)):
    return root*11

@inject(provider)
async def async_handle_dependency(root: int = Dependency(root_dependency)):
    return root*11

async def main():
    value = await async_handle_dependency()
    assert value == 2*3*5*7*11 
    print(f"Computed value: {value}")  # Output: Computed value: 2310


import asyncio
asyncio.run(main())