import os
import cryptography
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

class MeshNode:
    def __init__(self, node_id):
        self.node_id = node_id
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        self.shared_keys = {}

    def establish_secure_connection(self, peer_node):
        if peer_node.node_id in self.shared_keys:
            return self.shared_keys[peer_node.node_id]

        # Generate shared secret using Diffie-Hellman key exchange
        shared_secret = self.private_key.exchange(cryptography.hazmat.primitives.asymmetric.dh.DHParameterNumbers(
            p=int(os.urandom(256).hex(), 16),
            g=2
        ).create_dh_parameters(backend=default_backend()).parameter_numbers(), peer_node.public_key)

        # Derive shared encryption key using HKDF
        shared_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'mesh_node_shared_key',
            backend=default_backend()
        ).derive(shared_secret)

        self.shared_keys[peer_node.node_id] = shared_key
        peer_node.shared_keys[self.node_id] = shared_key
        return shared_key

    def encrypt_message(self, peer_node, message):
        shared_key = self.establish_secure_connection(peer_node)
        # Encrypt message using shared key and appropriate cryptographic primitives
        encrypted_message = ...
        return encrypted_message

    def decrypt_message(self, peer_node, encrypted_message):
        shared_key = self.establish_secure_connection(peer_node)
        # Decrypt message using shared key and appropriate cryptographic primitives
        message = ...
        return message
