"""模型列表与手动加载。"""
from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_current_user
from ..llm.registry import registry
from ..resp import ok

router = APIRouter(prefix="/api/models", tags=["模型"])


@router.get("")
def list_models(_=Depends(get_current_user)):
    return ok(registry.scan())


@router.post("/{model_id}/load")
async def load_model(model_id: str, _=Depends(get_current_user)):
    if model_id == "remote":
        return ok(registry.scan()[0], "远端模型无需加载")
    try:
        await registry.ensure_loaded(model_id)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "模型不存在")
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))
    return ok(next(m for m in registry.scan() if m["id"] == model_id), "加载完成")
