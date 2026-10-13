
from fastapi import HTTPException, Request, status

from app.storage.repository import MongoRepository


def get_repository(request: Request) -> MongoRepository:
    """
    Return the MongoDB repository initialized by
    the FastAPI lifespan.
    """

    repository = getattr(
        request.app.state,
        "repository",
        None,
    )

    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable",
        )

    return repository
