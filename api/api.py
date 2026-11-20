import json
from pathlib import Path
from fastapi import FastAPI

app = FastAPI()
DATA = Path("database/data.json")

@app.get("/produits")
def liste_produits():
    return json.loads(DATA.read_text(encoding="utf-8"))["produits"]