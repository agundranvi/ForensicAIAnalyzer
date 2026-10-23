"""Enforce a request limit before multipart parsing or temporary-file spooling."""

from starlette.responses import JSONResponse


class BodyLimit:
    def __init__(self, app, limit):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        try:
            size = int(headers.get(b"content-length", b"0"))
        except ValueError:
            size = self.limit + 1
        if size > self.limit:
            return await JSONResponse(
                {"detail": "Request exceeds upload limit"}, status_code=413
            )(scope, receive, send)
        received = 0
        exceeded = False
        started = False

        async def bounded_receive():
            nonlocal received, exceeded
            message = await receive()
            received += len(message.get("body", b""))
            if received > self.limit:
                exceeded = True
                raise ValueError("Request exceeds upload limit")
            return message

        async def bounded_send(message):
            nonlocal started
            if exceeded:
                return
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, bounded_receive, bounded_send)
        except Exception:
            if not exceeded:
                raise
        if exceeded and not started:
            await JSONResponse(
                {"detail": "Request exceeds upload limit"}, status_code=413
            )(scope, receive, send)
