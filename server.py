import hashlib
import hmac
import os
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from RAG import ask as rag_ask
from store import get_embeddings
from langchain_chroma import Chroma
from agent import triage_issue, get_github

PERSIST_DIR = "data/chroma"
app = FastAPI(title="DevMate")



class Askrequest(BaseModel):
    question : str



@app.post("/ask")
def ask_endpoint(req:Askrequest):
    embeddings = get_embeddings()
    db = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)
    result = rag_ask(db, req.question)
    return result


class TriageRequest(BaseModel):
    repo_full_name: str
    issue_number: int


@app.post("/triage")
def Triage_endpoint(req:TriageRequest):
    result = triage_issue(req.repo_full_name, req.issue_number)
    return result.model_dump()




def verify_signature(payload_body: bytes, signature_header: str, secret: str) -> bool:
    if not signature_header:
        return False

    expected = "sha256=" + hmac.new(
        secret.encode(), payload_body, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature_header)




@app.post("/webhooks/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    payload_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    secret = os.getenv("WEBHOOK_SECRET")

    if not verify_signature(payload_body, signature, secret):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event")

    if event_type == "issues" and payload.get("action") == "opened":
        repo_full_name = payload["repository"]["full_name"]
        issue_number = payload["issue"]["number"]

        background_tasks.add_task(handle_new_issue, repo_full_name, issue_number)

    return {"status": "received"}



def handle_new_issue(repo_full_name: str, issue_number: int):
    result = triage_issue(repo_full_name, issue_number)

    comment = (
        f"**DevMate Triage**\n\n"
        f"Label: `{result.label}`\n"
        f"Priority: `{result.priority}`\n\n"
        f"Reasoning: {result.reasoning}"
    )

    gh = get_github()
    repo = gh.get_repo(repo_full_name)
    issue = repo.get_issue(number=issue_number)
    issue.create_comment(comment)



     