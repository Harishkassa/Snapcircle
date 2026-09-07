from src.db import *

# internal imports
from src.core import settings

from src.exception import DatabaseConnectionException

logger = logging.getLogger(__name__)

# Base = declarative_base()

class Base(DeclarativeBase):
    pass

class DatabaseConnection:
    """
        This helps to intialize the setup of database engine, session for connection and Base class
    """
    def __init__(self):
        try:
            self.engine = create_async_engine(
                str(settings.SQLALCHEMY_DATABASE_URI),

                future=True,

                # Connection Pool
                pool_size= 20,
                max_overflow= 40,
                pool_timeout= 30,
                pool_recycle= 1800,

                # for Production
                pool_pre_ping= True,

                # performance / stability
                echo= False,

                # Optional
                connect_args={
                    "command_timeout": 10
                },
            )

                    
        except Exception as e:
            logger.critical(f"Database bootstrap failed: {str(e)}", exc_info=True)
            raise DatabaseConnectionException("Failed to initialize database pool connection.")
        

        self.AsyncSessionLocal = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
        
            # Better production behavior (avoid lazy reloading / refresh query again and again keeps the data usable) 
            expire_on_commit=False
        )             
    # Test connection immediately during bootstrap
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    async def check_connection(self):
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("Database connection test successfully executed.")   
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}", exc_info=True)
            raise DatabaseConnectionException()

    async def get_db(self):
        async with self.AsyncSessionLocal() as db:
            try:
                yield db
                await db.commit()
            except SQLAlchemyError as e:
                await db.rollback()
                logger.error(f"Database transaction error: {str(e)}", exc_info=True)
                raise DatabaseConnectionException()
            except Exception:
                await db.rollback()
                raise

            # finally: Not for this because async with SessionLocal() automatically context exit par session close kar deta hai
            #     db.close()


db = DatabaseConnection()