from __future__ import annotations

import httpx

from app.core.config import settings


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def build_positive_reply_prompt(review_text: str | None, reviewer_name: str | None, business_name: str) -> str:
    review_fragment = review_text or "No review text was provided."
    reviewer_fragment = reviewer_name or "customer"
    return (
        "Write a concise Google Business Profile reply for a positive review.\n"
        "Constraints:\n"
        "- 2 sentences maximum\n"
        "- Professional, warm, and specific\n"
        "- No markdown, no emojis, no quotation marks\n"
        f"- Business name: {business_name}\n"
        f"- Reviewer name: {reviewer_fragment}\n"
        f"- Review text: {review_fragment}\n"
    )


async def generate_positive_reply(review_text: str | None, reviewer_name: str | None, business_name: str) -> str:
    if not settings.gemini_api_key:
        name = reviewer_name or "there"
        return f"Thank you, {name}, for your positive feedback. We appreciate your support and look forward to serving you again."

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": build_positive_reply_prompt(review_text, reviewer_name, business_name),
                    }
                ]
            }
        ]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            GEMINI_URL.format(model=settings.gemini_model),
            params={"key": settings.gemini_api_key},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Gemini response did not include reply text") from exc
