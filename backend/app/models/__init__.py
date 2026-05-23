from app.models.user import User  # noqa: F401 — registers User with Base.metadata
from app.models.project import Project  # noqa: F401 — registers Project with Base.metadata

__all__ = ["User", "Project"]
