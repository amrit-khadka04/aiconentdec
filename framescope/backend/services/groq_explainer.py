import json
import logging

from groq import Groq

from config import settings

logger = logging.getLogger(__name__)

client = Groq(api_key=settings.groq_api_key)

SYSTEM = """You are a forensic video analyst writing evidence reports.
You receive an ML detector's score and forensic signals
for a video frame. You look at the image and write specific
natural language sentences describing what you visually observe
that is consistent with the ML verdict.
You never produce a score. Respond ONLY in valid JSON."""


async def explain_frame(
    base64_jpeg: str,
    ai_score: float,
    verdict: str,
    signals: dict,
    timestamp_sec: float,
) -> dict:
    prompt = f"""ML Detection Score: {ai_score:.2f} (0=human, 1=AI)
Verdict: {verdict.upper()}
Timestamp: {timestamp_sec:.1f}s

Forensic signals (higher = more AI-like):
- Texture uniformity: {signals['texture_uniformity']:.2f}
- Noise level: {signals['noise_level']:.2f}
- Frequency artifact: {signals['frequency_artifact']:.2f}
- Color uniformity: {signals['color_uniformity']:.2f}

Look at this image. Write 2-4 sentences describing specific
visual characteristics consistent with the verdict "{verdict}".
Be specific about textures, edges, lighting, skin, hair,
backgrounds you actually see in this frame.

Return ONLY this JSON:
{{
  "reasons": ["observation 1", "observation 2", "observation 3"],
  "primary_evidence": "single strongest visual indicator"
}}"""

    try:
        resp = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": SYSTEM},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_jpeg}"
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                },
            ],
            temperature=0.3,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        logger.warning("Groq explainer error: %s", e)
        return {
            "reasons": ["Visual explanation unavailable."],
            "primary_evidence": f"Error: {str(e)[:80]}",
        }
