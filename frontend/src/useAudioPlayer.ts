import { useEffect, useRef, useState } from "react";

export function useAudioPlayer(src: string | null) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const contextRef = useRef<AudioContext | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [volume, setVolumeState] = useState(0.75);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!src) {
      return;
    }
    const audio = new Audio(src);
    audio.preload = "metadata";
    audio.volume = volume;
    audioRef.current = audio;
    const onLoaded = () => setDuration(Number.isFinite(audio.duration) ? audio.duration : 0);
    const onTime = () => setCurrentTime(audio.currentTime);
    const onEnded = () => setIsPlaying(false);
    const onError = () => {
      setError("The mock track could not be loaded or decoded.");
      setIsPlaying(false);
    };
    audio.addEventListener("loadedmetadata", onLoaded);
    audio.addEventListener("timeupdate", onTime);
    audio.addEventListener("ended", onEnded);
    audio.addEventListener("error", onError);
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);
    setError(null);
    return () => {
      audio.pause();
      audio.src = "";
      audio.removeEventListener("loadedmetadata", onLoaded);
      audio.removeEventListener("timeupdate", onTime);
      audio.removeEventListener("ended", onEnded);
      audio.removeEventListener("error", onError);
      audioRef.current = null;
    };
  }, [src]);

  async function play() {
    const audio = audioRef.current;
    if (!audio || isPlaying) {
      return;
    }
    const AudioContextCtor = window.AudioContext ?? window.webkitAudioContext;
    if (AudioContextCtor && !contextRef.current) {
      contextRef.current = new AudioContextCtor();
    }
    if (contextRef.current?.state === "suspended") {
      await contextRef.current.resume();
    }
    await audio.play();
    setIsPlaying(true);
  }

  function pause() {
    audioRef.current?.pause();
    setIsPlaying(false);
  }

  function seek(value: number) {
    const audio = audioRef.current;
    if (!audio) {
      return;
    }
    audio.currentTime = value;
    setCurrentTime(value);
  }

  function setVolume(value: number) {
    setVolumeState(value);
    if (audioRef.current) {
      audioRef.current.volume = value;
    }
  }

  return { isPlaying, duration, currentTime, volume, error, play, pause, seek, setVolume };
}
