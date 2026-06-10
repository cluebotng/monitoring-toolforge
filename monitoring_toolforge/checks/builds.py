import logging

import aiohttp
from prometheus_client import Gauge

from monitoring_toolforge.checks import METRIC_PREFIX

from monitoring_toolforge.helpers import get_http_connector, get_api_gateway_url

logger = logging.getLogger(__name__)

build_successful = Gauge(
    f"{METRIC_PREFIX}_builds_build_successful",
    "Current status of a build",
    ["tool", "image"],
)


async def get_current_builds(tool_name: str) -> None:
    async with aiohttp.ClientSession(connector=get_http_connector()) as session:
        async with session.get(
            f"{get_api_gateway_url()}/builds/v1/tool/{tool_name}/builds",
            headers={"User-Agent": "ClueBot NG Monitoring"},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as r:
            if r.status != 200:
                logger.error(
                    f"builds-api returned non 200 status: {r.status}: {await r.text()}"
                )
                return

            data = await r.json()
            for job in data.get("builds", []):
                build_successful.labels(
                    tool=tool_name, image=job["parameters"]["image_name"]
                ).set(1 if job["status"] == "BUILD_SUCCESS" else 0)
