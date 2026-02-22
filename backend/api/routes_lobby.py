from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .websocket_handler import manager

router = APIRouter(tags=["multiplayer"])


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    conn_id = await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            await manager.handle_message(conn_id, data)
    except WebSocketDisconnect:
        await manager.disconnect(conn_id)
    except Exception:
        await manager.disconnect(conn_id)
