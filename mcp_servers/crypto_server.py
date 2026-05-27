#!/usr/bin/env python3
"""
MCP Crypto Server — demonstrates cryptographic operations: hashing, symmetric and
asymmetric encryption, digital signatures, JWT creation/verification, and secure
random generation.

Install: pip install mcp cryptography pyjwt
Configure in .claude/settings.json:
{
  "mcpServers": {
    "crypto": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/crypto_server.py"]
    }
  }
}
"""

import asyncio
import base64
import hashlib
import hmac
import json
import os
import secrets as rand
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import Tool, TextContent

server = Server("crypto")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@server.tool()
async def hash_text(text: str, algorithm: str = "sha256") -> list[TextContent]:
    """Hash text using various algorithms and return the digest.

    Args:
        text: Text to hash
        algorithm: "md5", "sha1", "sha256", "sha512", "blake2b", "blake2s",
                   "sha3_256", "sha3_512", "shake_128", "shake_256"
    """
    algos = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
        "blake2b": hashlib.blake2b,
        "blake2s": hashlib.blake2s,
        "sha3_256": hashlib.sha3_256,
        "sha3_512": hashlib.sha3_512,
    }

    if algorithm in algos:
        h = algos[algorithm](text.encode())
        digest = h.hexdigest()
        size = h.digest_size
    elif algorithm.startswith("shake"):
        bits = int(algorithm.split("_")[1])
        h = hashlib.shake_256(text.encode()) if algorithm == "shake_256" else hashlib.shake_128(text.encode())
        digest = h.hexdigest(bits // 8)
        size = bits // 8
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    return [TextContent(type="text", text=json.dumps({
        "algorithm": algorithm,
        "digest": digest,
        "digest_size_bytes": size,
        "input_length": len(text),
    }, indent=2))]

@server.tool()
async def hmac_sign(
    message: str,
    key: str = "",
    algorithm: str = "sha256",
) -> list[TextContent]:
    """Generate an HMAC (Hash-based Message Authentication Code).

    Args:
        message: Message to sign
        key: Secret key. If empty, a random key is generated for you.
        algorithm: "sha256", "sha512", "sha1", "md5"
    """
    if not key:
        key = rand.token_hex(32)

    algo_map = {"sha256": hashlib.sha256, "sha512": hashlib.sha512, "sha1": hashlib.sha1}
    digestmod = algo_map.get(algorithm, hashlib.sha256)

    mac = hmac.new(key.encode(), message.encode(), digestmod)

    return [TextContent(type="text", text=json.dumps({
        "hmac": mac.hexdigest(),
        "algorithm": f"HMAC-{algorithm.upper()}",
        "key": key,
        "key_length": len(key),
        "verification": f"hmac.compare_digest(hmac.new(key.encode(), message.encode(), '{algorithm}').digest(), bytes.fromhex('{mac.hexdigest()}'))",
    }, indent=2))]

@server.tool()
async def symmetric_encrypt(
    plaintext: str,
    key: str = "",
    algorithm: str = "fernet",
) -> list[TextContent]:
    """Encrypt text using symmetric encryption.

    Args:
        plaintext: Text to encrypt
        key: Encryption key (base64 for Fernet, hex for AES). Auto-generated if empty.
        algorithm: "fernet" (simple), "aes-gcm" (authenticated), "aes-cbc" (block), "chacha20"
    """
    result: dict[str, Any] = {"algorithm": algorithm}

    if algorithm == "fernet":
        from cryptography.fernet import Fernet
        if not key:
            key = Fernet.generate_key().decode()
        f = Fernet(key.encode()[:44])
        ciphertext = f.encrypt(plaintext.encode()).decode()
        result.update({
            "key": key,
            "ciphertext": ciphertext,
            "decrypt_with": f"Fernet(key).decrypt(ciphertext.encode()).decode()",
        })

    elif algorithm == "aes-gcm":
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        if not key:
            key = rand.token_hex(16)  # 128-bit, will be hashed to 256
        key_bytes = hashlib.sha256(key.encode()).digest()
        aesgcm = AESGCM(key_bytes)
        nonce = rand.token_bytes(12)
        ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
        result.update({
            "key": key,
            "nonce_hex": nonce.hex(),
            "ciphertext_b64": base64.b64encode(ct).decode(),
            "combined": base64.b64encode(nonce + ct).decode(),
        })

    elif algorithm == "chacha20":
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        if not key:
            key = rand.token_hex(32)
        key_bytes = bytes.fromhex(key) if len(key) == 64 else key.encode()[:32].ljust(32, b"\x00")
        nonce = rand.token_bytes(16)
        cipher = Cipher(algorithms.ChaCha20(key_bytes, nonce), mode=None)
        encryptor = cipher.encryptor()
        ct = encryptor.update(plaintext.encode())
        result.update({
            "key": key,
            "nonce_hex": nonce.hex(),
            "ciphertext_b64": base64.b64encode(ct).decode(),
        })

    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def symmetric_decrypt(
    ciphertext: str,
    key: str,
    algorithm: str = "fernet",
    nonce: str = "",
) -> list[TextContent]:
    """Decrypt text that was encrypted with symmetric encryption.

    Args:
        ciphertext: The encrypted data
        key: The encryption key used
        algorithm: Same algorithm used for encryption
        nonce: Nonce/IV (hex), required for AES-GCM and ChaCha20
    """
    result: dict[str, Any] = {"algorithm": algorithm}

    try:
        if algorithm == "fernet":
            from cryptography.fernet import Fernet, InvalidToken
            f = Fernet(key.encode()[:44])
            try:
                plaintext = f.decrypt(ciphertext.encode()).decode()
            except InvalidToken:
                return [TextContent(type="text",
                    text=json.dumps({"error": "Invalid key or corrupted data"}, indent=2))]
            result["plaintext"] = plaintext

        elif algorithm == "aes-gcm":
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            key_bytes = hashlib.sha256(key.encode()).digest()
            aesgcm = AESGCM(key_bytes)
            combined = base64.b64decode(ciphertext)
            n = bytes.fromhex(nonce) if nonce else combined[:12]
            ct = combined[12:] if not nonce else combined
            plaintext = aesgcm.decrypt(n, ct, None).decode()
            result["plaintext"] = plaintext

        elif algorithm == "chacha20":
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            key_bytes = bytes.fromhex(key) if len(key) == 64 else key.encode()[:32].ljust(32, b"\x00")
            n = bytes.fromhex(nonce)
            ct = base64.b64decode(ciphertext)
            cipher = Cipher(algorithms.ChaCha20(key_bytes, n), mode=None)
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ct).decode()
            result["plaintext"] = plaintext

    except Exception as e:
        return [TextContent(type="text",
            text=json.dumps({"error": f"Decryption failed: {e}"}, indent=2))]

    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def asymmetric_keygen(
    key_type: str = "rsa",
    key_size: int = 2048,
) -> list[TextContent]:
    """Generate an asymmetric key pair (RSA or Ed25519).

    Args:
        key_type: "rsa" or "ed25519"
        key_size: Key size in bits (for RSA: 2048 or 4096)
    """
    from cryptography.hazmat.primitives.asymmetric import rsa, ed25519
    from cryptography.hazmat.primitives import serialization

    result: dict[str, Any] = {"type": key_type}

    if key_type == "rsa":
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
        public_key = private_key.public_key()

        result["private_key_pem"] = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
        result["public_key_pem"] = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
        result["key_size"] = key_size

    elif key_type == "ed25519":
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        result["private_key_pem"] = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
        result["public_key_pem"] = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def sign_verify(
    message: str,
    action: str = "sign",
    private_key_pem: str = "",
    signature_b64: str = "",
    public_key_pem: str = "",
    algorithm: str = "rsa-sha256",
) -> list[TextContent]:
    """Digitally sign a message or verify a signature.

    Args:
        message: Message to sign or verify
        action: "sign" or "verify"
        private_key_pem: PEM-encoded private key (for signing)
        signature_b64: Base64-encoded signature (for verification)
        public_key_pem: PEM-encoded public key (for verification)
        algorithm: "rsa-sha256", "rsa-sha512", "ed25519"
    """
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, ed25519, utils
    from cryptography.exceptions import InvalidSignature

    result: dict[str, Any] = {}

    if action == "sign":
        if not private_key_pem:
            return [TextContent(type="text",
                text=json.dumps({"error": "private_key_pem is required for signing"}, indent=2))]

        private_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)

        if algorithm.startswith("rsa"):
            hash_alg = hashes.SHA256() if "sha256" in algorithm else hashes.SHA512()
            signature = private_key.sign(message.encode(), padding.PKCS1v15(), hash_alg)
        elif algorithm == "ed25519":
            signature = private_key.sign(message.encode())

        result["signature_b64"] = base64.b64encode(signature).decode()
        result["message"] = message
        result["algorithm"] = algorithm

    elif action == "verify":
        if not public_key_pem or not signature_b64:
            return [TextContent(type="text",
                text=json.dumps({"error": "public_key_pem and signature_b64 are required"}, indent=2))]

        public_key = serialization.load_pem_public_key(public_key_pem.encode())
        signature = base64.b64decode(signature_b64)

        try:
            if algorithm.startswith("rsa"):
                hash_alg = hashes.SHA256() if "sha256" in algorithm else hashes.SHA512()
                public_key.verify(signature, message.encode(), padding.PKCS1v15(), hash_alg)
            elif algorithm == "ed25519":
                public_key.verify(signature, message.encode())
            result["valid"] = True
        except InvalidSignature:
            result["valid"] = False

    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def jwt_token(
    action: str = "create",
    payload_json: str = "{}",
    secret: str = "",
    algorithm: str = "HS256",
    token: str = "",
) -> list[TextContent]:
    """Create or verify a JWT (JSON Web Token).

    Args:
        action: "create" or "verify"
        payload_json: JSON payload for the token (e.g. '{"sub": "user123", "role": "admin"}')
        secret: Secret key for HMAC algorithms (HS256, HS384, HS512)
        algorithm: "HS256", "HS384", "HS512", "RS256", "ES256"
        token: JWT string to verify (for verify action)
    """
    result: dict[str, Any] = {}

    if action == "create":
        if not secret:
            secret = rand.token_hex(32)

        payload = json.loads(payload_json)
        payload.setdefault("iat", int(time.time()))
        payload.setdefault("exp", int(time.time()) + 3600)  # 1 hour
        payload.setdefault("jti", rand.token_hex(8))

        # Manual JWT creation for HMAC algorithms
        header = {"alg": algorithm, "typ": "JWT"}
        header_b64 = _b64url_encode(json.dumps(header).encode())
        payload_b64 = _b64url_encode(json.dumps(payload).encode())
        signing_input = f"{header_b64}.{payload_b64}"

        hash_alg = algorithm.replace("HS", "sha")
        sig = hmac.new(secret.encode(), signing_input.encode(), hash_alg).digest()
        sig_b64 = _b64url_encode(sig)

        token_str = f"{signing_input}.{sig_b64}"

        result["token"] = token_str
        result["payload"] = payload
        result["secret"] = secret
        result["algorithm"] = algorithm

    elif action == "verify":
        parts = token.split(".")
        if len(parts) != 3:
            return [TextContent(type="text",
                text=json.dumps({"error": "Invalid JWT format"}, indent=2))]

        header_b64, payload_b64, sig_b64 = parts
        try:
            header = json.loads(_b64url_decode(header_b64))
            payload = json.loads(_b64url_decode(payload_b64))
        except Exception:
            return [TextContent(type="text",
                text=json.dumps({"error": "Invalid JWT encoding"}, indent=2))]

        if not secret:
            return [TextContent(type="text",
                text=json.dumps({"error": "Secret is required for HS256/HS384/HS512 verification"}, indent=2))]

        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}"
        hash_alg = header.get("alg", "HS256").replace("HS", "sha")
        expected_sig = _b64url_encode(
            hmac.new(secret.encode(), signing_input.encode(), hash_alg).digest()
        )

        valid = hmac.compare_digest(sig_b64, expected_sig)

        result["valid"] = valid
        result["payload"] = payload
        result["header"] = header
        if not valid and "exp" in payload:
            exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            if datetime.now(timezone.utc) > exp_time:
                result["reason"] = "Token expired"

    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

@server.tool()
async def random_bytes(length: int = 32, encoding: str = "hex") -> list[TextContent]:
    """Generate cryptographically secure random bytes.

    Args:
        length: Number of bytes (1-1024)
        encoding: Output encoding — "hex", "base64", "urlsafe_base64", "decimal"
    """
    length = min(length, 1024)
    data = rand.token_bytes(length)

    output: dict[str, Any] = {"length": length, "encoding": encoding}
    if encoding == "hex":
        output["value"] = data.hex()
    elif encoding == "base64":
        output["value"] = base64.b64encode(data).decode()
    elif encoding == "urlsafe_base64":
        output["value"] = base64.urlsafe_b64encode(data).decode()
    elif encoding == "decimal":
        output["value"] = str(int.from_bytes(data, "big"))[:100]

    return [TextContent(type="text", text=json.dumps(output, indent=2))]

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@server.resource("crypto://algorithms")
async def list_algorithms() -> str:
    return json.dumps({
        "hash": ["md5", "sha1", "sha256", "sha512", "blake2b", "blake2s", "sha3_256", "sha3_512", "shake_128", "shake_256"],
        "symmetric": ["fernet", "aes-gcm", "aes-cbc", "chacha20"],
        "asymmetric": ["rsa", "ed25519"],
        "hmac": ["HMAC-SHA256", "HMAC-SHA512"],
        "jwt": ["HS256", "HS384", "HS512", "RS256"],
    }, indent=2)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@server.prompt(
    name="security-checklist",
    description="Generate a cryptographic security checklist for an application",
    arguments={
        "app_type": {
            "type": "string",
            "enum": ["web_api", "mobile", "cli", "microservice", "data_pipeline"],
            "description": "Type of application to secure",
            "required": True,
        },
    },
)
async def security_checklist_prompt(app_type: str) -> dict:
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""Generate a cryptographic security checklist for a {app_type} application.

Use the crypto tools to demonstrate each item:
1. Use hash_text to show how to hash sensitive data (pick appropriate algorithm)
2. Use generate_key to create keys for different purposes (which key type for which use case?)
3. Use symmetric_encrypt to show how to encrypt data at rest
4. Use asymmetric_keygen to generate keys for TLS/mTLS
5. Use hmac_sign to show API request signing
6. Use jwt_token to create authentication tokens
7. Use generate_password to set password policies

For each checklist item:
- What to do
- Which tool/algorithm to use
- Example call with real parameters
- Why this matters for {app_type}

End with a "quick start" section: the minimum 3 things to implement first.""",
            },
        }],
    }

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

async def main():
    transport = StdioServerTransport()
    await server.run(transport)

if __name__ == "__main__":
    asyncio.run(main())
