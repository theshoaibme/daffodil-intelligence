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


# === MongoDB Integration ===
# pyrefly: ignore [missing-import]
import motor.motor_asyncio

_mongo_client = None
_mongo_db = None

def get_mongo_db():
    global _mongo_client, _mongo_db
    if _mongo_client is None and settings.MONGO_URL:
        try:
            _mongo_client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URL)
            db_name = "daffodil"
            try:
                # pyrefly: ignore [missing-import]
                from pymongo.uri_parser import parse_uri
                parsed = parse_uri(settings.MONGO_URL)
                if parsed.get("database"):
                    db_name = parsed["database"]
            except Exception:
                pass
            _mongo_db = _mongo_client[db_name]
            print(f"Connected to MongoDB: {db_name}")
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            _mongo_client = None
            _mongo_db = None
    return _mongo_db

def to_dict(obj):
    data = {}
    if hasattr(obj, '__class__') and hasattr(obj.__class__, '__table__'):
        for c in obj.__class__.__table__.columns:
            val = getattr(obj, c.name, None)
            data[c.name] = val
    return data

def from_dict(model_cls, data):
    if not data:
        return None
    obj = model_cls()
    if hasattr(model_cls, '__table__'):
        for c in model_cls.__table__.columns:
            if c.name in data:
                setattr(obj, c.name, data[c.name])
    return obj

class MongoSession:
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
        
        model_cls = None
        if hasattr(query, 'column_descriptions') and query.column_descriptions:
            model_cls = query.column_descriptions[0].get('entity') or query.column_descriptions[0].get('type')
            
        cls_name = model_cls.__name__ if model_cls else ""
        if not cls_name:
            query_str = str(query).lower()
            if 'user' in query_str:
                cls_name = 'User'
            elif 'chat' in query_str:
                cls_name = 'Chat'
            elif 'message' in query_str:
                cls_name = 'Message'
            elif 'session' in query_str:
                cls_name = 'Session'
            elif 'document' in query_str:
                cls_name = 'Document'
            elif 'ticket' in query_str:
                cls_name = 'Ticket'
            else:
                cls_name = 'Unknown'
                
        if not model_cls:
            import sys
            for module_name, module in list(sys.modules.items()):
                if 'models.' in module_name:
                    model_cls = getattr(module, cls_name, None)
                    if model_cls:
                        break
                        
        collection_name = f"{cls_name.lower()}s"
        db = get_mongo_db()
        
        filters = {}
        try:
            params = query.compile().params
            for k, v in params.items():
                col_name = re.sub(r'_\d+$', '', k)
                filters[col_name] = v
        except Exception:
            pass
            
        mongo_query = {}
        for col, val in filters.items():
            mongo_query[col] = val
            
        docs = []
        if db is not None:
            try:
                cursor = db[collection_name].find(mongo_query)
                offset = query._offset if hasattr(query, '_offset') and query._offset is not None else 0
                limit = query._limit if hasattr(query, '_limit') and query._limit is not None else None
                
                if offset:
                    cursor = cursor.skip(offset)
                if limit is not None:
                    cursor = cursor.limit(limit)
                
                async for doc in cursor:
                    if model_cls:
                        obj = from_dict(model_cls, doc)
                        docs.append(obj)
                    else:
                        docs.append(doc)
            except Exception as e:
                print(f"MongoDB query execute error: {e}")
                
        return MockResult(docs)
        
    def add(self, obj):
        if not hasattr(obj, 'id') or obj.id is None:
            import time
            obj.id = int(time.time() * 1000)
            
        from datetime import datetime
        now = datetime.utcnow()
        for field in ['created_at', 'updated_at', 'started_at']:
            if hasattr(obj, field) and getattr(obj, field) is None:
                setattr(obj, field, now)
                
        self.added.append(obj)
        
    async def commit(self):
        db = get_mongo_db()
        if db is not None:
            for obj in self.added:
                cls_name = obj.__class__.__name__
                collection_name = f"{cls_name.lower()}s"
                doc = to_dict(obj)
                try:
                    await db[collection_name].update_one(
                        {"id": obj.id},
                        {"$set": doc},
                        upsert=True
                    )
                except Exception as e:
                    print(f"MongoDB commit error: {e}")
        self.committed = True
        
    async def refresh(self, obj):
        pass


async def get_db():
    global _use_mock
    
    if settings.MONGO_URL:
        session = MongoSession()
        try:
            yield session
        finally:
            pass
        return
        
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
    if settings.MONGO_URL:
        db = get_mongo_db()
        if db is not None:
            print("MongoDB initialized successfully")
            return
        else:
            print("Failed to initialize MongoDB, using mock")
            _use_mock = True
            return
            
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