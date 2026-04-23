from __future__ import annotations

import asyncio
import hashlib
import json
import random
import re
import unicodedata
from dataclasses import dataclass
from typing import Protocol

import httpx

from brainopt.models import (
    CandidateBatch,
    CandidateNotes,
    CandidateVariant,
    Constraints,
    OptimizeRequest,
    RankedCandidate,
    RefineRequest,
)


class LLMProvider(Protocol):
    model_name: str

    async def generate_variants(self, request: OptimizeRequest) -> CandidateBatch:
        ...

    async def explain_ranking(self, request: OptimizeRequest, ranked_candidates: list[RankedCandidate]) -> str:
        ...

    async def explain_score_only(
        self,
        platform: str,
        tone: str,
        ranked_candidates: list[RankedCandidate],
    ) -> str:
        ...

    async def refine_winner(self, request: OptimizeRequest, winner: RankedCandidate) -> str:
        ...

    async def refine_text(self, request: RefineRequest) -> str:
        ...


class LLMRateLimitError(RuntimeError):
    pass


class LLMAPIError(RuntimeError):
    pass


def _strip_json_fence(raw_text: str) -> str:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


@dataclass(frozen=True)
class StrategyBlueprint:
    name: str
    angle: str
    hook_pattern: str
    structure: str
    avoid: str


_STRATEGY_POOL: tuple[StrategyBlueprint, ...] = (
    StrategyBlueprint(
        name="contrarian",
        angle="Disagree with a belief the audience is quietly holding.",
        hook_pattern="Open with the counter-claim as a flat, confident statement.",
        structure="Counter-claim, one sharp reason, one practical implication.",
        avoid="Vague hot takes without a concrete target.",
    ),
    StrategyBlueprint(
        name="operator",
        angle="Write as someone who has shipped the thing in the last quarter.",
        hook_pattern="Open with a specific operating observation from the work itself.",
        structure="Observation, why it matters now, one concrete move to make this week.",
        avoid="Advice that any coach could give without context.",
    ),
    StrategyBlueprint(
        name="micro_case",
        angle="A tiny concrete scenario: one team, one decision, one outcome.",
        hook_pattern="Drop straight into the scene with no framing preamble.",
        structure="Scene in one line, the decision in one line, the lesson in one line.",
        avoid="Long narrative setup or invented metrics.",
    ),
    StrategyBlueprint(
        name="sharp_observation",
        angle="Anchor on a single crisp, qualitative observation about the space.",
        hook_pattern="One short declarative sentence that is debatable but clearly true.",
        structure="Observation, the mechanism behind it, one short consequence.",
        avoid="Fabricated percentages or study names.",
    ),
    StrategyBlueprint(
        name="founder_tradeoff",
        angle="Name a real tradeoff operators face and pick a side.",
        hook_pattern="Open by naming the tradeoff directly as a tension.",
        structure="The tradeoff, why both sides tempt, the call you would make.",
        avoid="False binaries that do not actually conflict in practice.",
    ),
    StrategyBlueprint(
        name="team_adoption",
        angle="Focus on adoption, alignment, or handoffs instead of strategy in a vacuum.",
        hook_pattern="Name a dynamic the reader has seen on their own team.",
        structure="Dynamic, why it forms, the first thing that breaks it.",
        avoid="Org-chart theater without describing actual behavior.",
    ),
    StrategyBlueprint(
        name="timing",
        angle="Argue about when to act, not what to do.",
        hook_pattern="Open with a timing claim such as most teams do X too early.",
        structure="Timing claim, the signal that it is time, what to skip in the meantime.",
        avoid="Prescriptive advice that ignores stage and context.",
    ),
    StrategyBlueprint(
        name="leverage",
        angle="Zoom in on bottlenecks and where effort actually compounds.",
        hook_pattern="Point at a hidden bottleneck most people accept as normal.",
        structure="Bottleneck, the multiplier if unblocked, the cheap next action.",
        avoid="Generic productivity platitudes.",
    ),
    StrategyBlueprint(
        name="reframe",
        angle="Rename the problem so the right move becomes obvious.",
        hook_pattern="Open by relabeling the problem in one short line.",
        structure="Old frame, new frame, what changes in practice.",
        avoid="Wordplay that does not change any behavior.",
    ),
    StrategyBlueprint(
        name="failure_mode",
        angle="Point at the specific way this effort usually fails.",
        hook_pattern="Name the failure pattern as if it were a product everyone secretly owns.",
        structure="Pattern, root cause, one early signal of it showing up.",
        avoid="Doom-posting without offering a lever.",
    ),
    StrategyBlueprint(
        name="principle",
        angle="State one durable principle and defend it in plain terms.",
        hook_pattern="Open with the principle as a short, unqualified rule.",
        structure="Rule, one concrete example, the edge where it stops applying.",
        avoid="Universal advice with no stated edge case.",
    ),
    StrategyBlueprint(
        name="other_side_pov",
        angle="Adopt the viewpoint of the reader's counterpart (customer, engineer, investor).",
        hook_pattern="Open from inside the other side's head.",
        structure="What they see, why they react that way, what it implies for the reader.",
        avoid="Projecting feelings without grounding in observable behavior.",
    ),
    StrategyBlueprint(
        name="myth_bust",
        angle="Pick a specific popular belief in the audience's feed and push back.",
        hook_pattern="Compress the belief in one line, then flip it on the next.",
        structure="Belief, why it is stickier than it should be, the better default.",
        avoid="Strawman versions of the belief that nobody actually holds.",
    ),
    StrategyBlueprint(
        name="future_signal",
        angle="Point at an early signal of where the space is moving.",
        hook_pattern="Describe the signal as already happening, not as a forecast.",
        structure="Signal, what it implies, one adjustment worth making now.",
        avoid="Sci-fi speculation with no present-day hook.",
    ),
    StrategyBlueprint(
        name="cost_of_inaction",
        angle="Make the price of staying still concrete.",
        hook_pattern="Open with what the reader is already paying by doing nothing.",
        structure="Hidden cost, how it accumulates, the small move that stops the bleed.",
        avoid="Fear-mongering without a believable mechanism.",
    ),
)


_LAUNCH_STRATEGY_POOL: tuple[StrategyBlueprint, ...] = (
    StrategyBlueprint(
        name="builder_note",
        angle="Write as the builder explaining what was shipped and why it exists.",
        hook_pattern="Open with 'I built' or 'I open-sourced' plus the concrete thing.",
        structure="What shipped, the problem it addresses, the honest status or caveat.",
        avoid="Grand claims about changing an industry.",
    ),
    StrategyBlueprint(
        name="problem_solution",
        angle="Start from the specific workflow problem the tool solves.",
        hook_pattern="Name the broken workflow in one plain sentence.",
        structure="Problem, why existing behavior is insufficient, how the tool helps.",
        avoid="Generic complaints about AI, content, or productivity.",
    ),
    StrategyBlueprint(
        name="product_walkthrough",
        angle="Show what the tool actually does in sequence.",
        hook_pattern="Open with the product workflow in concrete verbs.",
        structure="Input, processing step, output, why that helps the reader.",
        avoid="Feature lists without a user-facing reason.",
    ),
    StrategyBlueprint(
        name="honest_alpha",
        angle="Use the alpha status as credibility rather than hiding it.",
        hook_pattern="Open by naming the useful but unfinished nature of the project.",
        structure="What is useful now, what is experimental, who should try it.",
        avoid="Apologizing for the project or overclaiming reliability.",
    ),
    StrategyBlueprint(
        name="technical_angle",
        angle="Write for technical readers who care about local control and architecture.",
        hook_pattern="Open with the local or open-source implementation choice.",
        structure="Architecture choice, practical benefit, one limitation to understand.",
        avoid="Deep dependency details that do not matter in a social post.",
    ),
    StrategyBlueprint(
        name="workflow_before_after",
        angle="Contrast the old drafting workflow with the new one.",
        hook_pattern="Open with the before-state readers already recognize.",
        structure="Before, after, why the shift matters.",
        avoid="Pretending the tool replaces human judgment.",
    ),
)


def _request_seed(request: OptimizeRequest) -> int:
    blob = "|".join(
        [
            request.topic or "",
            request.source_material or "",
            request.platform or "",
            request.audience or "",
            request.goal or "",
            request.tone or "",
            str(request.candidate_count),
        ]
    )
    digest = hashlib.sha256(blob.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _is_launch_brief(request: OptimizeRequest) -> bool:
    text = f"{request.topic}\n{request.source_material}".lower()
    launch_terms = (
        "i built",
        "built a",
        "built an",
        "open-sourced",
        "open sourced",
        "opensource",
        "open-source",
        "new tool",
        "github",
        "repo",
        "repository",
    )
    return any(term in text for term in launch_terms)


def _strategy_pool_for_request(request: OptimizeRequest) -> tuple[StrategyBlueprint, ...]:
    if _is_launch_brief(request):
        return _LAUNCH_STRATEGY_POOL
    return _STRATEGY_POOL


def _select_strategies(
    count: int,
    seed: int,
    pool: tuple[StrategyBlueprint, ...] = _STRATEGY_POOL,
) -> list[StrategyBlueprint]:
    rng = random.Random(seed)
    available = list(pool)
    rng.shuffle(available)
    if count <= len(available):
        return available[:count]
    selected = list(available)
    idx = 0
    while len(selected) < count:
        selected.append(available[idx % len(available)])
        idx += 1
    return selected


def _source_title(source_material: str) -> str:
    for raw_line in (source_material or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading = line.lstrip("#").strip()
        if len(heading) <= 80:
            return heading
        name_match = re.match(r"^([A-Z][A-Za-z0-9_-]{1,40})\s+(?:is|helps|turns|uses|runs|:|-)", heading)
        if name_match:
            return name_match.group(1)
        first_words = heading.split()[:3]
        return " ".join(first_words).strip()
    return ""


def _launch_context_block(request: OptimizeRequest) -> str:
    if not _is_launch_brief(request):
        return (
            "Brief interpretation\n"
            "- Treat the request as a thought-led social post, grounded in the supplied topic and source."
        )

    product_name = _source_title(request.source_material)
    product_line = f"- Product/project name from source: {product_name}" if product_name else ""
    return (
        "Brief interpretation\n"
        "- Treat this as a builder launch post, not a generic essay.\n"
        "- The reader should understand what was built, who it is for, what it does, and what is still experimental.\n"
        "- Use first person if the requested angle says the author built or open-sourced the project.\n"
        "- Prefer concrete product nouns over abstract claims about AI, creativity, social strategy, or virality.\n"
        "- For broad audiences, focus on the problem, workflow, and honest caveat. Avoid setup requirements unless the audience is explicitly technical.\n"
        "- Do not imply the full workflow is private or local-only when OpenAI or another external API may be used. Say 'local scoring worker' instead.\n"
        "- Do not lead with broad claims like 'AI should write your strategy' unless the user explicitly asked for that argument.\n"
        f"{product_line}"
    ).strip()


def _launch_fallback_text(blueprint: StrategyBlueprint, product_name: str) -> str:
    if blueprint.name == "builder_note":
        return (
            f"I open-sourced {product_name} because drafting is only half the problem.\n"
            "The harder part is comparing versions before you publish.\n"
            "It generates, scores, compares, and refines social post drafts in a local workbench.\n"
            "It is still alpha, but the workflow is already useful."
        )
    if blueprint.name == "product_walkthrough":
        return (
            f"{product_name} turns a brief into several post directions.\n"
            "Then a local scoring worker compares hook strength, momentum, and sentence contribution.\n"
            "The goal is not guaranteed performance.\n"
            "It is a better way to choose between drafts."
        )
    if blueprint.name == "technical_angle":
        return (
            f"{product_name} is open source because I wanted the scoring loop to stay inspectable.\n"
            "The API orchestrates generation, a local worker handles TribeV2 scoring, and the web app keeps comparison readable.\n"
            "That matters when the output is only as useful as the ranking logic behind it."
        )
    if blueprint.name == "honest_alpha":
        return (
            f"{product_name} is not a magic engagement predictor.\n"
            "It is an alpha workbench for testing post structure, pacing, and relative draft quality.\n"
            "That honesty is the point: better signals, fewer fake guarantees."
        )
    if blueprint.name == "problem_solution":
        return (
            "Most AI writing tools stop at generation.\n"
            f"{product_name} adds the missing comparison step: generate a few drafts, score them locally, and inspect why one version is stronger.\n"
            "The point is not autopublishing.\n"
            "It is making draft selection less subjective."
        )
    if blueprint.name == "workflow_before_after":
        return (
            "My old workflow was: generate several drafts, then pick one by feel.\n"
            f"{product_name} changes that into a loop: brief, generate, score, compare, refine.\n"
            "It still needs judgment, but the comparison is no longer a blank stare at four similar drafts."
        )
    return (
        f"{product_name} is a small attempt to make AI-assisted drafting more inspectable.\n"
        "Generate the variants, score them locally, compare the sentence-level signals, then refine the strongest one.\n"
        "That is a narrower promise than viral content, and a more useful one."
    )


def _is_poor_launch_variant(text: str, product_name: str) -> bool:
    lowered = (text or "").lower()
    if product_name and product_name.lower() not in lowered:
        return True
    unsupported_claims = (
        "without sending your drafts",
        "draft data stays private",
        "never leaves your machine",
        "never leave your machine",
        "local-only",
        "full privacy",
        "third-party optimizer",
    )
    if any(claim in lowered for claim in unsupported_claims):
        return True
    setup_terms = (
        "windows 11",
        "python 3.11",
        "openai api key",
        "local clone",
        "clone of the tribev2",
        "requires a local clone",
    )
    if sum(1 for term in setup_terms if term in lowered) >= 2:
        return True
    bad_openers = (
        "ai should",
        "most people think",
        "the future of",
        "i learned this the hard way",
        "hot take",
    )
    if lowered.startswith(bad_openers):
        return True
    grounding_terms = (
        "local",
        "workbench",
        "draft",
        "score",
        "scoring",
        "compare",
        "refine",
        "open source",
        "open-source",
        "alpha",
        "tribev2",
        "openai",
        "sentence",
        "momentum",
    )
    matches = {term for term in grounding_terms if term in lowered}
    return len(matches) < 2


def _duplicate_key(text: str) -> str:
    lowered = (text or "").lower()
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def _platform_style(platform: str) -> str:
    key = (platform or "general").lower()
    styles = {
        "twitter": (
            "Format: one tight unit, typically 1 to 3 short sentences. "
            "No preamble. The first 7 words must earn the read. "
            "Aim for under 240 characters unless a hard cap says otherwise."
        ),
        "x": (
            "Format: one tight unit, typically 1 to 3 short sentences. "
            "No preamble. The first 7 words must earn the read. "
            "Aim for under 240 characters unless a hard cap says otherwise."
        ),
        "linkedin": (
            "Format: 4 to 7 short lines separated by line breaks. "
            "Credible, specific, plain-spoken. No corporate cliches. "
            "End with a pointed takeaway or a single sharp question."
        ),
        "instagram": (
            "Format: the first line must hook on its own because it sits above the fold. "
            "2 to 4 short paragraphs, vivid but grounded. "
            "End on a clear beat, not a dangling thought."
        ),
        "threads": (
            "Format: conversational and quick. 1 to 4 short sentences. "
            "Feels like a thought from a smart friend, not a brand account."
        ),
        "general": (
            "Format: medium-length, readable in under 20 seconds, one idea per variant."
        ),
    }
    return styles.get(key, styles["general"])


def _tone_style(tone: str) -> str:
    key = (tone or "").strip().lower()
    if not key:
        return "Tone: direct and useful, with a clear point of view."
    guides = {
        "casual": "Tone: relaxed and plain-spoken. Contractions are fine. No jargon.",
        "professional": "Tone: composed and credible. Precise word choice. No filler.",
        "sharp": "Tone: blunt. Minimal hedging. Every sentence earns its place.",
        "witty": "Tone: dry and smart. Let the insight carry the humor, not punchlines.",
        "empathetic": "Tone: warm and grounded. Acknowledge the reader's reality before stating the take.",
        "bold": "Tone: confident and declarative. Do not back down from the claim.",
        "analytical": "Tone: reasoned and structured. Make the logic visible in one line.",
        "friendly": "Tone: approachable and human. Feels written by a person, not a brand.",
        "confident": "Tone: assured. No throat-clearing or apology phrases.",
        "provocative": "Tone: challenges the reader's default view without being rude.",
        "inspirational": "Tone: grounded optimism. Specific enough that it could not apply to anyone.",
    }
    if key in guides:
        return guides[key]
    return f"Tone: {tone}. Keep word choices consistent with that feel across every sentence."


def _source_material_excerpt(source_material: str, limit: int = 12000) -> tuple[str, bool]:
    cleaned = (source_material or "").strip()
    if not cleaned:
        return "", False
    if len(cleaned) <= limit:
        return cleaned, False
    clipped = cleaned[:limit]
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0]
    return clipped.strip(), True


def _topic_context(request: OptimizeRequest) -> str:
    topic = (request.topic or "").strip()
    has_source_material = bool((request.source_material or "").strip())
    if topic and has_source_material:
        return (
            f"Requested angle: {topic}\n"
            "Use the source material below as grounding, but keep the post centered on this requested angle."
        )
    if topic:
        return f"Requested angle: {topic}"
    if has_source_material:
        return (
            "No explicit angle was provided.\n"
            "Infer the strongest post angle from the source material and make it concrete."
        )
    return "No explicit angle or source material was provided."


def _source_material_prompt_block(request: OptimizeRequest) -> str:
    source_material = (request.source_material or "").strip()
    if not source_material:
        return "Source material\n- None supplied. Generate from the brief only."

    excerpt, was_truncated = _source_material_excerpt(source_material)
    truncation_note = (
        "The source excerpt was truncated for prompt size. Prioritize the main claim, strongest supporting detail, and clearest tension."
        if was_truncated
        else "Use the source material as grounding for facts and angle selection."
    )
    return (
        "Source material\n"
        "- Treat the pasted material as source context, not as copy to repost verbatim.\n"
        "- Pull out one clear argument, two concrete product facts, and one implication that matters to the audience.\n"
        "- Do not add facts, quotes, or numbers that are not supported by the source.\n"
        "- If the source is project documentation, use product facts from it: name, workflow, architecture, status, limitations, and supported use cases.\n"
        f"- {truncation_note}\n"
        "BEGIN SOURCE MATERIAL\n"
        f"{excerpt}\n"
        "END SOURCE MATERIAL"
    )


def _request_subject(request: OptimizeRequest) -> str:
    topic = (request.topic or "").strip()
    if topic:
        return topic
    excerpt, _ = _source_material_excerpt(request.source_material, limit=140)
    if excerpt:
        return excerpt.replace("\n", " ")
    return "the supplied topic"


def _generation_rules(request: OptimizeRequest) -> str:
    constraints = request.constraints
    rules = [
        "Use plain ASCII punctuation only. No smart quotes, en dashes, or em dashes.",
        "No emoji.",
        "Do not invent statistics, studies, case names, or quotes.",
        "Do not invent a target market, persona, or use case that is not supported by the brief or source.",
        "Use at least two concrete details from the source material in every variant when source material is supplied.",
        "Name the product/project when the source material provides a name.",
        "Avoid unsupported broad claims about AI, social strategy, virality, marketing, or engagement.",
        "Do not claim drafts stay private, never leave the machine, or avoid third-party services unless the source explicitly supports the full claim.",
        "Avoid installation details (Windows version, Python version, API keys, local clone paths) unless the audience or goal is setup-focused.",
        "Do not use corporate cliches (unlock, game-changer, move the needle, leverage synergies, in today's fast-paced world, let's dive in).",
        "Do not use generic LinkedIn hooks like 'Most people think', 'The future of', 'AI should', or 'I learned this the hard way'.",
        "No throat-clearing openers (in my experience, I have been thinking, here is a thought, hot take).",
        "Each variant must open with a line that could stand alone as a hook.",
        "No two variants may share the same first 4 words, the same opening move, or the same core argument.",
        "Each variant must feel written by a different thoughtful person, not a paraphrase of the others.",
        "Match the requested tone consistently across every sentence of a variant.",
    ]
    hashtag_limit = constraints.hashtag_limit
    if hashtag_limit is None:
        rules.append("Do not use hashtags unless they clearly add meaning.")
    elif hashtag_limit == 0:
        rules.append("Do not include any hashtags.")
    else:
        rules.append(f"Use at most {hashtag_limit} hashtag(s), and only if they add meaning.")
    if constraints.include_cta:
        rules.append(
            "Close with a light, specific CTA that suits the platform (a question, an invitation, or a concrete next step). "
            "The CTA must connect to the point, not tack on."
        )
    else:
        rules.append("Do not include a CTA.")
    if constraints.max_chars is not None:
        rules.append(f"Stay within {constraints.max_chars} characters including spaces.")
    if constraints.hard_max_length is not None:
        rules.append(f"Hard cap at {constraints.hard_max_length} characters. Shorter is fine.")
    return "\n".join(f"- {rule}" for rule in rules)


def _refinement_rules(constraints: Constraints) -> str:
    rules = [
        "Use plain ASCII punctuation only. No smart quotes, en dashes, or em dashes.",
        "No emoji.",
        "Do not add claims, facts, or numbers that were not in the original.",
        "Preserve the original core argument and voice.",
        "Keep the original first-line hook idea; tighten it only if it is objectively weak.",
        "Do not introduce corporate cliches.",
    ]
    if constraints.include_cta:
        rules.append("A light CTA is allowed only if it fits the existing draft.")
    else:
        rules.append("Do not add a CTA.")
    if constraints.max_chars is not None:
        rules.append(f"Stay within {constraints.max_chars} characters.")
    if constraints.hard_max_length is not None:
        rules.append(f"Hard cap at {constraints.hard_max_length} characters.")
    return "\n".join(f"- {rule}" for rule in rules)


_SMART_CHARS = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201a": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u201e": '"',
    "\u2013": "-",
    "\u2014": "-",
    "\u2026": "...",
    "\u00a0": " ",
    "\u2022": "-",
}


def _normalize_text(text: str, constraints: Constraints) -> str:
    if not text:
        return text
    normalized = text
    for src, dst in _SMART_CHARS.items():
        normalized = normalized.replace(src, dst)
    normalized = unicodedata.normalize("NFKC", normalized).strip()
    if constraints.hashtag_limit == 0:
        normalized = re.sub(r"(^|\s)#\w+", r"\1", normalized).strip()
    normalized = re.sub(r"[ \t]+\n", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    cap_candidates = [
        value
        for value in (constraints.hard_max_length, constraints.max_chars)
        if value is not None
    ]
    if cap_candidates:
        cap = min(cap_candidates)
        if len(normalized) > cap:
            normalized = normalized[:cap].rstrip()
    return normalized


def _with_strict_objects(schema: dict) -> dict:
    """Return an OpenAI structured-output schema with strict object fields."""
    cloned = json.loads(json.dumps(schema))

    def visit(node: object) -> None:
        if not isinstance(node, dict):
            return
        if node.get("type") == "object":
            node.setdefault("additionalProperties", False)
            properties = node.get("properties")
            if isinstance(properties, dict):
                node["required"] = list(properties.keys())
                for child in properties.values():
                    visit(child)
        items = node.get("items")
        if isinstance(items, dict):
            visit(items)
        any_of = node.get("anyOf")
        if isinstance(any_of, list):
            for child in any_of:
                visit(child)

    visit(cloned)
    return cloned


def _response_output_text(data: dict) -> str:
    if isinstance(data.get("output_text"), str):
        return data["output_text"]

    chunks: list[str] = []
    for item in data.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    return "".join(chunks).strip()


def _openai_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        body = response.text.strip()
        return body[:500] if body else response.reason_phrase

    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        message = str(error.get("message") or response.reason_phrase)
        error_type = error.get("type")
        error_code = error.get("code")
        details = [message]
        if error_type:
            details.append(f"type={error_type}")
        if error_code:
            details.append(f"code={error_code}")
        return " ".join(details)
    return str(payload)[:500]


@dataclass
class OpenAIProvider:
    api_key: str
    model_name: str
    fallback_model: str
    api_base: str
    reasoning_effort: str
    max_retries: int
    timeout_seconds: float

    def _model_sequence(self) -> list[str]:
        models = [self.model_name]
        fallback = (self.fallback_model or "").strip()
        if fallback and fallback not in models:
            models.append(fallback)
        return models

    async def _post_response(self, payload: dict) -> dict:
        url = f"{self.api_base.rstrip('/')}/responses"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        rate_limit_errors: list[str] = []

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            for model in self._model_sequence():
                payload["model"] = model
                for attempt in range(self.max_retries + 1):
                    response = await client.post(url, headers=headers, json=payload)
                    if response.status_code == 429:
                        message = _openai_error_message(response)
                        rate_limit_errors.append(f"{model}: {message}")
                        if attempt < self.max_retries:
                            retry_after = response.headers.get("retry-after")
                            try:
                                delay = float(retry_after) if retry_after else 1.5 * (attempt + 1)
                            except ValueError:
                                delay = 1.5 * (attempt + 1)
                            await asyncio.sleep(min(delay, 8.0))
                            continue
                        break
                    if response.status_code >= 400:
                        message = _openai_error_message(response)
                        raise LLMAPIError(f"OpenAI {response.status_code} for model {model}: {message}")
                    return response.json()

        detail = "; ".join(rate_limit_errors[-2:]) or "OpenAI returned 429 Too Many Requests."
        raise LLMRateLimitError(
            f"{detail}. Check account quota/rate limits, or set OPENAI_MODEL/OPENAI_FALLBACK_MODEL to an available lower-rate model."
        )

    async def _generate_json(
        self,
        prompt: str,
        schema: dict,
        schema_name: str = "narriv_response",
    ) -> dict:
        payload = {
            "model": self.model_name,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "You are Narriv's copywriting engine. Write sharp, concrete social copy. "
                        "Return only JSON that matches the requested schema."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": _with_strict_objects(schema),
                    "strict": True,
                }
            },
        }
        if self.reasoning_effort:
            payload["reasoning"] = {"effort": self.reasoning_effort}

        data = await self._post_response(payload)

        text = _response_output_text(data)
        if not text:
            raise ValueError("OpenAI response text is empty.")
        return json.loads(_strip_json_fence(text))

    async def generate_variants(self, request: OptimizeRequest) -> CandidateBatch:
        schema = {
            "type": "object",
            "properties": {
                "platform": {"type": "string"},
                "variants": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "strategy": {"type": "string"},
                            "tone": {"type": "string"},
                            "text": {"type": "string"},
                            "notes": {
                                "type": "object",
                                "properties": {
                                    "hook": {"type": "string"},
                                    "cta": {"type": "string"},
                                    "audience_angle": {"type": "string"},
                                },
                                "required": ["hook", "cta", "audience_angle"],
                            },
                        },
                        "required": ["id", "strategy", "tone", "text", "notes"],
                    },
                },
            },
            "required": ["platform", "variants"],
        }

        strategies = _select_strategies(
            request.candidate_count,
            _request_seed(request),
            _strategy_pool_for_request(request),
        )
        strategy_blocks = []
        for idx, blueprint in enumerate(strategies):
            strategy_blocks.append(
                f"- id=v{idx + 1} | strategy={blueprint.name}\n"
                f"    angle: {blueprint.angle}\n"
                f"    hook: {blueprint.hook_pattern}\n"
                f"    structure: {blueprint.structure}\n"
                f"    avoid: {blueprint.avoid}"
            )
        strategy_lines = "\n".join(strategy_blocks)

        prompt = f"""
You are a senior social content strategist writing variants a real founder would actually post.

Context
- Platform: {request.platform}
- Audience: {request.audience}
- Goal: {request.goal}
- Tone: {request.tone}
- Variants required: {request.candidate_count}

Angle guidance
{_topic_context(request)}

{_launch_context_block(request)}

{_source_material_prompt_block(request)}

Platform style
{_platform_style(request.platform)}

Tone direction
{_tone_style(request.tone)}

Use exactly these strategies, one per variant, in this order.
Each variant's 'strategy' field must equal the strategy name shown.

{strategy_lines}

Hard rules
{_generation_rules(request)}

Diversity self-check before answering
- Confirm each variant is about the requested subject, not a generic adjacent topic.
- Confirm each variant contains at least two details traceable to the source material when source material is supplied.
- Reread all variants in order. If any two could be summarized with the same sentence, rewrite one.
- Reread every first sentence. If two use the same opening move (question, stat, I-phrasing, etc.), rewrite one.
- Reread every last sentence. If two close the same way, rewrite one.
- Confirm every variant delivers on its assigned angle, hook, and structure above.

Notes fields for each variant
- 'hook' summarizes the first-line move in 6 words or fewer.
- 'cta' summarizes the closing move in 6 words or fewer. Write 'none' if no CTA is used.
- 'audience_angle' names the specific slice of the audience this variant speaks to most directly.

Return strict JSON matching the provided schema. No markdown fences. No commentary.
""".strip()

        payload = await self._generate_json(
            prompt=prompt,
            schema=schema,
            schema_name="candidate_batch",
        )
        batch = CandidateBatch.model_validate(payload)
        batch.platform = request.platform
        product_name = _source_title(request.source_material)
        should_ground_launch = _is_launch_brief(request) and bool(product_name)
        seen_texts: set[str] = set()
        for idx, variant in enumerate(batch.variants):
            if not variant.id:
                variant.id = f"v{idx + 1}"
            if idx < len(strategies) and not variant.strategy:
                variant.strategy = strategies[idx].name
            if not variant.tone:
                variant.tone = request.tone
            variant.text = _normalize_text(variant.text, request.constraints)
            if should_ground_launch and idx < len(strategies) and _is_poor_launch_variant(variant.text, product_name):
                fallback_text = _launch_fallback_text(strategies[idx], product_name)
                if request.constraints.include_cta:
                    fallback_text += "\nIf you want to try it, the repo is open."
                variant.text = _normalize_text(
                    fallback_text,
                    request.constraints,
                )
                variant.notes.hook = "Grounded launch fallback"
                variant.notes.audience_angle = "Builders and technical readers"
                variant.notes.cta = "none" if not request.constraints.include_cta else variant.notes.cta
            duplicate_key = _duplicate_key(variant.text)
            if duplicate_key in seen_texts and should_ground_launch and idx < len(strategies):
                fallback_text = _launch_fallback_text(strategies[idx], product_name)
                if request.constraints.include_cta:
                    fallback_text += "\nIf you want to try it, the repo is open."
                variant.text = _normalize_text(fallback_text, request.constraints)
                variant.notes.hook = "Duplicate replaced"
                variant.notes.audience_angle = "Builders and technical readers"
                variant.notes.cta = "none" if not request.constraints.include_cta else variant.notes.cta
                duplicate_key = _duplicate_key(variant.text)
            seen_texts.add(duplicate_key)
        return batch

    async def explain_ranking(self, request: OptimizeRequest, ranked_candidates: list[RankedCandidate]) -> str:
        top = ranked_candidates[:3]
        schema = {
            "type": "object",
            "properties": {
                "explanation": {"type": "string"},
            },
            "required": ["explanation"],
        }
        compact_scores = [
            {
                "id": item.id,
                "strategy": item.strategy,
                "final_score": item.scores.final_score,
                "hook_score": item.scores.hook_score,
                "sustained_response_score": item.scores.sustained_response_score,
                "end_strength_score": item.scores.end_strength_score,
                "diagnostics": item.diagnostics.model_dump(),
            }
            for item in top
        ]
        prompt = (
            "Write a concise recommendation for the winning candidate and two improvement priorities. "
            f"User brief: platform={request.platform}, audience={request.audience}, goal={request.goal}, tone={request.tone}. "
            f"Ranked candidates (top 3): {json.dumps(compact_scores)}"
        )
        payload = await self._generate_json(prompt=prompt, schema=schema, schema_name="ranking_explanation")
        return payload["explanation"].strip()

    async def explain_score_only(
        self,
        platform: str,
        tone: str,
        ranked_candidates: list[RankedCandidate],
    ) -> str:
        schema = {
            "type": "object",
            "properties": {"explanation": {"type": "string"}},
            "required": ["explanation"],
        }
        compact_scores = [
            {
                "id": item.id,
                "strategy": item.strategy,
                "final_score": item.scores.final_score,
                "hook_score": item.scores.hook_score,
                "sustained_response_score": item.scores.sustained_response_score,
                "end_strength_score": item.scores.end_strength_score,
                "diagnostics": item.diagnostics.model_dump(),
            }
            for item in ranked_candidates[:3]
        ]
        prompt = (
            "Write a concise explanation of why the top scored post leads and mention the main weakness of the lower-ranked draft if one exists. "
            f"Platform={platform}, tone={tone}. Ranked candidates: {json.dumps(compact_scores)}"
        )
        payload = await self._generate_json(prompt=prompt, schema=schema, schema_name="score_explanation")
        return payload["explanation"].strip()

    async def refine_winner(self, request: OptimizeRequest, winner: RankedCandidate) -> str:
        return await self.refine_text(
            RefineRequest(
                platform=request.platform,
                tone=request.tone,
                constraints=request.constraints,
                text=winner.text,
                refinement_goal="Polish the strongest candidate while preserving its strategy and audience fit.",
            )
        )

    async def refine_text(self, request: RefineRequest) -> str:
        schema = {
            "type": "object",
            "properties": {"final_text": {"type": "string"}},
            "required": ["final_text"],
        }
        prompt = (
            "Polish this social post while preserving the core claim and voice.\n"
            f"Platform: {request.platform}\n"
            f"Tone: {request.tone}\n"
            f"Refinement goal: {request.refinement_goal or 'Improve clarity and flow without changing the argument.'}\n"
            "Platform style:\n"
            f"{_platform_style(request.platform)}\n"
            "Tone direction:\n"
            f"{_tone_style(request.tone)}\n"
            "Rules:\n"
            f"{_refinement_rules(request.constraints)}\n"
            f"Original text:\n{request.text}\n"
            "Return only JSON with a single 'final_text' field."
        )
        payload = await self._generate_json(prompt=prompt, schema=schema, schema_name="refined_post")
        final_text = payload["final_text"].strip()
        return _normalize_text(final_text, request.constraints)


@dataclass
class MockProvider:
    model_name: str = "gpt-5.4 (mock)"

    async def generate_variants(self, request: OptimizeRequest) -> CandidateBatch:
        strategies = _select_strategies(
            request.candidate_count,
            _request_seed(request),
            _strategy_pool_for_request(request),
        )
        variants: list[CandidateVariant] = []
        product_name = _source_title(request.source_material) or _request_subject(request)
        for idx, blueprint in enumerate(strategies):
            if _is_launch_brief(request):
                base = _launch_fallback_text(blueprint, product_name)
            else:
                base = (
                    f"{_request_subject(request)}: {blueprint.angle} Written for {request.audience}. "
                    f"Goal is {request.goal}."
                )
            if request.constraints.include_cta:
                base += " If this resonates, comment 'guide' and I will share a framework."
            base = _normalize_text(base, request.constraints)
            variants.append(
                CandidateVariant(
                    id=f"v{idx + 1}",
                    strategy=blueprint.name,
                    tone=request.tone,
                    text=base,
                    notes=CandidateNotes(
                        hook=blueprint.hook_pattern[:60],
                        cta="Invites comment for follow-up" if request.constraints.include_cta else "none",
                        audience_angle=f"Tailored for {request.audience}",
                    ),
                )
            )
        return CandidateBatch(platform=request.platform, variants=variants)

    async def explain_ranking(self, request: OptimizeRequest, ranked_candidates: list[RankedCandidate]) -> str:
        if not ranked_candidates:
            return "No candidates were scored."
        winner = ranked_candidates[0]
        return (
            f"{winner.id} is recommended because it balances hook energy, sustained response, and platform fit. "
            f"Primary focus next: strengthen sentence {winner.diagnostics.weakest_sentence} and tighten CTA."
        )

    async def explain_score_only(
        self,
        platform: str,
        tone: str,
        ranked_candidates: list[RankedCandidate],
    ) -> str:
        if not ranked_candidates:
            return "No candidates were scored."
        winner = ranked_candidates[0]
        if len(ranked_candidates) == 1:
            return (
                f"The submitted post scores strongest on {winner.strategy or 'its current structure'}. "
                f"Main weakness: {winner.reason}"
            )
        runner_up = ranked_candidates[1]
        return (
            f"{winner.id} leads because it balances hook energy, sustained response, and platform fit better than {runner_up.id}. "
            f"Main tradeoff: {runner_up.reason}"
        )

    async def refine_winner(self, request: OptimizeRequest, winner: RankedCandidate) -> str:
        return _normalize_text(winner.text, request.constraints)

    async def refine_text(self, request: RefineRequest) -> str:
        return _normalize_text(request.text, request.constraints)
