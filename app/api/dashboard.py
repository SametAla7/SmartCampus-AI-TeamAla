"""Routes - Tableau de bord."""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import bad_request
from app.db.session import Session, get_db
from app.models.user import User
from app.schemas.dashboard import DashboardExportFormat, DashboardStats
from app.services.dashboard_service import build_dashboard_export, get_dashboard

router = APIRouter(prefix="/dashboard", tags=["Tableau de bord"])


@router.get("/stats", response_model=DashboardStats, summary="Statistiques du tableau de bord")
def get_dashboard_stats_endpoint(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DashboardStats:
    return get_dashboard(db, user)


@router.get("/export")
def export_dashboard(
    format: str = Query(default=DashboardExportFormat.PDF.value, description="Export format: pdf | xlsx"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    stats = get_dashboard(db, user)
    content, media_type, filename = build_dashboard_export(stats, format)
    return Response(content=content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})
