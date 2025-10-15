from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict
import sys

app = FastAPI(title="Reddit Ingest API")

# Allow extension pages and localhost to call us.
origins = [
	"http://localhost",
	"http://127.0.0.1:8000",
	# Chrome extension origins are dynamic (chrome-extension://<id>), so for local dev
	# we allow all. Tighten this in production.
	"*",
]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


class IngestPayload(BaseModel):
	filename: str
	data: Dict[str, Any]


@app.post("/ingest")
async def ingest(payload: IngestPayload):
	print("===== RECEIVED REDDIT POST PAYLOAD =====", file=sys.stdout, flush=True)
	print(payload.model_dump_json(indent=2), file=sys.stdout, flush=True)
	return {"status": "ok"}


@app.get("/health")
async def health():
	return {"status": "healthy"}
