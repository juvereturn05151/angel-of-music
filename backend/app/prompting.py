from app.schemas import MusicBrief, MusicalArc, PromptResponse


def compose_prompt(brief: MusicBrief) -> PromptResponse:
    warnings: list[str] = []
    instruments = sorted({item.value for item in brief.instruments})
    textures = sorted({item.value for item in brief.textures})
    avoid_terms = sorted(
        {" ".join(item.lower().split()) for item in brief.avoid_terms if item.strip()}
    )

    if brief.musical_arc == MusicalArc.loop_friendly and not brief.loop_requested:
        warnings.append("loop-friendly arc conflicts with loop_requested=false.")
    if brief.vocals == "disabled" and "vocals" not in avoid_terms:
        avoid_terms.append("vocals")
    if brief.vocals == "enabled" and "vocals" in avoid_terms:
        avoid_terms.remove("vocals")
        warnings.append("vocals were removed from avoid terms because vocals are enabled.")

    fields = [
        ("purpose", "temporary background music for game prototype mood communication"),
        ("narrative_role", brief.narrative_role.value),
        ("emotion", brief.emotion.value),
        ("textures", ", ".join(textures)),
        ("energy", f"{brief.energy:.2f}"),
        ("emotional_intensity", f"{brief.emotional_intensity:.2f}"),
        ("bpm", str(brief.bpm)),
        ("duration_seconds", str(brief.duration_seconds)),
        ("instrument_families", ", ".join(instruments)),
        ("musical_arc", brief.musical_arc.value),
        ("loop_requested", "yes" if brief.loop_requested else "no"),
        ("vocals", brief.vocals),
        ("avoid", ", ".join(avoid_terms)),
    ]
    prompt = "\n".join(f"{key}: {value}" for key, value in fields)
    return PromptResponse(prompt=" ".join(prompt.split()), warnings=warnings)
