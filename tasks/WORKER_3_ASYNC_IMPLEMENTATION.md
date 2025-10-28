# Worker 3: Async & Event-Driven Implementation - Week 2 MVP

**Worker ID**: Worker 3 (Performance & Scalability Approach)
**Approach**: SQLAlchemy Async + Event-Driven State Machine + FastAPI Async + Redis
**Priority**: Performance, Scalability, Future-Proofing
**Estimated Time**: 60-70h
**Codex Worker**: Use regular Claude workers (not Codex)

---

## 🎯 Mission

Implement Week 2 MVP with **async/await patterns and event-driven architecture** for maximum performance and scalability, preparing for Week 3 WebSocket streaming.

---

## 📋 Implementation Strategy

### Philosophy
- ✅ **Async-first** - Non-blocking I/O for all operations
- ✅ **Event-driven** - State changes emit events
- ✅ **Performance** - Optimize for high throughput
- ✅ **Future-proof** - Prepare for WebSocket integration

### Technology Stack
- **Database**: SQLAlchemy 2.0 Async (asyncpg for PostgreSQL, aiosqlite for SQLite)
- **State Machine**: Event-driven architecture with async event handlers
- **API**: FastAPI with async endpoints
- **Cache**: Redis for idempotency keys and session data
- **Events**: In-memory event bus (extensible to Redis Pub/Sub)
- **Auth**: python-jose for JWT, passlib + argon2-cffi
- **Testing**: pytest-asyncio + pytest-aiohttp

### Additional Dependencies

Add to `requirements.txt`:
```python
# Async database drivers
asyncpg>=0.29.0           # PostgreSQL async driver
aiosqlite>=0.19.0         # SQLite async driver

# Redis for caching
redis>=5.0.0              # Redis client
aioredis>=2.0.1           # Async Redis client

# Event handling
aio-pika>=9.3.0           # RabbitMQ client (optional, for distributed events)
```

---

## 📁 Project Structure

```
orchestrator/
├── core/
│   ├── database_async.py    ← Create: Async database configuration
│   ├── models_async.py      ← Create: SQLAlchemy async models
│   ├── schemas.py           ← Create: Pydantic schemas
│   ├── events.py            ← Create: Event bus and event definitions
│   ├── state_machine.py     ← Create: Event-driven state machine
│   ├── cache.py             ← Create: Redis caching layer
│   └── auth.py              ← Create: JWT authentication
├── api/
│   ├── main.py              ← Update: Add async routers
│   ├── dependencies.py      ← Create: Async dependencies
│   ├── supervisor_api.py    ← Create: 6 async endpoints
│   ├── resources_api.py     ← Create: 4 async endpoints
│   └── jobs_api.py          ← Create: 4 async endpoints
└── alembic/
    ├── versions/
    │   └── 001_initial_schema.py
    └── env.py               ← Configure: Async migrations
```

---

## 🔨 Implementation Tasks

### Phase 1: Async Database & Infrastructure (12h)

#### Task 1.1: Async Database Configuration (3h)

**File**: `orchestrator/core/database_async.py`

**Requirements**:
- AsyncEngine and async_sessionmaker
- Connection pooling for async operations
- Context manager for async sessions

**Pattern**:
```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from contextlib import asynccontextmanager

class AsyncDatabaseSettings(BaseSettings):
    """Async database configuration"""
    database_url: str = "sqlite+aiosqlite:///./parallel_ai.db"
    # For PostgreSQL: postgresql+asyncpg://user:pass@localhost/db

    model_config = SettingsConfigDict(env_file=".env", env_prefix="DB_")

settings = AsyncDatabaseSettings()

# Create async engine
async_engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.echo_sql,
    pool_size=settings.pool_size,
    max_overflow=settings.max_overflow,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async database session dependency.

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
        @app.get("/items")
        async def list_items(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

#### Task 1.2: Redis Cache Layer (3h)

**File**: `orchestrator/core/cache.py`

**Requirements**:
- Redis connection pool
- Idempotency key caching
- Session data caching
- TTL management

**Pattern**:
```python
import aioredis
from typing import Optional, Any
import json

class CacheManager:
    """
    Redis cache manager for idempotency and session data.

    Performance: Async operations, connection pooling
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize Redis connection pool"""
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """Establish Redis connection"""
        self.redis = await aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )

    async def set_idempotency_key(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600
    ) -> None:
        """
        Store idempotency key with TTL.

        Args:
            key: Idempotency key (request_id)
            value: Operation result
            ttl_seconds: Time to live (default: 1 hour)
        """
        await self.redis.setex(
            f"idempotency:{key}",
            ttl_seconds,
            json.dumps(value)
        )

    async def get_idempotency_key(self, key: str) -> Optional[Any]:
        """Retrieve cached idempotency result"""
        cached = await self.redis.get(f"idempotency:{key}")
        return json.loads(cached) if cached else None

cache_manager = CacheManager()
```

#### Task 1.3: Event Bus Architecture (3h)

**File**: `orchestrator/core/events.py`

**Requirements**:
- Event base class
- Event bus for pub/sub
- Async event handlers
- Event history for audit trail

**Pattern**:
```python
from typing import Callable, Dict, List, Any
from datetime import datetime
from pydantic import BaseModel
import asyncio

class Event(BaseModel):
    """
    Base event class.

    All state changes emit events for loose coupling.
    """
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]

class WorkerStateChangedEvent(Event):
    """Event: Worker state transition occurred"""
    event_type: str = "worker.state.changed"
    worker_id: str
    from_state: str
    to_state: str

class EventBus:
    """
    In-memory event bus with async handlers.

    Performance: Async event propagation
    Scalability: Can be extended to Redis Pub/Sub or RabbitMQ
    """

    def __init__(self):
        """Initialize event bus"""
        self._handlers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe to event type.

        Args:
            event_type: Event type to listen for
            handler: Async handler function
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event: Event) -> None:
        """
        Publish event to all subscribers.

        Args:
            event: Event instance to publish

        Performance: Async handlers run concurrently
        """
        self._event_history.append(event)

        handlers = self._handlers.get(event.event_type, [])
        await asyncio.gather(
            *[handler(event) for handler in handlers],
            return_exceptions=True
        )

event_bus = EventBus()
```

#### Task 1.4: Async SQLAlchemy Models (3h)

**File**: `orchestrator/core/models_async.py`

**Requirements**:
- Async model operations
- Async relationships
- Async queries

**Pattern**:
```python
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(AsyncAttrs, DeclarativeBase):
    """Base class for async models"""
    pass

class Worker(Base):
    """
    Async worker model.

    Performance: Async operations for all I/O
    """
    __tablename__ = "workers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[WorkerStatus] = mapped_column(SQLEnum(WorkerStatus), nullable=False)

    @classmethod
    async def get_by_id(cls, session: AsyncSession, worker_id: str) -> Optional["Worker"]:
        """
        Async query: Get worker by ID.

        Args:
            session: Async database session
            worker_id: Worker identifier

        Returns:
            Worker instance or None
        """
        result = await session.execute(
            select(cls).where(cls.id == worker_id)
        )
        return result.scalar_one_or_none()
```

---

### Phase 2: Event-Driven State Machine (10h)

#### Task 2.1: Worker State Machine with Events (5h)

**File**: `orchestrator/core/state_machine.py`

**Requirements**:
- Async state transitions
- Event emission on state changes
- Event-driven side effects
- Saga pattern for distributed transactions

**Pattern**:
```python
class WorkerStateMachine:
    """
    Event-driven async state machine.

    Architecture: Events trigger state changes, state changes emit events
    Performance: Async operations, non-blocking
    """

    def __init__(
        self,
        worker_id: str,
        db_session: AsyncSession,
        event_bus: EventBus
    ):
        """Initialize async state machine"""
        self.worker_id = worker_id
        self.db_session = db_session
        self.event_bus = event_bus

    async def transition(
        self,
        from_state: WorkerStatus,
        to_state: WorkerStatus
    ) -> None:
        """
        Execute async state transition with event emission.

        Args:
            from_state: Current state
            to_state: Target state

        Raises:
            InvalidTransitionError: If transition not allowed
        """
        # Validate transition
        if not self._is_valid_transition(from_state, to_state):
            raise InvalidTransitionError(f"{from_state} -> {to_state}")

        # Update database (async)
        await self._update_worker_state(to_state)

        # Emit event (async handlers will execute)
        event = WorkerStateChangedEvent(
            worker_id=self.worker_id,
            from_state=from_state.value,
            to_state=to_state.value,
            timestamp=datetime.utcnow(),
            data={}
        )
        await self.event_bus.publish(event)

    async def _update_worker_state(self, new_state: WorkerStatus) -> None:
        """Persist state change to database"""
        worker = await Worker.get_by_id(self.db_session, self.worker_id)
        if worker:
            worker.status = new_state
            await self.db_session.commit()

# Event handler example
async def on_worker_paused(event: WorkerStateChangedEvent) -> None:
    """
    Event handler: React to worker pause.

    This is called automatically when WorkerStateChangedEvent is published.
    """
    logger.info(f"Worker {event.worker_id} paused, triggering cleanup...")
    # Async cleanup operations

# Subscribe handlers
event_bus.subscribe("worker.state.changed", on_worker_paused)
```

#### Task 2.2: Job State Machine (5h)

Similar event-driven pattern for Job lifecycle.

---

### Phase 3: Authentication (4h)

#### Task 3.1: Async JWT Module (4h)

**File**: `orchestrator/core/auth.py`

**Requirements**:
- Async token validation
- Redis-backed token blacklist
- Async password hashing

**Pattern**:
```python
import asyncio
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

async def hash_password(password: str) -> str:
    """
    Async password hashing with Argon2id.

    Performance: Run blocking operation in thread pool
    """
    return await asyncio.to_thread(pwd_context.hash, password)

async def verify_password(plain: str, hashed: str) -> bool:
    """Async password verification"""
    return await asyncio.to_thread(pwd_context.verify, plain, hashed)
```

---

### Phase 4: Async API Endpoints (18h)

#### Task 4.1: Async API Dependencies (3h)

**File**: `orchestrator/api/dependencies.py`

**Requirements**:
- Async database session injection
- Async JWT validation
- Redis cache injection

**Pattern**:
```python
from typing import Annotated
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

async def get_current_user_async(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(security)],
    cache: Annotated[CacheManager, Depends(get_cache)]
) -> TokenData:
    """
    Async JWT validation with Redis caching.

    Performance: Cache validated tokens to reduce JWT decode overhead
    """
    # Check cache first
    cached_user = await cache.get(f"token:{credentials.credentials}")
    if cached_user:
        return TokenData(**cached_user)

    # Validate token
    try:
        token_data = verify_token(credentials.credentials)
        # Cache for 5 minutes
        await cache.set(f"token:{credentials.credentials}", token_data.model_dump(), ttl_seconds=300)
        return token_data
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

#### Task 4.2: Async Supervisor API (7h)

**File**: `orchestrator/api/supervisor_api.py`

**Requirements**:
- All endpoints async
- Non-blocking database queries
- Event emission for state changes

**Pattern**:
```python
@router.post("/workers/{worker_id}/pause")
async def pause_worker(
    worker_id: str,
    request_id: Annotated[str, Header()],
    db: Annotated[AsyncSession, Depends(get_async_db)],
    cache: Annotated[CacheManager, Depends(get_cache)],
    user: Annotated[TokenData, Depends(require_scope("supervisor:write"))]
) -> WorkerResponse:
    """
    Async pause worker with idempotency.

    Performance: Async database operations, Redis idempotency check
    """
    # Check idempotency
    cached_result = await cache.get_idempotency_key(request_id)
    if cached_result:
        return WorkerResponse(**cached_result)

    # Get worker (async)
    worker = await Worker.get_by_id(db, worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    # Execute state transition (async, emits events)
    state_machine = WorkerStateMachine(worker_id, db, event_bus)
    await state_machine.transition(worker.status, WorkerStatus.PAUSED)

    # Reload worker
    await db.refresh(worker)
    result = WorkerResponse.model_validate(worker)

    # Cache result
    await cache.set_idempotency_key(request_id, result.model_dump())

    return result
```

#### Task 4.3: Async Resource Manager API (4h)

#### Task 4.4: Async Job Orchestrator API (4h)

---

### Phase 5: Testing (12h)

#### Task 5.1: Async Unit Tests (7h)

**Requirements**:
- pytest-asyncio for async tests
- Mock async database operations
- Test event emission and handling

**Pattern**:
```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_worker_state_transition_emits_event():
    """
    Test: State transition emits event asynchronously.

    Performance test: Verify event handlers run concurrently
    """
    mock_db = AsyncMock(spec=AsyncSession)
    mock_event_bus = AsyncMock(spec=EventBus)

    sm = WorkerStateMachine("worker-1", mock_db, mock_event_bus)

    await sm.transition(WorkerStatus.IDLE, WorkerStatus.RUNNING)

    # Verify event published
    mock_event_bus.publish.assert_called_once()
    event = mock_event_bus.publish.call_args[0][0]
    assert event.event_type == "worker.state.changed"
    assert event.to_state == "RUNNING"
```

**Files**:
- `tests/unit/test_models_async.py` (2h)
- `tests/unit/test_state_machine_async.py` (3h)
- `tests/unit/test_cache.py` (2h)

**Coverage Target**: 75% minimum

#### Task 5.2: Async Integration Tests (5h)

**Files**:
- `tests/integration/test_supervisor_api_async.py` (2h)
- `tests/integration/test_resources_api_async.py` (1.5h)
- `tests/integration/test_jobs_api_async.py` (1.5h)

---

### Phase 6: Performance Optimization (6h)

#### Task 6.1: Connection Pooling Tuning (2h)

- Optimize asyncpg pool size
- Configure pool timeout
- Benchmark performance

#### Task 6.2: Redis Caching Strategy (2h)

- Cache hot paths (token validation, worker status)
- TTL optimization
- Cache invalidation strategy

#### Task 6.3: Async Query Optimization (2h)

- Use `selectinload` for eager loading
- Batch queries
- Profile slow queries

---

### Phase 7: Documentation (4h)

Same as Worker 1 & 2.

---

## 🎯 Deliverables

### Code Files (17 files)
1. `orchestrator/core/database_async.py`
2. `orchestrator/core/models_async.py`
3. `orchestrator/core/schemas.py`
4. `orchestrator/core/events.py` (NEW)
5. `orchestrator/core/state_machine.py` (event-driven)
6. `orchestrator/core/cache.py` (NEW)
7. `orchestrator/core/auth.py`
8. `orchestrator/api/dependencies.py`
9. `orchestrator/api/supervisor_api.py`
10. `orchestrator/api/resources_api.py`
11. `orchestrator/api/jobs_api.py`
12. `orchestrator/api/main.py` (updated)
13. `alembic/versions/001_initial_schema.py`
14. `alembic/env.py` (async migrations)
15-17. Test files (async unit + integration)

### Infrastructure
- Redis for caching
- Event bus architecture
- Performance benchmarks

### Tests
- Async unit tests (≥75% coverage)
- Async integration tests
- Performance tests

---

## ✅ Success Criteria

- [ ] All 14 API endpoints async
- [ ] Event-driven state machine working
- [ ] Redis caching operational
- [ ] 75%+ test coverage
- [ ] Performance benchmarks pass (>1000 req/s)
- [ ] All async tests passing
- [ ] No blocking I/O operations
- [ ] Excellence AI Standard 100% compliance

---

## 📚 Reference Documents

Same as Worker 1 & 2, plus:
- SQLAlchemy Async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- FastAPI Async: https://fastapi.tiangolo.com/async/
- aioredis: https://aioredis.readthedocs.io/

---

## 🔧 Development Commands

```bash
# Install async dependencies
pip install asyncpg aiosqlite aioredis

# Start Redis
docker run -d -p 6379:6379 redis:latest

# Run async migrations
alembic upgrade head

# Run API server
uvicorn orchestrator.api.main:app --reload --port 8000

# Run async tests
pytest tests/ -v --asyncio-mode=auto

# Performance benchmarks
locust -f tests/performance/locustfile.py
```

---

## 🚨 Important Notes

1. **Async everywhere**: All I/O operations must be async
2. **Event-driven**: State changes emit events, avoid tight coupling
3. **Redis required**: For caching and idempotency
4. **Performance focus**: Target >1000 requests/second
5. **Future-proof**: Architecture supports WebSocket (Week 3)

---

**Remember**: Performance and scalability are priorities. Optimize for throughput!

Good luck, Worker 3! 🚀⚡
