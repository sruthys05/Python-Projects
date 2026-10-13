from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.url import Stats, URLCreate, URLResponse
from app.services.url_service import URLExpiredError, URLService

router = APIRouter(tags=["urls"])
url_service = URLService()


@router.post("/shorten", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
def shorten_url(payload: URLCreate, request: Request, session: Session = Depends(get_db)) -> URLResponse:
    mapping = url_service.create_url(session, str(payload.url), payload.expires_in_days)
    return URLResponse(
        short_code=mapping.short_code,
        short_url=str(request.base_url).rstrip("/") + "/" + mapping.short_code,
        long_url=mapping.long_url,
        created_at=mapping.created_at,
        expires_at=mapping.expires_at,
    )


@router.get("/stats/{short_code}", response_model=Stats)
def get_stats(short_code: str, session: Session = Depends(get_db)) -> Stats:
    try:
        return url_service.get_stats(session, short_code)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Short URL not found") from error
    except URLExpiredError as error:
        raise HTTPException(status_code=410, detail="Short URL has expired") from error


@router.get("/{short_code}", response_class=RedirectResponse, include_in_schema=False)
def redirect_url(short_code: str, session: Session = Depends(get_db)) -> Response:
    try:
        destination = url_service.resolve(session, short_code)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Short URL not found") from error
    except URLExpiredError as error:
        raise HTTPException(status_code=410, detail="Short URL has expired") from error
    return RedirectResponse(url=destination, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
