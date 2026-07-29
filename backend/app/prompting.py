from app.schemas import MusicBrief, MusicalArc, PromptResponse


def compose_prompt(brief: MusicBrief) -> PromptResponse:
    warnings: list[str] = []
    if brief.musical_arc == MusicalArc.loop_friendly and not brief.loop_requested:
        warnings.append("loop-friendly arc conflicts with loop_requested=false.")

    fields = [
        ("purpose", " ".join(brief.purpose.split())),
        ("mood_overview", " ".join(brief.rationale.split())),
        ("bpm", str(brief.bpm)),
        ("duration_seconds", str(brief.duration_seconds)),
        ("loop_requested", "yes" if brief.loop_requested else "no"),
        ("vocals", brief.vocals),
    ]
    prompt = "\n".join(f"{key}: {value}" for key, value in fields)
    return PromptResponse(prompt=" ".join(prompt.split()), warnings=warnings)
