from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import aiohttp

# Assume these are defined/imported
from utils.queues import (
    queue_migration,
    queue_gain_before,
)


router = APIRouter()


@router.post("/prom/migration/decisions4")
async def start_migration(run_migration: bool = False):
    if not run_migration:
        queue_migration.empty_queue()
        queue_gain_before.empty_queue()
        return {"message": "Migration declined"}
    async def forward_stream():
        async with aiohttp.ClientSession() as session:
            async with session.post("http://10.150.1.200:5000/run-migration") as response:
                async for chunk in response.content.iter_any():
                    yield chunk
    return StreamingResponse(
        forward_stream(),
        media_type="text/event-stream"
    )

