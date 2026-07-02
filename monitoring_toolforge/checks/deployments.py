import logging

import aiohttp
from prometheus_client import Gauge

from monitoring_toolforge.checks import METRIC_PREFIX

from monitoring_toolforge.helpers import get_http_connector, get_api_gateway_url

logger = logging.getLogger(__name__)

latest_deployment_successful = Gauge(
    f"{METRIC_PREFIX}_components_deployment_latest_successful",
    "Current status of the latest deployment",
    ["tool"],
)

latest_deployment_build_successful = Gauge(
    f"{METRIC_PREFIX}_components_deployment_latest_build_successful",
    "Current status of the latest deployment build",
    ["tool", "build"],
)


async def get_latest_deployment(tool_name: str) -> None:
    async with aiohttp.ClientSession(connector=get_http_connector()) as session:
        async with session.get(
            f"{get_api_gateway_url()}/components/v1/tool/{tool_name}/deployment/latest",
            headers={"User-Agent": "ClueBot NG Monitoring"},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as r:
            if r.status != 200:
                logger.error(
                    f"builds-api returned non 200 status: {r.status}: {await r.text()}"
                )
                return

            response = await r.json()
            latest_deployment_successful.labels(tool=tool_name).set(
                1 if response["data"]["status"] == "successful" else 0
            )
            for build, status in response["data"].get("builds", {}).items():
                latest_deployment_build_successful.labels(
                    tool=tool_name, build=build
                ).set(1 if status["build_status"] in ("successful", "skipped") else 0)
