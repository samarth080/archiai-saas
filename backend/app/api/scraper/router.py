from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.scraper import (
    LayoutPatternOut,
    ScraperRunOut,
    ScraperRunRequest,
    ScraperSourceCreate,
    ScraperSourceOut,
    ScraperSourceUpdate,
)
from app.services.auth_service import get_current_user
from app.services.scraper_management_service import (
    create_scraper_source,
    delete_scraper_source,
    get_latest_scraper_run,
    get_scraper_run,
    get_scraper_source,
    list_layout_patterns,
    list_scraper_runs,
    list_scraper_sources,
    update_scraper_source,
)
from app.services.scraper_service import run_source_scraper
from app.utils.activity import log_activity

router = APIRouter(prefix="/api/scraper", tags=["scraper"])
bearer = HTTPBearer(auto_error=False)


async def _current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> str:
    if credentials is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await get_current_user(db, credentials.credentials)
    return str(user.id)


@router.post("/sources", response_model=ScraperSourceOut, status_code=201)
async def create_source(
    data: ScraperSourceCreate,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await create_scraper_source(db, user_id, data)


@router.get("/sources", response_model=list[ScraperSourceOut])
async def sources(
    _user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_scraper_sources(db)


@router.get("/sources/{source_id}", response_model=ScraperSourceOut)
async def source(
    source_id: str,
    _user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_scraper_source(db, source_id)


@router.put("/sources/{source_id}", response_model=ScraperSourceOut)
async def update_source(
    source_id: str,
    data: ScraperSourceUpdate,
    _user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await update_scraper_source(db, source_id, data)


@router.delete("/sources/{source_id}", status_code=204)
async def delete_source(
    source_id: str,
    _user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await delete_scraper_source(db, source_id)


@router.post("/run", response_model=ScraperRunOut)
async def run(
    data: ScraperRunRequest,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    source_record = await get_scraper_source(db, data.source_id)
    scraper_run = await run_source_scraper(db, source_record)
    await log_activity(db, user_id, f"scraper.run_{scraper_run.status}")
    return scraper_run


@router.get("/runs", response_model=list[ScraperRunOut])
async def runs(
    _user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_scraper_runs(db)


@router.get("/runs/{run_id}", response_model=ScraperRunOut)
async def run_detail(
    run_id: str,
    _user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_scraper_run(db, run_id)


@router.get("/status", response_model=ScraperRunOut)
async def status(
    _user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_latest_scraper_run(db)


@router.get("/patterns", response_model=list[LayoutPatternOut])
async def patterns(
    _user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_layout_patterns(db)
