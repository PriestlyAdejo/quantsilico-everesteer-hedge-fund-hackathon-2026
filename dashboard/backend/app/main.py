from fastapi import FastAPI

app = FastAPI(title="QuantSilico × Everesteer 2026 Research Console")


@app.get("/api/health")
def health():
    return {
        "status": "scaffold",
        "service": "QuantSilico Everesteer 2026 Research Console",
        "schema_version": 1,
    }
