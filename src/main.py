import os
import asyncio
import logging
from .agent import Agent
from .swarm import Swarm
from .blockchain import BlockchainManager

# Core logic for the Decentralized Coordination Mesh
async def main():
    # Initialize the blockchain manager
    blockchain_manager = BlockchainManager()
    await blockchain_manager.start()

    # Spawn the agent swarm
    swarm = Swarm()
    await swarm.deploy_agents()

    # Coordinate the swarm activities
    await swarm.coordinate()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
