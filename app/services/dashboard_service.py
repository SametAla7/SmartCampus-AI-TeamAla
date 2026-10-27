"""Service - Tableau de bord (statistiques calculees depuis la base)."""

from datetime import datetime
from io import BytesIO
from typing import Optional
from uuid import UUID

from sqlalchemy import func

from app.core.errors import bad_request, forbidden
from app.db.session import Session
from app.models.candidature import Candidature
from app.models.entretien import Entretien
from app.models.parcours import Parcours
from app.models.user import User, UserRole
from app.schemas.dashboard import DashboardEvolutionItem, DashboardParcoursItem, DashboardStats, DashboardExportFormat


def get_dashboard_stats(db: Session) -> DashboardStats:
    """Calcule les indicateurs a partir des donnees reellement enregistrees."""
    total = int(db.query(Candidature).count())

    par_statut_rows = (
        db.query(Candidature.statut, func.count(Candidature.id))
        .group_by(Candidature.statut)
        .all()
    )
    par_statut = {
        (statut.value if hasattr(statut, "value") else str(statut)): int(count)
        for statut, count in par_statut_rows
    }

    par_parcours_rows = (
        db.query(Parcours, func.count(Candidature.id))
        .join(Candidature, Candidature.parcours_id == Parcours.id)
        .group_by(Parcours.id)
        .all()
    )
    parcours_items = [
        DashboardParcoursItem(
            parcours_id=str(parcours.id),
            nom=parcours.nom,
            etablissement=parcours.etablissement.value if hasattr(parcours.etablissement, "value") else str(parcours.etablissement),
            total=int(count),
        )
        for parcours, count in par_parcours_rows
    ]

    nb_entretiens = int(db.query(Entretien).count())

    evolution: list[DashboardEvolutionItem] = []
    counts_by_month: dict[str, int] = {}
    for candidature in db.query(Candidature).all():
        date_depot = candidature.date_depot
        if date_depot is None:
            continue
        key = f"{date_depot.year:04d}-{date_depot.month:02d}"
        counts_by_month[key] = counts_by_month.get(key, 0) + 1
    evolution = [DashboardEvolutionItem(mois=key, total=count) for key, count in sorted(counts_by_month.items())]

    return DashboardStats(
        total_candidatures=total,
        candidatures_par_statut=par_statut,
        candidatures_par_parcours=parcours_items,
        nombre_entretiens=nb_entretiens,
        evolution=evolution,
    )


def get_dashboard(db: Session, user: User) -> DashboardStats:
    if user.role != UserRole.DIRECTION and user.role != UserRole.ADMINISTRATEUR:
        raise forbidden("FORBIDDEN_DASHBOARD", "Seul un utilisateur de la direction peut consulter le tableau de bord.")
    return get_dashboard_stats(db)


def build_dashboard_export(stats: DashboardStats, export_format: str) -> tuple[bytes, str, str]:
    """Genere un export PDF ou XLSX a partir des statistiques reelles."""
    if export_format == DashboardExportFormat.PDF.value:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        rows = [
            ["Indicateur", "Valeur"],
            ["Candidatures totales", str(stats.total_candidatures)],
            ["Entretiens", str(stats.nombre_entretiens)],
        ]
        for statut, count in stats.candidatures_par_statut.items():
            rows.append([f"Statut : {statut}", str(count)])
        for item in stats.candidatures_par_parcours:
            rows.append([f"Parcours : {item.nom}", str(item.total)])
        table = Table(rows)
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 1, "#000000"), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]))
        doc.build([Paragraph("SmartCampus AI - Tableau de bord", styles["Title"]), table])
        content = buffer.getvalue()
        return content, "application/pdf", "smartcampus_dashboard.pdf"

    if export_format == DashboardExportFormat.XLSX.value:
        import openpyxl

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.append(["Indicateur", "Valeur"])
        worksheet.append(["Candidatures totales", stats.total_candidatures])
        worksheet.append(["Nombre d'entretiens", stats.nombre_entretiens])
        for statut, count in stats.candidatures_par_statut.items():
            worksheet.append([f"Statut : {statut}", count])
        for item in stats.candidatures_par_parcours:
            worksheet.append([f"Parcours : {item.nom}", item.total])
        output = BytesIO()
        workbook.save(output)
        content = output.getvalue()
        return content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "smartcampus_dashboard.xlsx"

    raise bad_request("EXPORT_FORMAT_INVALID", "Format d'export non supporte. Utiliser 'pdf' ou 'xlsx'.")
