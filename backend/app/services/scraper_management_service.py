from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.layout_pattern import LayoutPattern
from app.models.scraper_run import ScraperRun
from app.models.scraper_source import ScraperSource
from app.schemas.scraper import ScraperSourceCreate, ScraperSourceUpdate


async def create_scraper_source(
    db: AsyncSession,
    user_id: str,
    data: ScraperSourceCreate,
) -> ScraperSource:
    source = ScraperSource(created_by=user_id, **data.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


async def list_scraper_sources(db: AsyncSession) -> list[ScraperSource]:
    result = await db.execute(select(ScraperSource).order_by(desc(ScraperSource.added_at)))
    return list(result.scalars().all())


async def get_scraper_source(db: AsyncSession, source_id: str) -> ScraperSource:
    source = await db.get(ScraperSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Scraper source not found")
    return source


async def update_scraper_source(
    db: AsyncSession,
    source_id: str,
    data: ScraperSourceUpdate,
) -> ScraperSource:
    source = await get_scraper_source(db, source_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(source, field, value)
    await db.commit()
    await db.refresh(source)
    return source


async def delete_scraper_source(db: AsyncSession, source_id: str) -> None:
    source = await get_scraper_source(db, source_id)
    reference_count = await db.scalar(
        select(func.count())
        .select_from(ScraperRun)
        .where(ScraperRun.source_id == source_id)
    )
    pattern_count = await db.scalar(
        select(func.count())
        .select_from(LayoutPattern)
        .where(LayoutPattern.source_id == source_id)
    )
    if reference_count or pattern_count:
        raise HTTPException(
            status_code=409,
            detail="Scraper source with recorded runs or patterns cannot be deleted",
        )
    await db.delete(source)
    await db.commit()


async def list_scraper_runs(db: AsyncSession) -> list[ScraperRun]:
    result = await db.execute(select(ScraperRun).order_by(desc(ScraperRun.started_at)))
    return list(result.scalars().all())


async def get_scraper_run(db: AsyncSession, run_id: str) -> ScraperRun:
    run = await db.get(ScraperRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Scraper run not found")
    return run


async def get_latest_scraper_run(db: AsyncSession) -> ScraperRun:
    result = await db.execute(select(ScraperRun).order_by(desc(ScraperRun.started_at)).limit(1))
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="No scraper runs found")
    return run


async def list_layout_patterns(db: AsyncSession) -> list[LayoutPattern]:
    result = await db.execute(select(LayoutPattern).order_by(desc(LayoutPattern.created_at)))
    return list(result.scalars().all())
