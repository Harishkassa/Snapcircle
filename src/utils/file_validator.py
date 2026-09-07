from src.utils import *

class FileValidator:
    
    ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
    MAX_SIZE = 5 * 1024 * 1024
    
    # for single file uploading but did not use this, we use websocket, liveness detection and frame quality real time
    # temporary
    async def _validate_single(self, file: UploadFile) -> UploadFile:
        if file.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Only JPEG & PNG allowed."
            )
        file_content = await file.read()
        if len(file_content) > self.MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 5MB limit."
            )
        await file.seek(0)
        return file

    
    # for temporary (single file upload at registeration)
    async def __call__(self, uploaded_file: UploadFile = File(...)) -> UploadFile:
        return await self._validate_single(uploaded_file)
    
    # async def validate_photofile(self, uploaded_file: UploadFile = File(...)) -> UploadFile:
    #     return await self._validate_single(uploaded_file)


class PhotosValidator():
    """
    Validates uploaded image files safely:
    1. Header pre-check (fast reject, not fully trustworthy on its own)
    2. Chunked read with a hard size cap (real DoS protection)
    3. Magic-byte + Pillow decode check (real content-type validation,
       does not trust the client-supplied Content-Type header)
    """
    
    ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
    MAX_SIZE = 5 * 1024 * 1024
    CHUNK_SIZE = 1024 * 1024

    MAGIC_BYTES = {
        b"\xff\xd8\xff": "image/jpeg",
        b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a": "image/png",
    }

    async def _validation_photos_files(self, file: UploadFile) -> UploadFile:
        
        if file.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Only JPEG & PNG allowed."
            )
        
        if file.size and file.size > self.MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 5MB limit."
            )
    
        # reset pointer BEFORE reading — protects against this validator
        # running more than once on the same UploadFile
        await file.seek(0)
        
        total_size = 0
        chunks = []
        while chunk := await file.read(self.CHUNK_SIZE):
            total_size += len(chunk)
            if total_size > self.MAX_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File size exceeds 5MB limit.",
                )
            chunks.append(chunk)
 
        file_bytes = b"".join(chunks)

        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )
        
        detected_type = self._detect_real_type(file_bytes)

        if detected_type not in self.ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match an allowed image type.",
            )
        
        try:
            img = Image.open(io.BytesIO(file_bytes))
            img.verify()  # decode-level check -- catches corrupted/fake images
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is not a valid image.",
            )
        
        # reset pointer so downstream code (e.g. S3 upload) can read it again
        await file.seek(0)
        return file

    def _detect_real_type(self, file_bytes: bytes) -> str | None:
        for signature, mime in self.MAGIC_BYTES.items():
            if file_bytes.startswith(signature):
                return mime
        return None


    # multiple images upload at event group 
    async def __call__(self, uploaded_photo_file: List[UploadFile] = File(...)) -> List[UploadFile]:
        validated_files = []
        for file in uploaded_photo_file:
            validated = await self._validation_photos_files(file)
            validated_files.append(validated)
        return validated_files
    

filevalidator = FileValidator()
photos_file_validator = PhotosValidator()