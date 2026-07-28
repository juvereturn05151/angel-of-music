import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach, vi } from "vitest";

Object.defineProperty(URL, "createObjectURL", {
  value: () => "blob:mock-preview"
});

Object.defineProperty(URL, "revokeObjectURL", {
  value: () => undefined
});

class MockAudio extends EventTarget {
  static playCalls = 0;
  src = "";
  preload = "";
  volume = 1;
  currentTime = 0;
  duration = 14;

  play = vi.fn(async () => {
    MockAudio.playCalls += 1;
  });

  pause = vi.fn();
}

Object.defineProperty(window, "Audio", {
  value: MockAudio
});

Object.defineProperty(window, "AudioContext", {
  value: class {
    state = "running";
    resume = vi.fn(async () => undefined);
  }
});

beforeEach(() => {
  MockAudio.playCalls = 0;
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

export { MockAudio };
