"""AI API 调用封装 - 使用 OpenAI 兼容 SDK"""
import asyncio
import json
import re
from openai import AsyncOpenAI
from config import config


def _get_client(model_cfg: dict) -> AsyncOpenAI:
    """根据模型配置创建 OpenAI 客户端"""
    return AsyncOpenAI(
        api_key=model_cfg["api_key"],
        base_url=model_cfg["base_url"],
        timeout=config.VOTING_TIMEOUT,
    )


async def ask_one(model_cfg: dict, question: str, retries: int = 0) -> str:
    """向单个 AI 发送问题，获取回答（非流式，用于投票评分）"""
    client = _get_client(model_cfg)
    try:
        response = await client.chat.completions.create(
            model=model_cfg["model_id"],
            messages=[{"role": "user", "content": question}],
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        if retries < config.MAX_RETRIES:
            await asyncio.sleep(1)
            return await ask_one(model_cfg, question, retries + 1)
        return f"[错误] {model_cfg['name']} 调用失败: {str(e)}"


async def ask_one_stream(model_cfg: dict, question: str, queue: asyncio.Queue):
    """流式向单个 AI 提问，通过 queue 推送 token"""
    model_name = model_cfg["name"]
    client = _get_client(model_cfg)
    full_text = ""
    try:
        stream = await client.chat.completions.create(
            model=model_cfg["model_id"],
            messages=[{"role": "user", "content": question}],
            temperature=0.7,
            max_tokens=1024,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                token = delta.content
                full_text += token
                await queue.put({"type": "token", "model": model_name, "token": token})
        await queue.put({"type": "done", "model": model_name, "answer": full_text})
    except Exception as e:
        err_msg = f"[{model_name} 调用失败] {str(e)}"
        await queue.put({"type": "token", "model": model_name, "token": err_msg})
        await queue.put({"type": "done", "model": model_name, "answer": err_msg})


async def ask_all(question: str) -> dict[str, str]:
    """并发向所有 AI 提问，返回 {模型名: 回答}"""
    tasks = [ask_one(m, question) for m in config.MODELS]
    answers = await asyncio.gather(*tasks)
    return {m["name"]: ans for m, ans in zip(config.MODELS, answers)}


async def score_answers(model_cfg: dict, question: str, answers: dict[str, str], retries: int = 0) -> dict[str, int]:
    """让一个 AI 给所有回答打分"""
    client = _get_client(model_cfg)
    answer_list = "\n\n".join(
        f"【{name}的回答】\n{ans}"
        for name, ans in answers.items()
    )
    prompt = f"""原始问题：{question}

以下是三个AI对上述问题的回答：

{answer_list}

请分别给三个AI的回答打分（1-10分）。
只输出JSON格式，不要任何解释：
{{"DeepSeek-R1": 8, "Qwen3-8B": 7, "GLM-4-Flash": 9}}"""

    try:
        response = await client.chat.completions.create(
            model=model_cfg["model_id"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200,
        )
        text = response.choices[0].message.content or ""
        return _parse_scores(text, list(answers.keys()))
    except Exception as e:
        if retries < config.MAX_RETRIES:
            await asyncio.sleep(1)
            return await score_answers(model_cfg, question, answers, retries + 1)
        return {name: 5 for name in answers}


async def synthesize_answer(model_cfg: dict, question: str, answers: dict[str, str]) -> str:
    """综合多个AI的回答，提取精华合成新答案"""
    client = _get_client(model_cfg)
    answer_list = "\n\n".join(
        f"【{name}的回答】\n{ans}"
        for name, ans in answers.items()
    )
    prompt = f"""你是一个内容综合专家。用户的问题是：

{question}

以下是三个AI对该问题的回答：

{answer_list}

请综合以上三个回答，提炼出一份全面、准确的最终答案。要求：
1. 提取所有回答中的共识点和关键信息
2. 保留各模型独特的洞见
3. 去掉重复和冗余内容
4. 结构清晰、语言流畅
5. 在文末标注关键信息分别来源于哪个模型

直接输出综合后的答案，不要加"综合答案："之类的标题。"""

    try:
        response = await client.chat.completions.create(
            model=model_cfg["model_id"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1500,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        return f"[合成失败] {str(e)}"


def _parse_scores(text: str, model_names: list[str]) -> dict[str, int]:
    """从 AI 返回的文本中解析评分 JSON"""
    try:
        scores = json.loads(text)
        return {m: int(scores.get(m, 5)) for m in model_names}
    except (json.JSONDecodeError, ValueError):
        pass
    scores = {}
    for name in model_names:
        pattern = rf'{name}[":\s]+(\d+)'
        match = re.search(pattern, text)
        scores[name] = int(match.group(1)) if match else 5
    return scores
