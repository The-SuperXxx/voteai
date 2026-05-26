"""VoteAI 后端入口"""
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from models import AskRequest, AskResponse
from voting import run_voting, run_voting_stream
from config import config
import database

app = FastAPI(title="VoteAI", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

database.init_db()


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/models")
async def list_models():
    return {
        "models": [{"name": m["name"], "provider": m["base_url"]} for m in config.MODELS]
    }


@app.post("/api/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    question = req.question.strip()
    if not question:
        return AskResponse(
            id="", question="", best_answer="请输入问题",
            best_model="", score=0, votes=[], all_answers=[],
        )

    result = await run_voting(question)
    result_id = str(uuid.uuid4())[:8]

    database.save_result(
        result_id=result_id,
        question=question,
        best_answer=result["best_answer"],
        best_model=result["best_model"],
        score=result["score"],
        votes=result["votes"],
        all_answers=result["all_answers"],
    )

    return AskResponse(
        id=result_id,
        question=question,
        best_answer=result["best_answer"],
        best_model=result["best_model"],
        score=result["score"],
        votes=result["votes"],
        all_answers=result["all_answers"],
    )


@app.get("/api/history")
async def history(limit: int = 20):
    return {"items": database.get_history(limit)}


@app.get("/api/result/{result_id}")
async def get_result(result_id: str):
    result = database.get_result(result_id)
    if result is None:
        return {"error": "not found"}, 404
    return result


@app.delete("/api/result/{result_id}")
async def delete_result(result_id: str):
    database.delete_result(result_id)
    return {"status": "ok"}


@app.get("/api/quota")
async def quota(request: Request):
    ip = request.client.host
    return database.get_quota(ip)


@app.post("/api/ask/stream")
async def ask_stream(req: AskRequest, request: Request):
    ip = request.client.host
    check = database.check_and_increment(ip)
    if not check["allowed"]:
        async def limit_gen():
            yield f"data: {_sse({'type': 'limit', 'message': '今日免费次数已用完(20次)，明天重置'})}\n\n"
        return StreamingResponse(limit_gen(), media_type="text/event-stream")

    question = req.question.strip()
    if not question:
        return StreamingResponse(
            iter([f"data: {{\"type\":\"error\",\"error\":\"empty question\"}}\n\n"]),
            media_type="text/event-stream"
        )

    async def generate():
        async for event in run_voting_stream(question):
            yield event

    return StreamingResponse(generate(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


def _sse(data: dict) -> str:
    import json
    return json.dumps(data, ensure_ascii=False)
