import aiohttp

from typing import Any, Dict, Optional
from fastapi import HTTPException

#NOT USED BUT IF IT"S GOOD WE CAN USE IT 
async def make_async_request(
    url: str,
    method: str = "POST",
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Generic aiohttp request handler with error handling.

    Args:
        url: Target URL
        method: HTTP method (GET/POST/PUT/DELETE)
        payload: Request body data
        headers: Custom headers
        timeout: Timeout in seconds

    Returns:
        JSON response as dict

    Raises:
        HTTPException: On request failure
    """
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.request(
                method=method,
                url=url,
                json=payload,
            ) as response:

                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=502,
                        detail=f"Remote API error ({response.status}): {error_text}",
                    )

                return await response.json()

    except ValueError as e:
        raise HTTPException(400, detail=f"Invalid request data: {str(e)}")
    except aiohttp.ClientError as e:
        raise HTTPException(503, detail=f"Service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(500, detail=f"Unexpected error: {str(e)}")


async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
