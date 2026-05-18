from fastapi import APIRouter

from plugins.registry import plugin_registry

router = APIRouter(prefix="/plugins", tags=["Plugins"])


@router.get("/")
async def list_plugins():
    return {"plugins": plugin_registry.list_plugins()}


@router.get("/marketplace")
async def marketplace():
    return {"plugins": plugin_registry.marketplace()}


@router.post("/discover")
async def discover():
    return {"plugins": plugin_registry.discover()}
