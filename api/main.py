from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict
import sys
from typing import List


# importing toxicity model for toxicity prediction 
from toxicity_model.app import predict
import httpx  # Import the HTTP client
from extract_pure_comments import extract_comments



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


class Texts(BaseModel):
    texts: List[str]


@app.post("/ingest")
async def ingest(payload: IngestPayload):
	print("==> RECEIVED REDDIT POST PAYLOAD", file=sys.stdout, flush=True)

	# Just print the payload to console
	print(payload.model_dump_json(indent=2), file=sys.stdout, flush=True)
	
	# extract pure comments from payload
	comments = extract_comments(payload.model_dump())
	predict_payload = {"texts": comments}  # prepared payload for /predict endpoint

    # Call the /predict endpoint fro predictions
	async with httpx.AsyncClient() as client:
		response = await client.post("http://127.0.0.1:8000/predict", json=predict_payload)
		predictions = response.json()
	print(predictions)


	return {"status": "ok"}




# APIs for predicting list of comments and a single comment. 
@app.post("/predict")
def predict_output(comments: Texts):
	return predict(comments)




@app.get("/health")
async def health():
	return {"status": "healthy"}
