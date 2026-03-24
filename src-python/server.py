# documents avaliable on: https://developers.cloudflare.com/workers/languages/python/
from workers import WorkerEntrypoint, Response

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return Response("Hello World!")
