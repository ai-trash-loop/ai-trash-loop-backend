"""Write openapi.json (the frontend generates its TypeScript types from it)."""
import json
from pathlib import Path

from app.config import Settings
from app.main import create_app

app = create_app(Settings(database_url="sqlite://"))
Path(__file__).resolve().parent.parent.joinpath("openapi.json").write_text(json.dumps(app.openapi(), indent=2) + "\n")
print("wrote openapi.json")
