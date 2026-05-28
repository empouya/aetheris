import os

os.environ.setdefault("AETHERIS_ENVIRONMENT", "testing")
os.environ.setdefault("AETHERIS_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("AETHERIS_REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("AETHERIS_QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("AETHERIS_MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("AETHERIS_MINIO_ACCESS_KEY", "test")
os.environ.setdefault("AETHERIS_MINIO_SECRET_KEY", "test")
os.environ.setdefault("AETHERIS_MINIO_BUCKET", "test")
os.environ.setdefault("AETHERIS_JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("AETHERIS_JWT_ALGORITHM", "HS256")
os.environ.setdefault("AETHERIS_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
