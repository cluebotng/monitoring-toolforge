import logging
import os

from prometheus_client import Gauge

from monitoring_toolforge.checks import METRIC_PREFIX

# asyncmy tries to lookup the current username using pwd.getpwuid to use as the default
# since we don't have a proper user in the container this raises.. just patch it for now
import getpass

getpass.getuser = lambda: "yolo"

from asyncmy import connect  # noqa

logger = logging.getLogger(__name__)

wiki_replica_lag = Gauge(
    f"{METRIC_PREFIX}_service_database_wiki_replica_lag",
    "Current status of a build",
    ["shard", "cluster"],
)


async def get_wiki_replica_lag(shard: str, cluster: str = "analytics") -> None:
    database_user = os.environ.get("TOOL_REPLICA_USER")
    database_password = os.environ.get("TOOL_REPLICA_PASSWORD")
    if not database_user or not database_password:
        logger.error("Missing TOOL_REPLICA_USER / TOOL_REPLICA_PASSWORD")
        return

    async with connect(
        host=f"{shard}.{cluster}.db.svc.wikimedia.cloud",
        user=database_user,
        password=database_password,
        echo=True,
    ) as connection:
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT lag FROM heartbeat_p.heartbeat")
            if row := await cursor.fetchone():
                wiki_replica_lag.labels(shard=shard, cluster=cluster).set(row[0])
