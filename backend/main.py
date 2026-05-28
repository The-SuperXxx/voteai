"""VoteAI 后端入口"""
import uuid
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi import UploadFile, File
from fastapi.staticfiles import StaticFiles
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

# 静态文件目录路径
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")


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
async def history(limit: int = 20, request: Request = None):
    ip = request.client.host if request else ""
    return {"items": database.get_history(limit, ip)}


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
        async for event in run_voting_stream(question, ip):
            yield event

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件，提取文本内容"""
    try:
        content = await file.read()
        filename = file.filename or ""

        if filename.endswith('.docx'):
            import io, docx
            doc = docx.Document(io.BytesIO(content))
            text = '\n'.join([p.text for p in doc.paragraphs])
        elif filename.endswith('.pdf'):
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(content))
                text = '\n'.join([p.extract_text() or '' for p in reader.pages])
            except ImportError:
                return {"error": "PDF 解析未安装", "text": ""}
        else:
            text = content.decode('utf-8', errors='ignore')

        return {"text": text[:5000], "filename": filename, "length": len(text)}
    except Exception as e:
        return {"error": str(e), "text": ""}


# SPA fallback（始终注册路由，运行时检查 dist 是否存在）
@app.get("/")
async def root():
    idx = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(idx):
        return FileResponse(idx)
    return {"detail": "Not Found"}, 404


@app.get("/assets/{path:path}")
async def assets(path: str):
    file_path = os.path.join(FRONTEND_DIR, "assets", path)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"detail": "Not Found"}, 404


@app.get("/{path:path}")
async def spa(path: str):
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(file_path) and not os.path.isdir(file_path):
        return FileResponse(file_path)
    idx = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(idx):
        return FileResponse(idx)
    return {"detail": "Not Found"}, 404


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


def _sse(data: dict) -> str:
    import json
    return json.dumps(data, ensure_ascii=False)
