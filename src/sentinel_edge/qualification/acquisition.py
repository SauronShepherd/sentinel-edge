"""Declared acquisition-route policy for multimodal evidence."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class AcquisitionRoute(StrEnum):
    SUPPLIED_UPLOAD = "supplied_upload"
    DOCUMENTED_API = "documented_api"
    FIXTURE = "fixture"
    SCRAPE = "scrape"
    ARBITRARY_DOWNLOAD = "arbitrary_download"


class AcquisitionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    route: AcquisitionRoute
    permitted: bool
    code: str
    audit_required: bool = True


def evaluate_acquisition(route: AcquisitionRoute, *, enrolled: bool = False, documented: bool = False) -> AcquisitionDecision:
    permitted = route is AcquisitionRoute.FIXTURE or (
        route is AcquisitionRoute.SUPPLIED_UPLOAD and enrolled
    ) or (route is AcquisitionRoute.DOCUMENTED_API and documented)
    return AcquisitionDecision(route=route, permitted=permitted,
        code="acquisition_permitted" if permitted else "acquisition_not_permitted")
