import os
import sys

from fastapi import APIRouter, Query

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from ai_service.gateway.health import build_ai_health_report

router = APIRouter()


@router.get("/ai")
async def health_ai(
    probe: bool = Query(
        False,
        description="If true, sends a minimal live request to each configured provider.",
    ),
):
    """
    AI gateway health: configured providers, fallback chain, router readiness.
    Use ?probe=true for live connectivity checks (may incur API usage).
    """
    return await build_ai_health_report(probe=probe)
