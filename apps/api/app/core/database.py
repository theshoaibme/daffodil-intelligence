from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import exc, text
from .config import get_settings

settings = get_settings()
Base = declarative_base()

_engine = None
_async_session = None
_use_mock = False


class MockStore:
    _users = {}
    _chats = {}
    _messages = {}
    _sessions = {}
    _documents = {}
    _tickets = {}
    _counter = 1


class MockSession:
    def __init__(self):
        self.added = []
        self.committed = False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass
    
    async def execute(self, query):
        from datetime import datetime
        import re
        
        class MockScalars:
            def __init__(self, data):
                self._data = data
            def all(self):
                return self._data
            def first(self):
                if self._data:
                    return self._data[0]
                return None
        
        class MockResult:
            def __init__(self, data):
                self._data = data
            
            def scalar_one_or_none(self):
                if self._data:
                    return self._data[0]
                return None
            
            def scalars(self):
                return MockScalars(self._data)
        
        # Get the model class being queried
        model_cls = None
        if hasattr(query, 'column_descriptions') and query.column_descriptions:
            model_cls = query.column_descriptions[0].get('entity') or query.column_descriptions[0].get('type')
            
        cls_name = model_cls.__name__ if model_cls else ""
        store_name = f"_{cls_name.lower()}s"
        store = getattr(MockStore, store_name, None)
        
        # Fallback if class name didn't match directly
        if store is None:
            query_str = str(query).lower()
            if 'user' in query_str:
                store = MockStore._users
            elif 'chat' in query_str:
                store = MockStore._chats
            elif 'message' in query_str:
                store = MockStore._messages
            elif 'session' in query_str:
                store = MockStore._sessions
            elif 'document' in query_str:
                store = MockStore._documents
            elif 'ticket' in query_str:
                store = MockStore._tickets
            else:
                store = {}
                
        data = list(store.values())
        
        # Extract filter criteria from query parameters
        filters = {}
        try:
            params = query.compile().params
            for k, v in params.items():
                col_name = re.sub(r'_\d+$', '', k)
                filters[col_name] = v
        except Exception:
            pass
            
        filtered_data = []
        for obj in data:
            match = True
            for col, val in filters.items():
                if hasattr(obj, col):
                    obj_val = getattr(obj, col)
                    if obj_val != val:
                        match = False
                        break
            if match:
                filtered_data.append(obj)
                
        # Sort by created_at if present
        if filtered_data and hasattr(filtered_data[0], 'created_at'):
            filtered_data.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
            
        # Apply offset and limit
        offset = query._offset if hasattr(query, '_offset') and query._offset is not None else 0
        limit = query._limit if hasattr(query, '_limit') and query._limit is not None else None
        
        if offset:
            filtered_data = filtered_data[offset:]
        if limit is not None:
            filtered_data = filtered_data[:limit]
            
        return MockResult(filtered_data)
    
    def add(self, obj):
        if not hasattr(obj, 'id') or obj.id is None:
            obj.id = MockStore._counter
            MockStore._counter += 1
            
        from datetime import datetime
        now = datetime.utcnow()
        for field in ['created_at', 'updated_at', 'started_at']:
            if hasattr(obj, field) and getattr(obj, field) is None:
                setattr(obj, field, now)
                
        self.added.append(obj)
    
    async def commit(self):
        self.committed = True
        for obj in self.added:
            cls_name = obj.__class__.__name__
            store_name = f"_{cls_name.lower()}s"
            store = getattr(MockStore, store_name, None)
            if store is not None:
                store[obj.id] = obj
    
    async def refresh(self, obj):
        pass


def get_engine():
    global _engine
    if _engine is None:
        try:
            async_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
            _engine = create_async_engine(
                async_url, 
                echo=False, 
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
        except Exception as e:
            print(f"Database engine error: {e}")
            print("Using in-memory mock database for development")
            _engine = None
            global _use_mock
            _use_mock = True
    return _engine

def get_session_maker():
    global _async_session
    engine = get_engine()
    if engine and _async_session is None:
        _async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return _async_session


async def get_db():
    global _use_mock
    
    if _use_mock or get_session_maker() is None:
        session = MockSession()
        try:
            yield session
        finally:
            pass
        return
    
    session_maker = get_session_maker()
    if session_maker is None:
        raise Exception("Database not initialized")
    
    async with session_maker() as session:
        try:
            yield session
        except exc.SQLAlchemyError:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    global _use_mock
    engine = get_engine()
    if engine:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                await conn.execute(
                    text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(512)")
                )
        except Exception as e:
            print(f"Table creation: {e}")
            _use_mock = True
    else:
        print("Using in-memory mock database")
        _use_mock = True


def is_mock_database() -> bool:
    return _use_mock


async def close_db():
    global _engine, _async_session
    if _engine:
        await _engine.dispose()
        _engine = None
        _async_session = None