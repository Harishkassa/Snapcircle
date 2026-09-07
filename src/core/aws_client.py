from src.core import *

# internal imports
from src.exception import (S3ClientInitException, 
                           S3StorageException)

logger = logging.getLogger(__name__)

class S3Service:
    """
    TRUE Singleton — class-level attribute + guard check
    Chahe kitni baar S3Service() call karo, connection sirf EK BAAR banega
    """

    # Class-level attributes (instance-level nahi) — sabhi objects ke beech shared
    _client = None
    _bucket_name = None


    def __init__(self):
        if settings.AWS_SECRET_ACCESS_KEY is None:
            raise S3ClientInitException("Environment variable AWS_SECRET_ACCESS_KEY is not not set.")
        if settings.AWS_ACCESS_KEY_ID is None:
            raise S3ClientInitException("Environment variable AWS_ACCESS_KEY_ID is not set.")

        
        if S3Service._client is None:
            # Enterprise timeout configuration to prevent hanging connections
            boto_config = Config(
                connection_timeout=5,
                read_timeout=10,
                retries = {"max_connection" : 3, "mode" : "standard"}
            )

            try:
                # Initialize the unified Boto3 S3 Client
                S3Service._client = boto3.client(
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION,
                    endpoint_url=settings.AWS_ENDPOINT_URL,
                    config=boto_config
                )
                S3Service._bucket_name = settings.AWS_S3_BUCKET_NAME
                logger.info("Boto3 S3 Client initialized successfully.")
            except Exception as e:
                logger.critical(f"S3 Client initialization failed: {str(e)}", exc_info=True)
                raise S3ClientInitException()
        
        # Instance apna reference class-level attribute ki taraf point karega
        self.client = S3Service._client
        self.bucket_name = S3Service._bucket_name
        
    async def upload_file(self, file_bytes : bytes, object_name : str):
        """Uploads raw binary data to the designated S3 bucket."""
        try:
            await self.client.put_object(
                Bucket= self.bucket_name,
                Key= object_name,
                Body= file_bytes
            )
            s3_path = f"s3://{self.bucket_name}/{object_name}"
            logger.info(f"Successfully uploaded object to {s3_path}")
        except Exception as e:
            logger.error(f"Failed uploading object {object_name}: {str(e)}", exc_info=True)
            raise S3StorageException(f"S3 Storage failed to upload the object file {object_name}.")
        
s3_service = S3Service()