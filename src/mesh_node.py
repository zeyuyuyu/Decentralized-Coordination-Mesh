import asyncio
from dataclasses import dataclass
from typing import Dict, Set, Any, Optional, Callable
import json
import logging

@dataclass
class PeerInfo:
    id: str
    address: str
    port: int
    last_seen: float

class MeshNode:
    def __init__(self, node_id: str, port: int):
        self.node_id = node_id
        self.port = port
        self.peers: Dict[str, PeerInfo] = {}
        self.topics: Dict[str, Set[Callable]] = {}
        self.logger = logging.getLogger('mesh_node')

    async def start(self):
        """Start the mesh node server"""
        self.server = await asyncio.start_server(
            self._handle_connection, '0.0.0.0', self.port)
        self.logger.info(f'Node {self.node_id} listening on port {self.port}')

    async def _handle_connection(self, reader: asyncio.StreamReader, 
                               writer: asyncio.StreamWriter):
        """Handle incoming peer connections"""
        try:
            data = await reader.read(1024)
            msg = json.loads(data.decode())
            
            if msg['type'] == 'discovery':
                await self._handle_discovery(msg, writer)
            elif msg['type'] == 'publish':
                await self._handle_publish(msg)

        except Exception as e:
            self.logger.error(f'Error handling connection: {e}')
        finally:
            writer.close()
            await writer.wait_closed()

    async def _handle_discovery(self, msg: Dict, writer: asyncio.StreamWriter):
        """Handle peer discovery messages"""
        peer_id = msg['node_id']
        self.peers[peer_id] = PeerInfo(
            id=peer_id,
            address=msg['address'],
            port=msg['port'],
            last_seen=asyncio.get_event_loop().time()
        )
        response = {
            'type': 'discovery_ack',
            'node_id': self.node_id,
            'peers': [
                {'id': p.id, 'address': p.address, 'port': p.port}
                for p in self.peers.values()
            ]
        }
        writer.write(json.dumps(response).encode())
        await writer.drain()

    async def _handle_publish(self, msg: Dict):
        """Handle incoming published messages"""
        topic = msg['topic']
        if topic in self.topics:
            for callback in self.topics[topic]:
                try:
                    await callback(msg['data'])
                except Exception as e:
                    self.logger.error(f'Error in subscriber callback: {e}')

    async def publish(self, topic: str, data: Any):
        """Publish data to a topic"""
        msg = {
            'type': 'publish',
            'topic': topic,
            'data': data,
            'origin': self.node_id
        }
        
        # Publish to local subscribers
        await self._handle_publish(msg)
        
        # Forward to peers
        for peer in self.peers.values():
            try:
                reader, writer = await asyncio.open_connection(
                    peer.address, peer.port)
                writer.write(json.dumps(msg).encode())
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                self.logger.error(f'Failed to forward to peer {peer.id}: {e}')

    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a topic with a callback"""
        if topic not in self.topics:
            self.topics[topic] = set()
        self.topics[topic].add(callback)

    def unsubscribe(self, topic: str, callback: Callable):
        """Unsubscribe from a topic"""
        if topic in self.topics and callback in self.topics[topic]:
            self.topics[topic].remove(callback)
            if not self.topics[topic]:
                del self.topics[topic]
