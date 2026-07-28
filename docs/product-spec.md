# Angel of Music Product Spec

## Approval

Approved for implementation by Codex on July 28, 2026.

## Target User

Angel of Music is for a game designer who is building an early prototype and needs temporary music that communicates the intended mood of a scene before a composer, sound designer, or final art pipeline is involved.

The designer may have a screenshot, concept image, mood board frame, or rough environment mockup. They are not trying to produce final soundtrack material. They are trying to make a prototype easier to understand during internal playtests, design reviews, pitch conversations, and handoffs to audio collaborators.

## Core Problem

Early prototypes often communicate mechanics before they communicate tone. A scene may be meant to feel lonely, sacred, tense, playful, uncanny, romantic, triumphant, or fragile, but placeholder silence or mismatched stock music can mislead reviewers.

Angel of Music should help the designer turn a scene image into a useful musical direction quickly, then generate a short instrumental cue that can stand in as temporary mood music.

## Main Workflow

1. The user uploads or selects a scene image.
2. The app analyzes the image for mood-relevant details such as setting, color, lighting, implied action, tension, scale, and emotional tone.
3. The app produces an editable musical brief in plain language.
4. The user reviews and edits the brief before generation.
5. The backend generates a short instrumental cue from the approved brief.
6. The app returns the cue, basic audio properties, and the brief that produced it.
7. The user can download or reuse the result as temporary prototype audio.

## Useful Result Criteria

A result is useful when it helps a designer communicate intent, not when it sounds like a finished commercial score.

The generated output should:

- Match the intended emotional direction of the scene.
- Be short enough to iterate quickly.
- Avoid vocals unless explicitly supported later.
- Loop or sit under gameplay without demanding too much attention.
- Be accompanied by the editable brief so the user can explain or revise the direction.
- Include basic measurable audio properties, such as duration and approximate loudness, when available.
- Make it easy to compare the scene, brief, and generated cue as one connected decision.

## MVP Scope

The MVP includes:

- Single image upload.
- Image-based mood interpretation.
- Editable musical brief.
- Short instrumental music generation.
- Job-based generation flow for long-running work.
- Basic status states: queued, running, done, and failed.
- Basic result display and download.
- Clear messaging that output is temporary prototype material.

## Excluded From MVP

The MVP does not include:

- Final soundtrack production.
- Multi-track stems.
- DAW project export.
- Advanced mixing or mastering.
- Beat-accurate adaptive music systems.
- In-game middleware integration.
- Real-time scoring during gameplay.
- Composer marketplace features.
- Collaboration, comments, or approvals.
- User accounts, billing, or asset libraries unless needed for local testing.
- Legal review or rights clearance automation.

## Claims To Avoid

Angel of Music must not claim that it:

- Replaces composers, sound designers, or music supervisors.
- Produces final, release-ready, legally cleared soundtrack assets.
- Guarantees originality, copyright clearance, or non-infringement.
- Identifies the only correct musical interpretation of an image.
- Infers private facts, real-world intent, or sensitive traits from an image.
- Can safely imitate a living artist, named composer, copyrighted score, or protected franchise style.
- Grants rights to uploaded images the user does not already have permission to use.

## Image Rights Expectations

Users should only upload images they own, created, licensed, or otherwise have permission to use for this purpose.

The product should avoid presenting uploaded images as public gallery content by default. During development, uploaded files should be treated as user-provided inputs for generating a private prototype result.

If sample images are included in the app, they should be original, public-domain, permissively licensed, or generated specifically for the project with documented usage expectations.

## Output Usage Expectations

Generated music is intended for temporary prototype, internal review, and mood communication use.

The app should communicate that users are responsible for checking whether generated output is appropriate for their intended use, especially before public release, commercial use, publishing, streaming, or inclusion in a shipped game.

The safest default product language is:

"Use these results as temporary prototype audio and creative direction. Do not treat them as final cleared soundtrack assets without review."

## Implementation Guidance

The frontend and backend should communicate through explicit HTTP contracts. Music generation should be modeled as a job rather than one long browser request, because generation can be slow, fail, or need progress reporting.

The product should preserve human control by making the musical brief editable before generation. The image should suggest direction; it should not silently decide the final creative intent.
