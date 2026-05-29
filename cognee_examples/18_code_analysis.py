"""
18_code_analysis.py — Codebase Understanding & Architecture Analysis.

Simulates ingesting a code repository and building a code knowledge graph
where modules, classes, functions, and dependencies are entities connected
by import, call, inherit, and define relationships.

Prerequisites:
    pip install cognee
"""

import asyncio

import cognee


async def main():
    print("Building Code Knowledge Graph from a simulated codebase...")
    print("=" * 60)

    # ── Simulated codebase structure ───────────────────────────────────
    await cognee.add("""
    # File: src/auth/authenticator.py
    # Package: authentication

    class Authenticator:
        '''Handles user authentication and token management.'''
        def __init__(self, db: Database, token_service: TokenService):
            self.db = db
            self.token_service = token_service

        def authenticate(self, username: str, password: str) -> AuthResult:
            user = self.db.find_user(username)
            if not user:
                return AuthResult(success=False, reason="User not found")
            if not self.verify_password(password, user.password_hash):
                return AuthResult(success=False, reason="Invalid password")
            token = self.token_service.create_token(user.id)
            return AuthResult(success=True, token=token, user=user)

        def verify_password(self, password: str, password_hash: str) -> bool:
            # Uses bcrypt for password verification
            import bcrypt
            return bcrypt.checkpw(password.encode(), password_hash.encode())
    """, dataset_name="codebase")

    await cognee.add("""
    # File: src/auth/token_service.py
    # Package: authentication

    class TokenService:
        '''Creates and validates JWT tokens.'''
        def __init__(self, secret_key: str, token_ttl: int = 86400):
            self.secret_key = secret_key
            self.token_ttl = token_ttl

        def create_token(self, user_id: str) -> str:
            import jwt
            from datetime import datetime, timedelta
            payload = {
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(seconds=self.token_ttl),
            }
            return jwt.encode(payload, self.secret_key, algorithm='HS256')

        def validate_token(self, token: str) -> dict | None:
            import jwt
            try:
                return jwt.decode(token, self.secret_key, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return None
            except jwt.InvalidTokenError:
                return None
    """, dataset_name="codebase")

    await cognee.add("""
    # File: src/payment/processor.py
    # Package: payment

    from src.auth.authenticator import Authenticator
    from src.database import Database

    class PaymentProcessor:
        '''Handles payment transactions with gateway integration.'''
        def __init__(self, db: Database, authenticator: Authenticator,
                     gateway_url: str):
            self.db = db
            self.authenticator = authenticator
            self.gateway_url = gateway_url

        def process_payment(self, token: str, amount: float,
                            currency: str) -> PaymentResult:
            # Validate the user's auth token first
            auth = self.authenticator.token_service.validate_token(token)
            if not auth:
                return PaymentResult(success=False, reason="Invalid token")

            user = self.db.find_user(auth['user_id'])
            if not user:
                return PaymentResult(success=False, reason="User not found")

            # Charge the payment gateway
            charge = self.charge_gateway(user.payment_method, amount, currency)
            if not charge.success:
                return PaymentResult(success=False, reason=charge.error)

            # Record the transaction
            self.db.create_transaction(user.id, amount, currency, charge.id)
            return PaymentResult(success=True, transaction_id=charge.id)

        def charge_gateway(self, payment_method: str, amount: float,
                           currency: str) -> GatewayResponse:
            import requests
            response = requests.post(
                self.gateway_url,
                json={'method': payment_method, 'amount': amount,
                      'currency': currency},
                timeout=30
            )
            return GatewayResponse.from_response(response)

        def refund_payment(self, transaction_id: str) -> RefundResult:
            transaction = self.db.find_transaction(transaction_id)
            if not transaction:
                return RefundResult(success=False, reason="Not found")
            # Process refund through gateway
            # ...
            return RefundResult(success=True)
    """, dataset_name="codebase")

    await cognee.add("""
    # File: src/database.py
    # Package: database

    class Database:
        '''Database abstraction layer over PostgreSQL.'''
        def __init__(self, connection_string: str):
            self.connection_string = connection_string

        def find_user(self, username: str) -> User | None:
            pass

        def find_transaction(self, transaction_id: str) -> Transaction | None:
            pass

        def create_transaction(self, user_id: str, amount: float,
                               currency: str, gateway_id: str) -> Transaction:
            pass
    """, dataset_name="codebase")

    await cognee.cognify()

    # ── Code architecture queries ──────────────────────────────────────
    print("\n── Code Architecture Queries ──\n")

    queries = [
        # Dependency analysis
        "What does PaymentProcessor depend on and how are those dependencies "
        "used?",

        # Impact analysis
        "If I change the signature of TokenService.create_token(), which "
        "classes and methods are affected?",

        # Call chain tracing
        "Trace the full call chain from process_payment() to token validation. "
        "What happens at each step?",

        # Architecture overview
        "What are the main packages in this codebase and what does each contain?",
    ]

    for query in queries:
        print(f" Q: {query}")
        print("-" * 60)
        results = await cognee.search(query)
        for r in results:
            print(f"  → {r}")
        print()

    print("Done! Cognee can map code dependencies and answer impact-analysis")
    print("questions that would take manual grep + reading to answer.")


if __name__ == "__main__":
    asyncio.run(main())
