"""智能体协作 - 多AI回答 + 综合合成"""
import asyncio
import uuid
from config import config
from ai_clients import ask_all, ask_one_stream, synthesize_answer
import database


async def run_voting(question: str) -> dict:
    """执行完整流程：提问 → 综合合成 → 返回（非流式）"""
    answers = await ask_all(question)
    synthesized = await synthesize_answer(config.MODELS[0], question, answers)
    return _build_result(answers, synthesized)


async def run_voting_stream(question: str):
    """执行流式流程：提问(流式) → 合成 → 通过 SSE 推送"""
    queue = asyncio.Queue()
    result_id = str(uuid.uuid4())[:8]

    # 启动流式提问
    tasks = [asyncio.create_task(ask_one_stream(m, question, queue)) for m in config.MODELS]

    # 收集完整答案
    answers = {}
    done_count = 0

    while done_count < len(config.MODELS):
        event = await queue.get()
        if event["type"] in ("token", "done"):
            yield f"data: {_sse(event)}\n\n"
        if event["type"] == "done":
            answers[event["model"]] = event["answer"]
            done_count += 1

    # 合成
    yield f"data: {_sse({'type': 'status', 'status': 'synthesizing'})}\n\n"
    await asyncio.gather(*tasks)

    synthesized = await synthesize_answer(config.MODELS[0], question, answers)
    result = _build_result(answers, synthesized)

    database.save_result(
        result_id=result_id,
        question=question,
        best_answer=result["best_answer"],
        best_model=result["best_model"],
        score=result["score"],
        votes=result["votes"],
        all_answers=result["all_answers"],
    )

    yield f"data: {_sse({'type': 'result', 'id': result_id, **result})}\n\n"


def _build_result(answers: dict, synthesized: str) -> dict:
    """构建最终结果"""
    model_names = [m["name"] for m in config.MODELS]
    all_answers_list = [
        {"model": name, "answer": answers[name], "avg_score": 0}
        for name in model_names
    ]
    return {
        "best_answer": synthesized,
        "best_model": "综合合成",
        "score": 0,
        "votes": [],
        "all_answers": all_answers_list,
    }


def _sse(data: dict) -> str:
    import json
    return json.dumps(data, ensure_ascii=False)
