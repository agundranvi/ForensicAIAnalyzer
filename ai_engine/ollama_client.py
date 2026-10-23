"""Loopback-only Ollama transport; never inherit proxies or follow redirects."""

import requests


def post(payload):
    with requests.Session() as session:
        session.trust_env = False
        response = session.post(
            "http://127.0.0.1:11434/api/chat",
            json=payload,
            timeout=180,
            allow_redirects=False,
        )
        if response.status_code != 200:
            raise requests.RequestException(
                "Local Ollama returned an unsuccessful response"
            )
        return response
