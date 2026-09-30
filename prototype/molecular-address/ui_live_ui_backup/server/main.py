from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Molecular Address Live API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "project": "molecular-address",
        "mode": "digital-dna-storage-simulation",
    }


@app.get("/api/project")
def project():
    root = Path(__file__).resolve().parents[2]

    return {
        "name": "Molecular Address",
        "root": str(root),
        "stages": [
            "input",
            "fragmentation",
            "dna_encoding",
            "molecular_address",
            "redundancy",
            "storage",
            "error_simulation",
            "recovery",
            "verification",
        ],
        "physical_dna_claim": False,
    }
