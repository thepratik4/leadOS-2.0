from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.dossier import CompanyDossierResponse
from app.services.dossier_service import dossier_service

router = APIRouter(prefix="/companies/{company_id}/dossier", tags=["Dossier"])


@router.get("", response_model=CompanyDossierResponse)
async def get_company_dossier(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        dossier = await dossier_service.generate_dossier(db=db, company_id=company_id)
        return dossier
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dossier: {e!s}",
        )
