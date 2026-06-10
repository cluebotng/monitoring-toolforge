import logging

import aiohttp
from prometheus_client import Gauge

from monitoring_toolforge.checks import METRIC_PREFIX

from monitoring_toolforge.helpers import get_http_connector, get_api_gateway_url

logger = logging.getLogger(__name__)

job_running = Gauge(
    f"{METRIC_PREFIX}_jobs_job_running",
    "Current status of a job",
    ["tool", "job"],
)


async def get_current_jobs(tool_name: str) -> None:
    async with aiohttp.ClientSession(connector=get_http_connector()) as session:
        async with session.get(
            f"{get_api_gateway_url()}/jobs/v1/tool/{tool_name}/jobs/",
            headers={"User-Agent": "ClueBot NG Monitoring"},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as r:
            if r.status != 200:
                logger.error(
                    f"jobs-api returned non 200 status: {r.status}: {await r.text()}"
                )
                return

            data = await r.json()
            for job in data.get("jobs", []):
                job_running.labels(tool=tool_name, job=job["name"]).set(
                    1 if job["status"]["short"] == "running" else 0
                )
