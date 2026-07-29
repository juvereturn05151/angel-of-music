export type NarrativeRole =
  | "exploration"
  | "danger"
  | "mystery"
  | "discovery"
  | "combat"
  | "victory"
  | "loss"
  | "character-theme"
  | "transition"
  | "other";

export type Emotion =
  | "peaceful"
  | "tense"
  | "mysterious"
  | "heroic"
  | "melancholic"
  | "playful"
  | "frightening"
  | "hopeful"
  | "ambiguous"
  | "other";

export type Texture =
  | "warm"
  | "dark"
  | "bright"
  | "sparse"
  | "dense"
  | "organic"
  | "mechanical"
  | "ethereal"
  | "distorted";

export type InstrumentFamily =
  | "strings"
  | "piano"
  | "brass"
  | "woodwinds"
  | "percussion"
  | "synthesizer"
  | "choir-like-pad"
  | "guitar"
  | "bass"
  | "bells";

export type MusicalArc =
  | "steady"
  | "gradual-build"
  | "gradual-release"
  | "rising-tension"
  | "dramatic-hit"
  | "unresolved"
  | "loop-friendly";

export interface VisualObservation {
  image_hash: string;
  width: number;
  height: number;
  format: "JPEG" | "PNG" | "WEBP";
  dominant_color: string;
  brightness: "dark" | "balanced" | "bright";
  contrast: "low" | "moderate" | "high";
  aspect_ratio: string;
  notes: string[];
}

export interface ArtisticInference {
  narrative_role: NarrativeRole;
  emotion: Emotion;
  textures: Texture[];
  energy: number;
  emotional_intensity: number;
  bpm: number;
  duration_seconds: number;
  instruments: InstrumentFamily[];
  musical_arc: MusicalArc;
  loop_requested: boolean;
  avoid_terms: string[];
  rationale: string;
}

export interface MusicBrief extends ArtisticInference {
  purpose: string;
  vocals: "disabled" | "enabled";
  custom_narrative_role: string | null;
  custom_emotion: string | null;
}

export interface AnalysisResponse {
  analysis_id: string;
  observation: VisualObservation;
  inference: ArtisticInference;
  normalized_image_id: string;
  limitations: string[];
  analyzer: string;
  analyzer_version: string;
}

export interface PromptResponse {
  prompt: string;
  warnings: string[];
}

export interface GeneratedTrack {
  track_id: string;
  job_id: string;
  duration_seconds: number;
  audio_url: string;
  audio_filename: string;
  audio_sha256: string;
  created_at: string;
}

export interface GenerationJob {
  job_id: string;
  status: "queued" | "generating" | "analyzing" | "complete" | "failed";
  created_at: string;
  updated_at: string;
  error: string | null;
  track: GeneratedTrack | null;
}
