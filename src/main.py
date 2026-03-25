import asyncio
from .mesh_node import MeshNode

async def main():
    node = MeshNode()
    await node.start_node()
    await node.join_network()
    await node.participate_in_consensus()

if __name__ == "__main__":
    asyncio.run(main())