from fastapi import APIRouter

from app.api.v1.companies import router as companies_router
from app.api.v1.discovery import router as discovery_router
from app.api.v1.dossier import router as dossier_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.health import router as health_router
from app.api.v1.outreach import router as outreach_router
from app.api.v1.saved_leads import router as saved_leads_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router)
api_v1_router.include_router(discovery_router)
api_v1_router.include_router(companies_router)
api_v1_router.include_router(evidence_router)
api_v1_router.include_router(saved_leads_router)
api_v1_router.include_router(dossier_router)
api_v1_router.include_router(outreach_router)
