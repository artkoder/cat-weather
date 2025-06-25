import aiohttp

class SchedulerBot:
    def __init__(self, token: str):
        self.token = token
        self.session = aiohttp.ClientSession()
        self.api_url = f"https://api.telegram.org/bot{token}"

    async def api_request(self, method: str, data: dict | None = None) -> dict:
        async with self.session.post(f"{self.api_url}/{method}", json=data) as resp:
            resp.raise_for_status()
            return await resp.json()

