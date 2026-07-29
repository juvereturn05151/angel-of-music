import { useEffect, useMemo, useState } from "react";

import {
  analyzeImage,
  audioUrl,
  composePrompt,
  fetchJob,
  startGeneration
} from "./api";
import type { AnalysisResponse, GenerationJob, MusicBrief } from "./types";
import { useAudioPlayer } from "./useAudioPlayer";

import "./styles.css";

const emptyBrief: MusicBrief = {
  purpose: "temporary background music for game prototype mood communication",
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
  vocals: "disabled",
  custom_narrative_role: null,
  custom_emotion: null
};

function toBrief(analysis: AnalysisResponse): MusicBrief {
  return {
    ...analysis.inference,
    purpose: "temporary background music for game prototype mood communication",
    vocals: "disabled",
    custom_narrative_role: null,
    custom_emotion: null
  };
}

function validateBrief(brief: MusicBrief): string[] {
  const errors: string[] = [];
  if (brief.bpm < 40 || brief.bpm > 220) errors.push("BPM must be between 40 and 220.");
  if (brief.duration_seconds < 10 || brief.duration_seconds > 120) {
    errors.push("Duration must be between 10 and 120 seconds.");
  }
  if (!brief.purpose.trim()) errors.push("Purpose is required.");
  if (!brief.rationale.trim()) errors.push("Mood overview is required.");
  return errors;
}

function trackDownloadName(job: GenerationJob): string {
  const filename = job.track?.audio_filename;
  if (filename) return filename;
  const extension = job.track?.audio_url.endsWith(".mp3") ? "mp3" : "wav";
  return `angel-of-music-${job.track?.track_id.slice(0, 8) ?? "track"}.${extension}`;
}

function AudioPlayer({
  downloadName,
  src
}: {
  downloadName: string;
  src: string;
}) {
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
        <a className="downloadLink" download={downloadName} href={src}>
          Download Track
        </a>
      </div>
    </section>
  );
}

export function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [brief, setBrief] = useState<MusicBrief>(emptyBrief);
  const [job, setJob] = useState<GenerationJob | null>(null);
  const [status, setStatus] = useState<"idle" | "analyzing" | "generating">("idle");
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
    setJob(null);
    setError(null);
  }

  function updateBrief(nextBrief: MusicBrief) {
    setBrief(nextBrief);
    setJob(null);
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
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Image analysis failed.");
    } finally {
      setStatus("idle");
    }
  }

  async function generateTrack() {
    if (!analysis || validationErrors.length) return;
    setStatus("generating");
    setError(null);
    try {
      const promptResponse = await composePrompt(brief);
      const nextJob = await startGeneration({
        imageHash: analysis.observation.image_hash,
        analysisId: analysis.analysis_id,
        brief,
        prompt: promptResponse.prompt
      });
      setJob(nextJob);
      if (nextJob.status === "complete" && nextJob.track) {
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
            generate a short background cue.
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
              <label className="spanTwo">
                1. Purpose
                <input
                  value={brief.purpose}
                  onChange={(event) => updateBrief({ ...brief, purpose: event.target.value })}
                />
              </label>
              <label className="spanTwo">
                2. Mood Overview
                <textarea
                  value={brief.rationale}
                  onChange={(event) => updateBrief({ ...brief, rationale: event.target.value })}
                />
              </label>
              <label>
                3. BPM
                <input
                  max={220}
                  min={40}
                  type="number"
                  value={brief.bpm}
                  onChange={(event) => updateBrief({ ...brief, bpm: Number(event.target.value) })}
                />
              </label>
              <label>
                4. Duration (seconds, up to 120)
                <input
                  max={120}
                  min={10}
                  type="number"
                  value={brief.duration_seconds}
                  onChange={(event) =>
                    updateBrief({ ...brief, duration_seconds: Number(event.target.value) })
                  }
                />
              </label>
              <label className="checkbox">
                <input
                  checked={brief.loop_requested}
                  onChange={(event) => updateBrief({ ...brief, loop_requested: event.target.checked })}
                  type="checkbox"
                />
                5. Loop
              </label>
              <label>
                6. Vocals
                <select
                  value={brief.vocals}
                  onChange={(event) => {
                    const vocals = event.target.value as MusicBrief["vocals"];
                    const avoidTerms =
                      vocals === "enabled"
                        ? brief.avoid_terms.filter((item) => item.toLowerCase() !== "vocals")
                        : Array.from(new Set([...brief.avoid_terms, "vocals"]));
                    updateBrief({ ...brief, vocals, avoid_terms: avoidTerms });
                  }}
                >
                  <option value="disabled">No vocals</option>
                  <option value="enabled">Allow vocals</option>
                </select>
              </label>
            </div>
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
          <section className="panel">
            <h2>4. Generation Job</h2>
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

        {trackSrc && job ? (
          <AudioPlayer downloadName={trackDownloadName(job)} src={trackSrc} />
        ) : null}

        {error ? <p className="error">{error}</p> : null}
      </section>
    </main>
  );
}
