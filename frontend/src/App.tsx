import { useEffect, useMemo, useState } from "react";

import {
  analyzeImage,
  audioUrl,
  composePrompt,
  fetchJob,
  fetchProvenance,
  startGeneration
} from "./api";
import { emotions, instruments, musicalArcs, narrativeRoles, textures } from "./constants";
import type {
  AnalysisResponse,
  GenerationJob,
  InstrumentFamily,
  MusicBrief,
  Texture
} from "./types";
import { useAudioPlayer } from "./useAudioPlayer";

import "./styles.css";

const emptyBrief: MusicBrief = {
  narrative_role: "exploration",
  emotion: "peaceful",
  textures: ["warm"],
  energy: 0.35,
  emotional_intensity: 0.35,
  bpm: 84,
  duration_seconds: 14,
  instruments: ["piano"],
  musical_arc: "steady",
  loop_requested: true,
  avoid_terms: ["vocals"],
  rationale: "",
  vocals: "disabled"
};

function toBrief(analysis: AnalysisResponse): MusicBrief {
  return { ...analysis.inference, vocals: "disabled" };
}

function toggleList<T extends string>(items: T[], value: T): T[] {
  if (items.includes(value)) {
    return items.filter((item) => item !== value);
  }
  return [...items, value];
}

function validateBrief(brief: MusicBrief): string[] {
  const errors: string[] = [];
  if (brief.textures.length === 0) errors.push("Choose at least one texture.");
  if (brief.instruments.length === 0) errors.push("Choose at least one instrument family.");
  if (brief.bpm < 40 || brief.bpm > 220) errors.push("BPM must be between 40 and 220.");
  if (brief.duration_seconds < 10 || brief.duration_seconds > 20) {
    errors.push("Duration must be between 10 and 20 seconds.");
  }
  if (brief.musical_arc === "loop-friendly" && !brief.loop_requested) {
    errors.push("Loop-friendly arc conflicts with loop request turned off.");
  }
  return errors;
}

function AudioPlayer({ src }: { src: string }) {
  const player = useAudioPlayer(src);
  return (
    <section className="panel">
      <h2>Track Result</h2>
      {player.error ? <p className="error">{player.error}</p> : null}
      <div className="player">
        <button type="button" onClick={player.isPlaying ? player.pause : player.play}>
          {player.isPlaying ? "Pause" : "Play"}
        </button>
        <label>
          Progress
          <input
            aria-label="Track progress"
            max={player.duration || 1}
            min={0}
            onChange={(event) => player.seek(Number(event.target.value))}
            step={0.1}
            type="range"
            value={player.currentTime}
          />
        </label>
        <label>
          Volume
          <input
            aria-label="Track volume"
            max={1}
            min={0}
            onChange={(event) => player.setVolume(Number(event.target.value))}
            step={0.05}
            type="range"
            value={player.volume}
          />
        </label>
      </div>
    </section>
  );
}

export function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [brief, setBrief] = useState<MusicBrief>(emptyBrief);
  const [prompt, setPrompt] = useState("");
  const [promptWarnings, setPromptWarnings] = useState<string[]>([]);
  const [job, setJob] = useState<GenerationJob | null>(null);
  const [provenance, setProvenance] = useState<Record<string, unknown> | null>(null);
  const [status, setStatus] = useState<"idle" | "analyzing" | "prompting" | "generating">("idle");
  const [error, setError] = useState<string | null>(null);

  const validationErrors = useMemo(() => validateBrief(brief), [brief]);
  const trackSrc = job?.track ? audioUrl(job.track.audio_url) : null;

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  useEffect(() => {
    if (!job || job.status === "complete" || job.status === "failed") {
      return;
    }
    const timer = window.setInterval(async () => {
      try {
        const nextJob = await fetchJob(job.job_id);
        setJob(nextJob);
        if (nextJob.status === "complete" && nextJob.track) {
          setProvenance(await fetchProvenance(nextJob.track.track_id));
          setStatus("idle");
        }
        if (nextJob.status === "failed") {
          setError(nextJob.error ?? "The mock generation job failed.");
          setStatus("idle");
        }
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Could not poll job status.");
        setStatus("idle");
      }
    }, 900);
    return () => window.clearInterval(timer);
  }, [job]);

  function clearDownstreamState() {
    setAnalysis(null);
    setBrief(emptyBrief);
    setPrompt("");
    setPromptWarnings([]);
    setJob(null);
    setProvenance(null);
    setError(null);
  }

  function onFileChange(file: File | null) {
    clearDownstreamState();
    setSelectedFile(file);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(file ? URL.createObjectURL(file) : null);
  }

  async function runAnalysis() {
    if (!selectedFile) return;
    setStatus("analyzing");
    setError(null);
    try {
      const result = await analyzeImage(selectedFile);
      setAnalysis(result);
      setBrief(toBrief(result));
      setPrompt("");
      setPromptWarnings([]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Image analysis failed.");
    } finally {
      setStatus("idle");
    }
  }

  async function previewPrompt() {
    setStatus("prompting");
    setError(null);
    try {
      const result = await composePrompt(brief);
      setPrompt(result.prompt);
      setPromptWarnings(result.warnings);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Prompt composition failed.");
    } finally {
      setStatus("idle");
    }
  }

  async function generateTrack() {
    if (!analysis || validationErrors.length || !prompt) return;
    setStatus("generating");
    setError(null);
    setProvenance(null);
    try {
      const nextJob = await startGeneration({
        imageHash: analysis.observation.image_hash,
        analysisId: analysis.analysis_id,
        brief,
        prompt
      });
      setJob(nextJob);
      if (nextJob.status === "complete" && nextJob.track) {
        setProvenance(await fetchProvenance(nextJob.track.track_id));
        setStatus("idle");
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Mock generation failed to start.");
      setStatus("idle");
    }
  }

  return (
    <main className="shell">
      <header className="masthead">
        <div>
          <p className="eyebrow">Human-in-the-loop game audio prototype</p>
          <h1>Angel of Music</h1>
          <p>
            Upload a scene image, inspect visual observations, edit the artistic brief, and
            generate a short instrumental background cue.
          </p>
        </div>
        <aside>
          Human-reviewed analysis. No copyrighted music download, no licensing claim.
        </aside>
      </header>

      <section className="workspace">
        <section className="panel">
          <h2>1. Image</h2>
          <input
            accept="image/png,image/jpeg,image/webp"
            aria-label="Scene image"
            onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
            type="file"
          />
          {previewUrl ? <img alt="Selected scene preview" className="preview" src={previewUrl} /> : null}
          <button disabled={!selectedFile || status === "analyzing"} onClick={runAnalysis} type="button">
            {status === "analyzing" ? "Analyzing..." : "Run Analysis"}
          </button>
        </section>

        {analysis ? (
          <section className="panel">
            <h2>2. Visual Observations</h2>
            <dl className="facts">
              <div>
                <dt>Format</dt>
                <dd>{analysis.observation.format}</dd>
              </div>
              <div>
                <dt>Size</dt>
                <dd>
                  {analysis.observation.width} x {analysis.observation.height}
                </dd>
              </div>
              <div>
                <dt>Brightness</dt>
                <dd>{analysis.observation.brightness}</dd>
              </div>
              <div>
                <dt>Contrast</dt>
                <dd>{analysis.observation.contrast}</dd>
              </div>
              <div>
                <dt>Dominant Color</dt>
                <dd>{analysis.observation.dominant_color}</dd>
              </div>
            </dl>
            {analysis.observation.notes.map((note) => (
              <p className="note" key={note}>
                {note}
              </p>
            ))}
          </section>
        ) : null}

        {analysis ? (
          <section className="panel wide">
            <h2>3. Editable Music Brief</h2>
            <div className="formGrid">
              <label>
                Narrative role
                <select
                  value={brief.narrative_role}
                  onChange={(event) =>
                    setBrief({ ...brief, narrative_role: event.target.value as MusicBrief["narrative_role"] })
                  }
                >
                  {narrativeRoles.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </label>
              <label>
                Emotion
                <select
                  value={brief.emotion}
                  onChange={(event) =>
                    setBrief({ ...brief, emotion: event.target.value as MusicBrief["emotion"] })
                  }
                >
                  {emotions.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </label>
              <label>
                BPM
                <input
                  max={220}
                  min={40}
                  type="number"
                  value={brief.bpm}
                  onChange={(event) => setBrief({ ...brief, bpm: Number(event.target.value) })}
                />
              </label>
              <label>
                Duration
                <input
                  max={20}
                  min={10}
                  type="number"
                  value={brief.duration_seconds}
                  onChange={(event) =>
                    setBrief({ ...brief, duration_seconds: Number(event.target.value) })
                  }
                />
              </label>
              <label>
                Energy
                <input
                  max={1}
                  min={0}
                  step={0.01}
                  type="range"
                  value={brief.energy}
                  onChange={(event) => setBrief({ ...brief, energy: Number(event.target.value) })}
                />
              </label>
              <label>
                Emotional intensity
                <input
                  max={1}
                  min={0}
                  step={0.01}
                  type="range"
                  value={brief.emotional_intensity}
                  onChange={(event) =>
                    setBrief({ ...brief, emotional_intensity: Number(event.target.value) })
                  }
                />
              </label>
              <label>
                Musical arc
                <select
                  value={brief.musical_arc}
                  onChange={(event) =>
                    setBrief({ ...brief, musical_arc: event.target.value as MusicBrief["musical_arc"] })
                  }
                >
                  {musicalArcs.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </label>
              <label className="checkbox">
                <input
                  checked={brief.loop_requested}
                  onChange={(event) => setBrief({ ...brief, loop_requested: event.target.checked })}
                  type="checkbox"
                />
                Loop requested
              </label>
            </div>

            <fieldset>
              <legend>Textures</legend>
              {textures.map((item) => (
                <label className="chip" key={item}>
                  <input
                    checked={brief.textures.includes(item)}
                    onChange={() =>
                      setBrief({ ...brief, textures: toggleList<Texture>(brief.textures, item) })
                    }
                    type="checkbox"
                  />
                  {item}
                </label>
              ))}
            </fieldset>

            <fieldset>
              <legend>Instrument families</legend>
              {instruments.map((item) => (
                <label className="chip" key={item}>
                  <input
                    checked={brief.instruments.includes(item)}
                    onChange={() =>
                      setBrief({
                        ...brief,
                        instruments: toggleList<InstrumentFamily>(brief.instruments, item)
                      })
                    }
                    type="checkbox"
                  />
                  {item}
                </label>
              ))}
            </fieldset>

            <label>
              Avoid terms
              <input
                value={brief.avoid_terms.join(", ")}
                onChange={(event) =>
                  setBrief({
                    ...brief,
                    avoid_terms: event.target.value.split(",").map((item) => item.trim())
                  })
                }
              />
            </label>
            <label>
              Rationale
              <textarea
                value={brief.rationale}
                onChange={(event) => setBrief({ ...brief, rationale: event.target.value })}
              />
            </label>
            {validationErrors.length ? (
              <ul className="errorList">
                {validationErrors.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : null}
          </section>
        ) : null}

        {analysis ? (
          <section className="panel wide">
            <h2>4. Deterministic Prompt</h2>
            <button disabled={status === "prompting" || validationErrors.length > 0} onClick={previewPrompt}>
              {status === "prompting" ? "Composing..." : "Preview Prompt"}
            </button>
            {prompt ? <pre>{prompt}</pre> : <p className="note">Prompt preview waits for your approved brief.</p>}
            {promptWarnings.map((warning) => (
              <p className="warning" key={warning}>
                {warning}
              </p>
            ))}
          </section>
        ) : null}

        {prompt ? (
          <section className="panel">
            <h2>5. Generation Job</h2>
            <button disabled={status === "generating" || validationErrors.length > 0} onClick={generateTrack}>
              {status === "generating" ? "Starting..." : "Generate Track"}
            </button>
            {job ? (
              <p className="status">
                Job {job.job_id.slice(0, 8)}: {job.status}
              </p>
            ) : null}
            {job?.status === "failed" ? <button onClick={generateTrack}>Retry</button> : null}
          </section>
        ) : null}

        {trackSrc ? <AudioPlayer src={trackSrc} /> : null}

        {provenance ? (
          <section className="panel wide">
            <h2>Provenance And Limitations</h2>
            <pre>{JSON.stringify(provenance, null, 2)}</pre>
          </section>
        ) : null}

        {error ? <p className="error">{error}</p> : null}
      </section>
    </main>
  );
}
