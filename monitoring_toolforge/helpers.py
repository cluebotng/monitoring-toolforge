import logging
import os
import ssl
from pathlib import PosixPath
from typing import Optional

import aiohttp
import yaml

logger = logging.getLogger(__name__)


def get_client_certificate() -> tuple[PosixPath | None, PosixPath | None]:
    # Local execution
    base_dir = PosixPath("~").expanduser()

    # Production container
    if tool_data_dir := os.environ.get("TOOL_DATA_DIR"):
        base_dir = PosixPath(tool_data_dir)

    client_cert = base_dir / ".toolskube" / "client.crt"
    client_key = base_dir / ".toolskube" / "client.key"
    if client_cert.is_file() and client_key.is_file():
        return client_cert, client_key

    return None, None


def get_http_connector() -> aiohttp.TCPConnector | None:
    client_cert, client_key = get_client_certificate()
    if not client_cert or not client_key:
        return None

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    ssl_context.load_cert_chain(
        certfile=client_cert.as_posix(), keyfile=client_key.as_posix()
    )
    return aiohttp.TCPConnector(ssl=ssl_context)


def get_api_gateway_url() -> str:
    config_path = PosixPath("/etc/toolforge/common.yaml")
    if config_path.is_file():
        with config_path.open("r") as fh:
            data = yaml.loads(fh.read())
            if api_gateway_url := data.get("api_gateway", {}).get("url"):
                return api_gateway_url.rstrip("/")

    return os.environ.get("TOOL_TOOLFORGE_API_URL", "https://localhost:30003").rstrip(
        "/"
    )


def get_kubernetes_namespace() -> Optional[str]:
    namespace_file = PosixPath(
        "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
    )
    if namespace_file.is_file():
        with namespace_file.open("r") as fh:
            return fh.read().strip()
    return None


def get_tool_name() -> str:
    # Local development
    if tool_name := os.environ.get("TOOLFORGE_TOOL_NAME"):
        return tool_name

    # Production container
    if kubernetes_namespace := get_kubernetes_namespace():
        return kubernetes_namespace.removeprefix("tool-")

    raise RuntimeError("Could not determine tool name")
