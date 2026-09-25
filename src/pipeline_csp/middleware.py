"""Middleware, die `{{ form.media }}` in allen Templates ein CSP-Nonce gibt."""

from asgiref.sync import iscoroutinefunction, markcoroutinefunction

from pipeline_csp.media import _current_request, install


class MediaNonceMiddleware:
    """Setzt das Nonce des Requests in jedes von `Media` gerenderte `<link>` und `<script>`.

    Muss in `MIDDLEWARE` hinter der CSP-Middleware stehen. Beim Laden wird
    `Media.render_css` und `Media.render_js` einmalig umhuellt; waehrend eines Requests haelt eine
    ContextVar den Request, aus dem der Patch das Nonce liest. So bekommen auch
    Templates von Fremdpaketen und das Admin das Nonce, ohne sie anzupassen.

    Es werden nur Tags veraendert, die `Media` aus Python-Code erzeugt, nie die
    gesamte Response: per XSS eingeschleustes HTML bekommt kein Nonce.
    """

    sync_capable = True
    async_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        install()
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

    def __call__(self, request):
        if iscoroutinefunction(self):
            return self.__acall__(request)
        token = _current_request.set(request)
        try:
            return self.get_response(request)
        finally:
            _current_request.reset(token)

    async def __acall__(self, request):
        token = _current_request.set(request)
        try:
            return await self.get_response(request)
        finally:
            _current_request.reset(token)
