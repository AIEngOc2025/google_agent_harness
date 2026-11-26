import importlib.util
import logging
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

if importlib.util.find_spec("harbor") is not None:
    from kit.harbor_docker import KitDockerEnvironment


@unittest.skipUnless(importlib.util.find_spec("harbor") is not None, "Harbor is not installed")
class SidecarPlatformTests(unittest.IsolatedAsyncioTestCase):
    async def test_build_uses_compose_platform(self):
        environment = KitDockerEnvironment.__new__(KitDockerEnvironment)
        environment._env_vars = SimpleNamespace()
        environment.logger = logging.getLogger(__name__)
        with (
            patch.object(environment, "_compose_env_vars", return_value={"DOCKER_DEFAULT_PLATFORM": "linux/amd64"}),
            patch("kit.harbor_docker.ensure_docker_image_built", new_callable=AsyncMock, return_value="amd64-image") as build,
        ):
            await environment._ensure_egress_control_sidecar_image_built()
        self.assertEqual(build.await_args.kwargs["platform"], "linux/amd64")
        self.assertEqual(environment._env_vars.egress_control_sidecar_image_name, "amd64-image")

    async def test_without_compose_platform_uses_harbor_default(self):
        environment = KitDockerEnvironment.__new__(KitDockerEnvironment)
        with (
            patch.object(environment, "_compose_env_vars", return_value={}),
            patch("harbor.environments.docker.docker.DockerEnvironment._ensure_egress_control_sidecar_image_built", new_callable=AsyncMock) as fallback,
        ):
            await environment._ensure_egress_control_sidecar_image_built()
        fallback.assert_awaited_once()
