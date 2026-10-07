from fastapi import HTTPException, status


class AcademicRAGException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class InvalidPDFException(AcademicRAGException):
    def __init__(self, filename: str, reason: str = "Invalid PDF format or corrupted file"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid PDF '{filename}': {reason}."
        )


class EmptyPDFException(AcademicRAGException):
    def __init__(self, filename: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The uploaded PDF '{filename}' contains 0 pages or is empty."
        )


class ScannedPDFException(AcademicRAGException):
    def __init__(self, filename: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"The uploaded PDF '{filename}' contains no extractable text. It appears to consist of scanned images or non-searchable raster pages. Please provide a PDF with digital text."
        )


class DuplicateDocumentException(AcademicRAGException):
    def __init__(self, filename: str, existing_filename: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate document detected: '{filename}' has the exact same content hash as previously indexed '{existing_filename}'."
        )


class FileTooLargeException(AcademicRAGException):
    def __init__(self, filename: str, size_mb: float, max_mb: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File '{filename}' ({size_mb:.2f} MB) exceeds maximum allowed size of {max_mb} MB."
        )


class MissingAPIKeyException(AcademicRAGException):
    def __init__(self, provider: str = "OpenAI"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing {provider} API key. Please configure OPENAI_API_KEY in the backend .env file or switch LLM_PROVIDER to ollama."
        )


class ProviderException(AcademicRAGException):
    def __init__(self, provider: str, error_detail: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{provider} service error: {error_detail}"
        )


class OllamaNotRunningException(AcademicRAGException):
    def __init__(self, base_url: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama is not running or unreachable at {base_url}. Please ensure Ollama is installed and started (`ollama serve`), or switch LLM_PROVIDER to openai."
        )


class VectorStoreException(AcademicRAGException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector database operation failed: {message}"
        )


class EmbeddingMismatchException(AcademicRAGException):
    def __init__(self, current_info: str, saved_info: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Embedding configuration mismatch: Current configuration is '{current_info}', "
                f"but existing Chroma database was built with '{saved_info}'. "
                f"To switch embedding providers, reset the collection or clear the Chroma database."
            )
        )


class EmptyQuestionException(AcademicRAGException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The question field cannot be empty. Please ask a specific academic question."
        )


class NoRelevantDocumentsException(AcademicRAGException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="I couldn't find enough information in the uploaded documents to answer this question."
        )
