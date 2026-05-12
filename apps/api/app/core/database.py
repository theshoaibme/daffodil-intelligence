from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import exc
from .config import get_settings

settings = get_settings()
Base = declarative_base()

_engine = None
_async_session = None
_use_mock = False


class MockStore:
    _users = {}
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
        class MockResult:
            def __init__(self, data):
                self._data = data
            
            def scalar_one_or_none(self):
                if self._data:
                    return self._data[0]
                return None
        
        query_str = str(query)
        if 'User' in query_str or 'user' in query_str.lower():
            class MockUser:
                def __init__(self, data):
                    self.__dict__.update(data) if isinstance(data, dict) else None
                    for k, v in data.items() if isinstance(data, dict) else []:
                        setattr(self, k, v)
            
            users = [MockUser(u) for u in MockStore._users.values()]
            return MockResult(users)
        
        return MockResult([])
    
    def add(self, obj):
        if hasattr(obj, 'id') and obj.id is None:
            obj.id = MockStore._counter
            MockStore._counter += 1
        self.added.append(obj)
    
    async def commit(self):
        self.committed = True
        for obj in self.added:
            if hasattr(obj, 'email'):
                MockStore._users[obj.id] = {
                    'id': obj.id,
                    'email': obj.email,
                    'password_hash': obj.password_hash,
                    'full_name': obj.full_name,
                    'role': obj.role
                }
    
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
        except Exception as e:
            print(f"Table creation: {e}")
            _use_mock = True
    else:
        print("Using in-memory mock database")
        _use_mock = True


async def close_db():
    global _engine, _async_session
    if _engine:
        await _engine.dispose()
        _engine = None
        _async_session = None