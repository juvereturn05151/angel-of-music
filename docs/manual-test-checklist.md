# Manual Test Checklist

- Start backend with `uvicorn app.main:app --reload`.
- Start frontend with `npm.cmd run dev`.
- Open `http://localhost:5173`.
- Upload a valid PNG, JPEG, or WebP.
- Confirm the preview appears.
- Run mock analysis.
- Confirm visual observations are read-only and separate from artistic inference.
- Edit role, emotion, textures, instruments, BPM, duration, arc, loop request, avoid terms, and rationale.
- Confirm invalid values show validation feedback.
- Preview the deterministic prompt.
- Start mock generation.
- Confirm job status appears.
- Confirm a completed job displays the audio player.
- Play, pause, seek, and adjust volume.
- Confirm provenance displays no absolute paths or secrets.
- Upload a different image and confirm stale analysis, prompt, job, track, and provenance disappear.
- Try corrupt or unsupported files and confirm controlled errors.
