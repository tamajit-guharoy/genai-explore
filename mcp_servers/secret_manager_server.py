#!/usr/bin/env python3
"""
MCP Secret Manager Server — demonstrates encryption, secure credential storage,
key generation, password hashing, TOTP generation, and JWT handling.

Install: pip install mcp cryptography pyjwt
Configure in .claude/settings.json:
{
  "mcpServers": {
    "secrets": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/secret_manager_server.py"],
      "env": {
        "SECRETS_MASTER_KEY": "your-fernet-key-here",
        "SECRETS_VAULT_PATH": "./.vault.json"
      }
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import Tool, TextContent

server = Server("secrets")

# ---------------------------------------------------------------------------
# Vault setup
# ---------------------------------------------------------------------------
VAULT_PATH = Path(os.environ.get("SECRETS_VAULT_PATH", ".vault.json"))

def _load_vault() -> dict:
    if VAULT_PATH.exists():
        try:
            from cryptography.fernet import Fernet
            master_key = os.environ.get("SECRETS_MASTER_KEY", "")
            if master_key:
                f = Fernet(master_key.encode() if len(master_key) < 50 else master_key.encode()[:44])
                decrypted = f.decrypt(VAULT_PATH.read_bytes())
                return json.loads(decrypted)
        except Exception:
            pass  # Fall through to empty vault
    return {"secrets": {}, "version": 1}

def _save_vault(vault: dict) -> None:
    from cryptography.fernet import Fernet
    master_key = os.environ.get("SECRETS_MASTER_KEY", "")
    if not master_key:
        # Generate one if not set
        master_key = base64.urlsafe_b64encode(hashlib.sha256(b"mcp-secrets-default").digest()).decode()
    f = Fernet(master_key.encode()[:44])
    VAULT_PATH.write_bytes(f.encrypt(json.dumps(vault, indent=2).encode()))

_vault = _load_vault()

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@server.tool()
async def generate_password(length: int = 20, include_special: bool = True) -> list[TextContent]:
    """Generate a cryptographically secure random password.

    Args:
        length: Password length (8-128). Defaults to 20.
        include_special: Include special characters. Defaults to True.
    """
    if length < 8:
        length = 8
    if length > 128:
        length = 128

    import string
    alphabet = string.ascii_letters + string.digits
    if include_special:
        alphabet += "!@#$%^&*()-_=+[]{}|;:,.<>?/"

    # Ensure at least one of each type
    password = [
        rand.choice(string.ascii_lowercase),
        rand.choice(string.ascii_uppercase),
        rand.choice(string.digits),
        rand.choice("!@#$%^&*") if include_special else rand.choice(string.ascii_letters),
    ]
    password += [rand.choice(alphabet) for _ in range(length - len(password))]
    rand.SystemRandom().shuffle(password)
    pwd = "".join(password)

    # Estimate strength
    entropy = len(pwd) * (len(set(alphabet))).bit_length()
    strength = "weak" if entropy < 60 else "moderate" if entropy < 80 else "strong" if entropy < 100 else "very strong"

    return [TextContent(type="text", text=json.dumps({
        "password": pwd,
        "length": len(pwd),
        "entropy_bits": entropy,
        "strength": strength,
    }, indent=2))]

@server.tool()
async def hash_password(password: str, algorithm: str = "bcrypt") -> list[TextContent]:
    """Hash a password using a secure algorithm.

    Args:
        password: The password to hash
        algorithm: "bcrypt", "sha256", or "pbkdf2"
    """
    result: dict[str, Any] = {"algorithm": algorithm}

    if algorithm == "bcrypt":
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode(), salt).decode()
        result["hash"] = hashed
        result["verify_command"] = f"bcrypt.checkpw(password.encode(), '{hashed}'.encode())"
    elif algorithm == "sha256":
        salt = rand.token_hex(16)
        hashed = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
        result["hash"] = f"sha256:{salt}:{hashed}"
        result["verify_command"] = "Re-hash and compare"
    elif algorithm == "pbkdf2":
        import hashlib as hl
        salt = rand.token_bytes(16)
        hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        result["hash"] = f"pbkdf2:{base64.b64encode(salt).decode()}:{base64.b64encode(hashed).decode()}"

    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def generate_key(key_type: str = "fernet", key_size: int = 256) -> list[TextContent]:
    """Generate cryptographic keys.

    Args:
        key_type: "fernet" (Fernet symmetric), "aes" (AES key), "rsa" (RSA keypair text),
                  "hmac" (HMAC key), "api-key" (random API key)
        key_size: Key size in bits (for AES/RSA)
    """
    result: dict[str, Any] = {"type": key_type}

    if key_type == "fernet":
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        result["key"] = key
        result["usage"] = "from cryptography.fernet import Fernet; f = Fernet(key)"
    elif key_type == "aes":
        key = rand.token_bytes(key_size // 8)
        result["key_hex"] = key.hex()
        result["key_b64"] = base64.b64encode(key).decode()
        result["size_bits"] = key_size
    elif key_type == "rsa":
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
        result["private_key_pem"] = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
        result["public_key_pem"] = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
    elif key_type == "hmac":
        key = rand.token_hex(32)
        result["key"] = key
        result["usage"] = f'hmac.new(key.encode(), msg.encode(), "sha256").hexdigest()'
    elif key_type == "api-key":
        key = f"sk-{rand.token_hex(24)}"
        result["key"] = key

    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def vault_store(key: str, value: str, metadata: str = "{}") -> list[TextContent]:
    """Securely store a secret in the encrypted vault.

    Args:
        key: Name/key for the secret
        value: The secret value to store
        metadata: JSON object with optional metadata (tags, description, etc.)
    """
    _vault["secrets"][key] = {
        "value": value,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "metadata": json.loads(metadata) if metadata else {},
    }
    _save_vault(_vault)
    return [TextContent(type="text",
        text=json.dumps({"stored": key, "message": f"Secret '{key}' stored securely"}, indent=2))]

@server.tool()
async def vault_get(key: str) -> list[TextContent]:
    """Retrieve a secret from the encrypted vault.

    Args:
        key: The secret name/key to retrieve
    """
    entry = _vault.get("secrets", {}).get(key)
    if not entry:
        return [TextContent(type="text",
            text=json.dumps({"error": f"Secret not found: {key}"}, indent=2))]
    return [TextContent(type="text", text=json.dumps({
        "key": key,
        "value": entry["value"],
        "metadata": entry.get("metadata", {}),
        "created_at": entry.get("created_at"),
    }, indent=2))]

@server.tool()
async def vault_list() -> list[TextContent]:
    """List all stored secret keys (values hidden)."""
    keys = []
    for k, v in _vault.get("secrets", {}).items():
        keys.append({
            "key": k,
            "created_at": v.get("created_at"),
            "metadata": v.get("metadata", {}),
            "value_length": len(v.get("value", "")),
        })
    return [TextContent(type="text", text=json.dumps(keys, indent=2))]

@server.tool()
async def vault_delete(key: str) -> list[TextContent]:
    """Delete a secret from the vault.

    Args:
        key: The secret key to delete
    """
    if key in _vault.get("secrets", {}):
        del _vault["secrets"][key]
        _save_vault(_vault)
        return [TextContent(type="text",
            text=json.dumps({"deleted": key}, indent=2))]
    return [TextContent(type="text",
        text=json.dumps({"error": f"Secret not found: {key}"}, indent=2))]

@server.tool()
async def generate_totp(secret: str = "", label: str = "app") -> list[TextContent]:
    """Generate a TOTP (Time-based One-Time Password) code and optionally a new secret.

    Args:
        secret: Base32-encoded TOTP secret. Leave empty to generate a new one.
        label: Label for the generated secret (e.g. "myapp:user@example.com")
    """
    import base64 as b64

    if not secret:
        # Generate new TOTP secret
        secret_bytes = rand.token_bytes(20)
        secret = base64.b32encode(secret_bytes).decode().rstrip("=")

    # Generate current TOTP code
    # RFC 6238 TOTP implementation
    def _totp(secret_b32: str, interval: int = 30, digits: int = 6) -> str:
        # Decode base32 secret (add padding)
        padding = 8 - len(secret_b32) % 8
        if padding != 8:
            secret_b32 += "=" * padding
        key = base64.b32decode(secret_b32.upper())

        counter = int(time.time() // interval)
        counter_bytes = counter.to_bytes(8, "big")
        hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()
        offset = hmac_hash[-1] & 0x0F
        code = (int.from_bytes(hmac_hash[offset:offset + 4], "big") & 0x7FFFFFFF) % (10 ** digits)
        return str(code).zfill(digits)

    code = _totp(secret)
    remaining = 30 - (int(time.time()) % 30)

    otpauth_url = f"otpauth://totp/{label}?secret={secret}&issuer=MCP+Secret+Manager"

    return [TextContent(type="text", text=json.dumps({
        "secret_base32": secret,
        "current_code": code,
        "valid_for_seconds": remaining,
        "otpauth_url": otpauth_url,
        "setup_instruction": f"Add to authenticator app: {otpauth_url}",
    }, indent=2))]

@server.tool()
async def encrypt_decrypt(
    text: str,
    action: str = "encrypt",
    key: str = "",
    algorithm: str = "fernet",
) -> list[TextContent]:
    """Encrypt or decrypt text using symmetric encryption.

    Args:
        text: Text to encrypt or decrypt
        action: "encrypt" or "decrypt"
        key: Encryption key (base64 for fernet, hex for AES). Leave empty to use master key.
        algorithm: "fernet" or "aes-gcm"
    """
    if not key:
        key = os.environ.get("SECRETS_MASTER_KEY", base64.urlsafe_b64encode(b"default-key-32b").decode())

    if algorithm == "fernet":
        from cryptography.fernet import Fernet
        try:
            f = Fernet(key.encode()[:44])
            if action == "encrypt":
                result = f.encrypt(text.encode()).decode()
            else:
                result = f.decrypt(text.encode()).decode()
            return [TextContent(type="text", text=json.dumps({"result": result}, indent=2))]
        except Exception as e:
            return [TextContent(type="text",
                text=json.dumps({"error": f"Fernet {action} failed: {e}"}, indent=2))]

    elif algorithm == "aes-gcm":
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        try:
            key_bytes = bytes.fromhex(key) if len(key) == 64 else hashlib.sha256(key.encode()).digest()
            aesgcm = AESGCM(key_bytes)
            if action == "encrypt":
                nonce = rand.token_bytes(12)
                ciphertext = aesgcm.encrypt(nonce, text.encode(), None)
                result = base64.b64encode(nonce + ciphertext).decode()
            else:
                raw = base64.b64decode(text)
                nonce, ciphertext = raw[:12], raw[12:]
                result = aesgcm.decrypt(nonce, ciphertext, None).decode()
            return [TextContent(type="text", text=json.dumps({"result": result}, indent=2))]
        except Exception as e:
            return [TextContent(type="text",
                text=json.dumps({"error": f"AES-GCM {action} failed: {e}"}, indent=2))]

@server.tool()
async def hash_checksum(
    text: str = "",
    file_path: str = "",
    algorithm: str = "sha256",
) -> list[TextContent]:
    """Compute a cryptographic hash/checksum for text or a file.

    Args:
        text: Text to hash (if no file_path provided)
        file_path: Path to file to hash (takes precedence over text)
        algorithm: "md5", "sha1", "sha256", "sha512", "blake2b"
    """
    algos = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
        "blake2b": hashlib.blake2b,
    }
    if algorithm not in algos:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    h = algos[algorithm]()
    if file_path:
        p = Path(file_path)
        if not p.exists():
            return [TextContent(type="text",
                text=json.dumps({"error": f"File not found: {file_path}"}, indent=2))]
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    else:
        h.update(text.encode())

    return [TextContent(type="text", text=json.dumps({
        "algorithm": algorithm,
        "hash": h.hexdigest(),
        "digest_size_bytes": h.digest_size,
    }, indent=2))]

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@server.resource("secrets://vault-status")
async def vault_status() -> str:
    return json.dumps({
        "total_secrets": len(_vault.get("secrets", {})),
        "master_key_set": bool(os.environ.get("SECRETS_MASTER_KEY")),
        "vault_path": str(VAULT_PATH.resolve()),
        "encrypted": os.environ.get("SECRETS_MASTER_KEY", "") != "",
    }, indent=2)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@server.prompt(
    name="security-audit",
    description="Audit secrets and suggest security improvements",
    arguments={
        "scope": {"type": "string", "description": "What to audit — 'passwords', 'keys', 'all'", "required": False},
    },
)
async def security_audit_prompt(scope: str = "all") -> dict:
    vault_entries = len(_vault.get("secrets", {}))
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""You are a security auditor. Review the following security posture:

Vault status: {vault_entries} secrets stored
Master key configured: {bool(os.environ.get('SECRETS_MASTER_KEY'))}
Scope: {scope}

Provide recommendations:
1. How to improve secret storage security
2. Password policy recommendations
3. Key rotation best practices
4. Any immediate risks to address

Be specific and actionable.""",
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
