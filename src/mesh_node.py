import asyncio
import json
from typing import Dict, Set, Optional
from dataclasses import dataclass
from datetime import datetime
import socket
import random

@dataclass
class NodeInfo:
    node_id: str
    last_seen: datetime
    address: str
    port: int
    status: str

class MeshNode:
    def __init__(self, port: int = 5000):
        self.node_id = hex(random.getrandbits(128))[2:]
        self.port = port
        self.peers: Dict[str, NodeInfo] = {}
        self.active = False
        self._heartbeat_interval = 30
    
    async def start(self):
        self.active = True
        self.server = await asyncio.start_server(
            self._handle_connection, '0.0.0.0', self.port
        )
        await asyncio.gather(
            self._discovery_broadcast(),
            self._maintain_mesh(),
            self._prune_dead_nodes()
        )

    async def stop(self):
        self.active = False
        if hasattr(self, 'server'):
            self.server.close()
            await self.server.wait_closed()

    async def _handle_connection(self, reader, writer):
        data = await reader.read(4096)
        message = json.loads(data.decode())
        
        if message['type'] == 'discovery':
            await self._handle_discovery(message, writer)
        elif message['type'] == 'heartbeat':
            await self._handle_heartbeat(message)

        writer.close()
        await writer.wait_closed()

    async def _handle_discovery(self, message: dict, writer):
        peer_info = NodeInfo(
            node_id=message['node_id'],
            last_seen=datetime.now(),
            address=message['address'],
            port=message['port'],
            status='active'
        )
        self.peers[peer_info.node_id] = peer_info
        
        # Send back our peer list
        response = {
            'type': 'discovery_response',
            'peers': [
                {
                    'node_id': p.node_id,
                    'address': p.address,
                    'port': p.port
                } for p in self.peers.values()
            ]
        }
        writer.write(json.dumps(response).encode())
        await writer.drain()

    async def _handle_heartbeat(self, message: dict):
        if message['node_id'] in self.peers:
            self.peers[message['node_id']].last_seen = datetime.now()
            self.peers[message['node_id']].status = 'active'

    async def _discovery_broadcast(self):
        while self.active:
            message = {
                'type': 'discovery',
                'node_id': self.node_id,
                'address': socket.gethostbyname(socket.gethostname()),
                'port': self.port
            }
            
            # Broadcast to known peers
            for peer in list(self.peers.values()):
                try:
                    reader, writer = await asyncio.open_connection(
                        peer.address, peer.port
                    )
                    writer.write(json.dumps(message).encode())
                    await writer.drain()
                    writer.close()
                    await writer.wait_closed()
                except:
                    peer.status = 'unreachable'
            
            await asyncio.sleep(self._heartbeat_interval)

    async def _maintain_mesh(self):
        while self.active:
            for peer in list(self.peers.values()):
                if peer.status == 'unreachable':
                    try:
                        # Attempt to reconnect
                        reader, writer = await asyncio.open_connection(
                            peer.address, peer.port
                        )
                        peer.status = 'active'
                        peer.last_seen = datetime.now()
                        writer.close()
                        await writer.wait_closed()
                    except:
                        pass
            await asyncio.sleep(self._heartbeat_interval)

    async def _prune_dead_nodes(self):
        while self.active:
            now = datetime.now()
            dead_nodes = [
                node_id for node_id, info in self.peers.items()
                if (now - info.last_seen).seconds > self._heartbeat_interval * 3
            ]
            for node_id in dead_nodes:
                del self.peers[node_id]
            await asyncio.sleep(self._heartbeat_interval)

    def get_active_peers(self) -> Set[str]:
        return {p.node_id for p in self.peers.values() if p.status == 'active'}

    async def broadcast_message(self, message: dict):
        for peer in list(self.peers.values()):
            if peer.status == 'active':
                try:
                    reader, writer = await asyncio.open_connection(
                        peer.address, peer.port
                    )
                    writer.write(json.dumps(message).encode())
                    await writer.drain()
                    writer.close()
                    await writer.wait_closed()
                except:
                    peer.status = 'unreachable'
