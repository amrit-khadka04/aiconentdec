import json
import logging

from groq import Groq

from config import settings

logger = logging.getLogger(__name__)

client = Groq(api_key=settings.groq_api_key)

SYSTEM = """You are a forensic video analyst and deepfake detection expert.
Your job is to independently examine video frames for signs of AI generation or
manipulation, drawing on peer-reviewed research (FaceForensics++, Wang et al. 2020,
Frank et al. 2020, Rossler et al. 2019) and your own visual analysis.

IMPORTANT: Do not simply confirm the ML score. Conduct your own independent
visual examination and report what you actually see.

You must respond ONLY in valid JSON — no prose outside the JSON block."""

# Ordered by discriminative power based on research literature
_ARTIFACT_CHECKLIST = """
Known AI/deepfake artifact categories to inspect:
A) SKIN & FACE: unnatural smoothness, waxy/plastic look, inconsistent skin pores,
   over-smooth forehead/cheeks, missing microdetails (pores, fine lines, stubble)
B) EYES: missing or asymmetric catchlight reflections, glassy/unfocused appearance,
   colour bleed at iris boundary, unnaturally perfect iris symmetry
C) HAIR & EDGES: blurred or floating hair strands, fringing artefacts at hair/background
   boundary, unnaturally sharp or soft hair-to-skin transitions
D) LIGHTING: physically impossible shadow directions, flat monotone shadows, missing
   subsurface scattering in skin, colour constancy violations between face and background
E) BACKGROUND: GAN-style blurry or melting background details, repeating or warped
   patterns, inconsistent depth-of-field artefacts
F) TEXTURE & FREQUENCY: checkerboard noise visible at pixel level (GAN upsampling),
   absence of film grain or sensor noise, unnaturally uniform texture patches
G) COLOUR & SATURATION: overly saturated or desaturated palette, colour bleeding
   between regions, unnatural colour uniformity across the scene
H) TEMPORAL/COMPRESSION: JPEG blocking in face region inconsistent with background
   (face was composited), abrupt edge seams around face region
"""


async def explain_frame(
    base64_jpeg: str,
    ai_score: float,
    verdict: str,
    signals: dict,
    timestamp_sec: float,
) -> dict:
    signal_lines = "\n".join(
        f"  - {k.replace('_', ' ').title()}: {v:.2f}"
        for k, v in signals.items()
    )

    prompt = f"""=== FORENSIC ANALYSIS REQUEST ===
Timestamp: {timestamp_sec:.1f}s
ML Model Score: {ai_score:.2f}  (0.0 = definitely human, 1.0 = definitely AI)
ML Verdict: {verdict.upper()}

Forensic signal scores (higher value = more AI-like):
{signal_lines}

{_ARTIFACT_CHECKLIST}

=== YOUR TASK ===
1. Carefully examine the image above for the artifact categories listed.
2. Identify the 2-4 most compelling pieces of visual evidence — be specific
   (mention exact locations: "left cheek", "background behind the subject",
   "hairline at top-right", etc.).
3. Assign each observation to one of the artifact categories (A–H).
4. Give an overall confidence rating for your conclusion:
   - "high"   → clear, unambiguous visual evidence present
   - "medium" → some indicators present but image could be authentic
   - "low"    → weak or ambiguous evidence; hard to tell visually

Return EXACTLY this JSON and nothing else:
{{
  "reasons": [
    "Specific observation 1 with location detail",
    "Specific observation 2 with location detail",
    "Specific observation 3 with location detail"
  ],
  "primary_evidence": "Single most decisive visual indicator with location",
  "artifact_categories": ["X", "Y"],
  "confidence": "high|medium|low"
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
            temperature=0.15,
            max_tokens=600,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content)
        # Normalise keys so downstream code is never broken by missing fields
        return {
            "reasons": data.get("reasons", ["Visual explanation unavailable."]),
            "primary_evidence": data.get("primary_evidence", "No primary evidence identified."),
            "artifact_categories": data.get("artifact_categories", []),
            "confidence": data.get("confidence", "medium"),
        }
    except Exception as e:
        logger.warning("Groq explainer error: %s", e)
        return {
            "reasons": ["Visual explanation unavailable."],
            "primary_evidence": f"Error: {str(e)[:80]}",
            "artifact_categories": [],
            "confidence": "low",
        }
