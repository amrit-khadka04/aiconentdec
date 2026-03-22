import json
import logging

from groq import Groq

from config import settings

logger = logging.getLogger(__name__)

client = Groq(api_key=settings.groq_api_key)

SYSTEM = """You are a forensic video analyst and deepfake/AI-generation detection expert.
Your job is to independently examine video frames for signs of AI generation or
manipulation, drawing on the latest peer-reviewed research including:
- FaceForensics++ (Rossler et al., 2019)
- CNNDetection / Universal Fake Detector (Wang et al., 2020)
- Spectral artifacts in GAN images (Frank et al., 2020; Durall et al., 2020)
- Diffusion model fingerprints (Corvi et al., 2023; Ricker et al., 2024)
- DIRE: Diffusion Reconstruction Error detection (Wang et al., 2023)
- GenImage benchmark (Zhu et al., 2024)
- AI-generated video detection (Zhong et al., 2024; VideoFact, 2024)
- Temporal artifact analysis in AI video (Liu et al., 2024)

IMPORTANT: Do not simply confirm the ML score. Conduct your own independent
visual examination and report what you actually see.  Modern AI video generators
(Sora, Runway ML, Pika, Kling, HailuoAI, Lumiere, Stable Video Diffusion) leave
distinct artifacts that differ from classical GAN deepfakes — look for diffusion-
specific artifacts (over-smooth textures, impossible physics, semantic drift) in
addition to traditional deepfake markers.

You must respond ONLY in valid JSON — no prose outside the JSON block."""

# Ordered by discriminative power based on research literature
_ARTIFACT_CHECKLIST = """
Known AI/deepfake artifact categories to inspect:
A) SKIN & FACE: unnatural smoothness, waxy/plastic look, inconsistent skin pores,
   over-smooth forehead/cheeks, missing microdetails (pores, fine lines, stubble),
   unnaturally perfect symmetry typical of diffusion face generators
B) EYES: missing or asymmetric catchlight reflections, glassy/unfocused appearance,
   colour bleed at iris boundary, unnaturally perfect iris symmetry, extra/missing
   eyelashes or eyelashes that blend into the skin
C) HAIR & EDGES: blurred or floating hair strands, fringing artefacts at hair/background
   boundary, hair that appears painted rather than individually rendered, unnaturally
   perfect highlights, spaghetti strands or merged clumps
D) LIGHTING: physically impossible shadow directions, flat monotone shadows, missing
   subsurface scattering in skin, colour constancy violations between face and background,
   ambient occlusion that defies the scene geometry
E) BACKGROUND: GAN-style blurry or melting background details, repeating or warped
   patterns, inconsistent depth-of-field artefacts, objects that partially melt into
   surroundings, impossible scene geometry
F) TEXTURE & FREQUENCY: checkerboard noise visible at pixel level (GAN upsampling),
   absence of film grain or sensor noise, unnaturally uniform texture patches, diffusion
   over-smoothing that removes natural micro-texture
G) COLOUR & SATURATION: overly saturated or desaturated palette, colour bleeding
   between regions, unnatural colour uniformity, hue shifts in skin tones inconsistent
   with scene lighting, flattened saturation range typical of AI colour grading
H) TEMPORAL/COMPRESSION: JPEG blocking in face region inconsistent with background
   (face was composited), abrupt edge seams around face region, inconsistent noise
   across image quadrants indicating compositing
I) DIFFUSION-SPECIFIC: over-smooth surfaces with missing real-world imperfections,
   semantic inconsistencies (objects that don't make physical sense), hands with wrong
   finger count or merged fingers, text that is unreadable or garbled, accessories
   that partially disappear or morph at frame edges
J) PHYSICS & MOTION: clothing or fabric with impossible folds, water/fire/smoke with
   unnatural behaviour, motion blur that doesn't correspond to subject movement direction,
   objects that clip through each other or defy gravity
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
1. Carefully examine the image for ALL artifact categories listed (A–J).
2. Identify the 2–4 most compelling pieces of visual evidence — be specific
   (mention exact locations: "left cheek", "background behind the subject",
   "hairline at top-right", "right hand fingers", etc.).
3. Assign each observation to one of the artifact categories (A–J).
4. Pay particular attention to:
   - Any region where the image quality or noise level abruptly changes
   - Faces or skin with unusually smooth, plastic-like texture
   - Hair, fingers, or fine details that look merged/blurred
   - Physics or lighting that seems impossible or inconsistent
   - Background elements that look warped, melted, or unusually blurry
5. Give an overall confidence rating for your conclusion:
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
            temperature=0.10,
            max_tokens=700,
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
