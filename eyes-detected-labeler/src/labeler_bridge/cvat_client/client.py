import json, os
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlsplit
from urllib.error import URLError, HTTPError


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class CVATClient:
    """Explicit local API adapter. No credentials in diagnostics or automatic image upload."""

    def __init__(self, base_url=None, token=None, timeout=10):
        self.base = (base_url or os.environ.get("CVAT_URL", "http://localhost:8080")).rstrip("/")
        u = urlsplit(self.base)
        if u.scheme not in ["http", "https"] or u.username or u.password or u.query or u.fragment:
            raise ValueError("Invalid CVAT base URL")
        if u.hostname not in ["localhost", "127.0.0.1", "host.docker.internal", "cvat_server"]:
            raise ValueError("Starter CVAT transport is restricted to explicit local deployment")
        self.token = token or os.environ.get("CVAT_TOKEN", "")
        self.timeout = timeout

    def request(self, method, path, data=None):
        if not path.startswith("/api/") or ".." in path:
            raise ValueError("Invalid API path")
        req = Request(
            self.base + path,
            data=json.dumps(data).encode() if data is not None else None,
            method=method,
            headers={
                "Content-Type": "application/json",
                **({"Authorization": "Token " + self.token} if self.token else {}),
            },
        )
        try:
            with build_opener(NoRedirect).open(req, timeout=self.timeout) as r:
                body = r.read()
                return json.loads(body) if body else {}
        except (URLError, HTTPError, TimeoutError, OSError):
            raise RuntimeError(
                "CVAT request failed. Start local CVAT, verify URL/token and API version; no annotation success recorded."
            ) from None

    def health(self):
        return self.request("GET", "/api/server/about")

    def create_project(self, spec):
        return self.request("POST", "/api/projects", spec)

    def create_task(self, name, project_id):
        return self.request("POST", "/api/tasks", {"name": name, "project_id": project_id})

    def get_annotations(self, task_id):
        return self.request("GET", f"/api/tasks/{int(task_id)}/annotations")

    def import_annotations(self, task_id, payload):
        return self.request("PATCH", f"/api/tasks/{int(task_id)}/annotations?action=create", payload)
