import json
from pathlib import Path
from fastapi import FastAPI

app = FastAPI()
DATA = Path("database/data.json")
DATA_ROOT = Path("database/root.json")

@app.get("/root")
def root_page():
    return json.loads(DATA_ROOT.read_text(encoding="utf-8"))["root"]

@app.get("/produits")
def liste_produits():
    return json.loads(DATA.read_text(encoding="utf-8"))["produits"]