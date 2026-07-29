import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { MockAudio } from "./test/setup";

const analysis = {
  analysis_id: "analysis-1",
  normalized_image_id: "image-1",
  analyzer: "mock-visual-analyzer",
  analyzer_version: "1.0",
  limitations: ["Mock output is for workflow testing."],
  observation: {
    image_hash: "a".repeat(64),
    width: 64,
    height: 48,
    format: "PNG",
    dominant_color: "#778899",
    brightness: "balanced",
    contrast: "moderate",
    aspect_ratio: "64:48",
    notes: ["Mock analysis uses decoded image properties only."]
  },
  inference: {
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
    rationale: "Mock rationale."
  }
};

function jsonResponse(body: unknown, ok = true) {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status: ok ? 200 : 400,
      headers: { "Content-Type": "application/json" }
    })
  );
}

function installHappyFetch() {
  const job = {
    job_id: "job-1",
    status: "complete",
    created_at: "2026-07-28T00:00:00Z",
    updated_at: "2026-07-28T00:00:01Z",
    error: null,
    track: {
      track_id: "track-1",
      job_id: "job-1",
      duration_seconds: 14,
      audio_url: "/api/tracks/track-1/audio",
      audio_filename: "track-1.mp3",
      audio_sha256: "b".repeat(64),
      created_at: "2026-07-28T00:00:01Z"
    }
  };
  globalThis.fetch = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/api/analyze-image")) return jsonResponse(analysis);
    if (url.includes("/api/compose-prompt")) {
      return jsonResponse({ prompt: "vocals: disabled bpm: 84", warnings: [] });
    }
    if (url.includes("/api/generate")) return jsonResponse(job);
    if (url.includes("/api/tracks/track-1/provenance")) {
      return jsonResponse({ schema_version: "1.0", image_hash: "a".repeat(64) });
    }
    return jsonResponse({});
  }) as typeof fetch;
}

describe("App", () => {
  it("shows the initial upload workflow", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Angel of Music" })).toBeInTheDocument();
    expect(screen.getByLabelText("Scene image")).toBeInTheDocument();
    expect(screen.getByText(/Human-reviewed analysis/i)).toBeInTheDocument();
  });

  it("analyzes an image and lets the user edit the mood overview", async () => {
    installHappyFetch();
    const user = userEvent.setup();
    render(<App />);

    await user.upload(
      screen.getByLabelText("Scene image"),
      new File(["x"], "scene.png", { type: "image/png" })
    );
    await user.click(screen.getByRole("button", { name: /Run Analysis/i }));

    expect(await screen.findByText(/Visual Observations/)).toBeInTheDocument();
    await user.clear(screen.getByLabelText("2. Mood Overview"));
    await user.type(screen.getByLabelText("2. Mood Overview"), "gentle comic tension");
    expect(screen.getByLabelText("2. Mood Overview")).toHaveValue("gentle comic tension");
  });

  it("lets the user choose whether vocals are allowed", async () => {
    installHappyFetch();
    const user = userEvent.setup();
    render(<App />);

    await user.upload(
      screen.getByLabelText("Scene image"),
      new File(["x"], "scene.png", { type: "image/png" })
    );
    await user.click(screen.getByRole("button", { name: /Run Analysis/i }));
    const vocals = await screen.findByLabelText("Vocals");

    expect(vocals).toHaveValue("disabled");
    await user.selectOptions(vocals, "enabled");
    expect(vocals).toHaveValue("enabled");
  });

  it("lets the user edit the prompt purpose", async () => {
    installHappyFetch();
    const user = userEvent.setup();
    render(<App />);

    await user.upload(
      screen.getByLabelText("Scene image"),
      new File(["x"], "scene.png", { type: "image/png" })
    );
    await user.click(screen.getByRole("button", { name: /Run Analysis/i }));
    const purpose = await screen.findByLabelText("1. Purpose");

    await user.clear(purpose);
    await user.type(purpose, "temporary village theme for a cozy quest hub");

    expect(purpose).toHaveValue("temporary village theme for a cozy quest hub");
  });

  it("clears stale prompt data when the image changes", async () => {
    installHappyFetch();
    const user = userEvent.setup();
    render(<App />);

    await user.upload(
      screen.getByLabelText("Scene image"),
      new File(["x"], "scene.png", { type: "image/png" })
    );
    await user.click(screen.getByRole("button", { name: /Run Analysis/i }));
    await user.click(await screen.findByRole("button", { name: /Preview Prompt/i }));
    expect(await screen.findByText(/vocals: disabled/)).toBeInTheDocument();

    await user.upload(
      screen.getByLabelText("Scene image"),
      new File(["y"], "second.png", { type: "image/png" })
    );

    expect(screen.queryByText(/vocals: disabled/)).not.toBeInTheDocument();
  });

  it("generates a completed track and plays without duplicate play calls", async () => {
    installHappyFetch();
    const user = userEvent.setup();
    render(<App />);

    await user.upload(
      screen.getByLabelText("Scene image"),
      new File(["x"], "scene.png", { type: "image/png" })
    );
    await user.click(screen.getByRole("button", { name: /Run Analysis/i }));
    await user.click(await screen.findByRole("button", { name: /Preview Prompt/i }));
    await user.click(await screen.findByRole("button", { name: /Generate Track/i }));

    expect(await screen.findByText("Track Result")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Download Track" })).toHaveAttribute(
      "download",
      "track-1.mp3"
    );
    const play = screen.getByRole("button", { name: "Play" });
    await user.click(play);
    await user.click(play);

    await waitFor(() => expect(MockAudio.playCalls).toBe(1));
  });

  it("shows API errors", async () => {
    globalThis.fetch = vi.fn(() => jsonResponse({ detail: "Bad image" }, false)) as typeof fetch;
    const user = userEvent.setup();
    render(<App />);

    await user.upload(
      screen.getByLabelText("Scene image"),
      new File(["x"], "scene.png", { type: "image/png" })
    );
    await user.click(screen.getByRole("button", { name: /Run Analysis/i }));

    expect(await screen.findByText("Bad image")).toBeInTheDocument();
  });
});
