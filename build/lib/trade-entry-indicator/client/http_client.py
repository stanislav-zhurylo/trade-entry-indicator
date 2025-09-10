import aiohttp

from aiocache import cached

@cached(ttl=60)  # Cache the result for 60 seconds
async def execute_http_request(method: str, url: str, payload=None, headers=None):
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, json=payload, headers=headers) as response:
            return await response.json()