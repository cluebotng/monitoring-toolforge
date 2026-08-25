import asyncio
import logging

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from prometheus_client import (
    REGISTRY,
    GC_COLLECTOR,
    PROCESS_COLLECTOR,
    PLATFORM_COLLECTOR,
)

from monitoring_toolforge.checks.builds import get_current_builds
from monitoring_toolforge.checks.deployments import get_latest_deployment
from monitoring_toolforge.checks.services.wiki_replica import get_wiki_replica_lag
from monitoring_toolforge.helpers import get_tool_name
from monitoring_toolforge.checks.jobs import get_current_jobs

logger = logging.getLogger(__name__)


class PrometheusResponse(Response):
    media_type = CONTENT_TYPE_LATEST


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    # Disable the default metrics
    REGISTRY.unregister(GC_COLLECTOR)
    REGISTRY.unregister(PROCESS_COLLECTOR)
    REGISTRY.unregister(PLATFORM_COLLECTOR)


@app.get("/metrics", response_class=PrometheusResponse)
async def _render_metrics():
    tool_name = get_tool_name()
    await asyncio.gather(
        get_current_jobs(tool_name),
        get_current_builds(tool_name),
        get_latest_deployment(tool_name),
        get_wiki_replica_lag("s1"),  # enwiki_p is in s1
    )
    return generate_latest()


@app.get("/health")
async def _render_health():
    return "OK"
