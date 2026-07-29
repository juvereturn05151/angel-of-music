import type { Emotion, InstrumentFamily, MusicalArc, NarrativeRole, Texture } from "./types";

export const narrativeRoles: NarrativeRole[] = [
  "exploration",
  "danger",
  "mystery",
  "discovery",
  "combat",
  "victory",
  "loss",
  "character-theme",
  "transition",
  "other"
];

export const emotions: Emotion[] = [
  "peaceful",
  "tense",
  "mysterious",
  "heroic",
  "melancholic",
  "playful",
  "frightening",
  "hopeful",
  "ambiguous",
  "other"
];

export const textures: Texture[] = [
  "warm",
  "dark",
  "bright",
  "sparse",
  "dense",
  "organic",
  "mechanical",
  "ethereal",
  "distorted"
];

export const instruments: InstrumentFamily[] = [
  "strings",
  "piano",
  "brass",
  "woodwinds",
  "percussion",
  "synthesizer",
  "choir-like-pad",
  "guitar",
  "bass",
  "bells"
];

export const musicalArcs: MusicalArc[] = [
  "steady",
  "gradual-build",
  "gradual-release",
  "rising-tension",
  "dramatic-hit",
  "unresolved",
  "loop-friendly"
];
