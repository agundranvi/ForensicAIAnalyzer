import requests
from pathlib import Path

assets = {
    "bootstrap.min.css": "bootstrap@5.3.3/dist/css/bootstrap.min.css",
    "chart.umd.js": "chart.js@4.4.8/dist/chart.umd.js",
    "cytoscape.min.js": "cytoscape@3.31.0/dist/cytoscape.min.js",
    "vis-timeline.min.js": "vis-timeline@7.7.3/standalone/umd/vis-timeline-graph2d.min.js",
    "vis-timeline.min.css": "vis-timeline@7.7.3/styles/vis-timeline-graph2d.min.css",
}
for name, url in assets.items():
    r = requests.get("https://cdn.jsdelivr.net/npm/" + url, timeout=30)
    r.raise_for_status()
    Path("static/vendor", name).write_bytes(r.content)
    print(name, len(r.content), flush=True)
