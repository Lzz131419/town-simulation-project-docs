import type { Town, TownEvent } from "../types";
import { isMarketDay } from "./market-day";
import { daylight } from "./lighting";

export interface AudioSettings {
  enabled: boolean;
  volume: number;
  environment: boolean;
  ambience: boolean;
}
export const AUDIO_SETTINGS_KEY = "mist-river-audio-v1";
export function defaultAudioSettings(reducedMotion: boolean): AudioSettings {
  return {
    enabled: true,
    volume: 0.35,
    environment: !reducedMotion,
    ambience: true,
  };
}
export function readAudioSettings(): AudioSettings {
  const defaults = defaultAudioSettings(
    window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  try {
    const saved = JSON.parse(
      localStorage.getItem(AUDIO_SETTINGS_KEY) ?? "null",
    );
    if (!saved || typeof saved !== "object") return defaults;
    for (const key of ["enabled", "environment", "ambience"] as const)
      if (typeof saved[key] === "boolean") defaults[key] = saved[key];
    if (typeof saved.volume === "number" && Number.isFinite(saved.volume))
      defaults.volume = Math.max(0, Math.min(1, saved.volume));
  } catch {
    /* Storage may be disabled; sound still works for this session. */
  }
  return defaults;
}

export interface Voice {
  wave: "sine" | "triangle" | "noise";
  hz: number;
  endHz?: number;
  delay: number;
  duration: number;
  gain: number;
}
export interface Sound {
  kind:
    | "harvest"
    | "make"
    | "coin"
    | "delivery"
    | "eat"
    | "social"
    | "blocked"
    | "sleep"
    | "family";
  voices: Voice[];
}
const harvest = [
  "farm",
  "harvest_veg",
  "gather",
  "gather_honey",
  "harvest_flax",
  "forage",
  "mine",
  "chop",
  "fish",
];
const make = [
  "bake",
  "weave",
  "assemble",
  "forge",
  "craft",
  "cook",
  "grill",
  "brew",
];
const tone = (
  hz: number,
  duration: number,
  gain: number,
  delay = 0,
  wave: Voice["wave"] = "sine",
  endHz?: number,
): Voice => ({ wave, hz, endHz, delay, duration, gain });

// Pure timbre descriptions, shared by the renderer and tests. Times are seconds.
export function soundForEvent(
  event: Pick<TownEvent, "type" | "details">,
): Sound | null {
  const type = event.type;
  if (type === "family") {
    const kind = event.details?.kind;
    return {
      kind: "family",
      voices:
        kind === "quarrel"
          ? [tone(165, 0.28, 0.1, 0, "triangle", 110)]
          : kind === "reconcile"
            ? [262, 330, 392].map((hz) => tone(hz, 0.5, 0.07))
            : [262, 330].map((hz, i) => tone(hz, 0.35, 0.08, i * 0.12)),
    };
  }
  const index = harvest.indexOf(type);
  if (index >= 0)
    return { kind: "harvest", voices: [tone(740 + index * 35, 0.24, 0.16)] };
  if (make.includes(type))
    return {
      kind: "make",
      voices: [
        tone(180, 0.17, 0.2, 0, "sine", 70),
        tone(950, 0.035, 0.05, 0, "noise"),
      ],
    };
  if (
    type === "buy" ||
    type === "sell" ||
    (type === "order" && event.details?.transaction_type === "filled")
  )
    return {
      kind: "coin",
      voices: [0, 0.09].flatMap((delay) => [
        tone(1320, 0.1, 0.09, delay),
        tone(2112, 0.07, 0.035, delay),
      ]),
    };
  if (type === "delivery")
    return {
      kind: "delivery",
      voices: [523, 659, 784].map((hz, i) => tone(hz, 0.18, 0.12, i * 0.11)),
    };
  if (type === "eat" || type.startsWith("eat_"))
    return {
      kind: "eat",
      voices: [
        tone(700, 0.045, 0.1, 0, "noise"),
        tone(550, 0.04, 0.08, 0.08, "noise"),
      ],
    };
  if (type === "sleep" || type === "wake")
    return {
      kind: "sleep",
      voices: [
        tone(
          type === "sleep" ? 392 : 523,
          0.38,
          0.045,
          0,
          "sine",
          type === "sleep"
            ? 262
            : event.details?.reason === "disturbed"
              ? 392
              : 659,
        ),
      ],
    };
  if (["social", "gift", "feast"].includes(type))
    return {
      kind: "social",
      voices: [tone(330, 0.32, 0.09), tone(415, 0.32, 0.08)],
    };
  if (["blocked", "failed", "failure"].includes(type))
    return {
      kind: "blocked",
      voices: [tone(130, 0.19, 0.12, 0, "triangle", 65)],
    };
  return null;
}

export function environmentFor(
  world: Pick<Town, "tick" | "weather" | "season" | "market_day"> | null,
  settings: AudioSettings,
) {
  const enabled = Boolean(
    world && settings.enabled && settings.environment && settings.ambience,
  );
  const winter = world?.season === "winter";
  return {
    market:
      enabled &&
      world &&
      isMarketDay(world) &&
      (world.tick * 10 + 480) % 1440 >= 360 &&
      (world.tick * 10 + 480) % 1440 < 1140
        ? 0.018
        : 0,
    rain: enabled
      ? world?.weather === "storm"
        ? 0.1
        : world?.weather === "rain"
          ? 0.055
          : 0
      : 0,
    rainHz: world?.weather === "storm" ? 2200 : 1400,
    wind: enabled
      ? winter
        ? 0.035
        : world?.weather === "cloudy"
          ? 0.012
          : 0
      : 0,
    windHz: winter ? 1100 : 380,
    crickets:
      enabled && !winter ? (daylight(world!.tick).night / 0.34) * 0.045 : 0,
  };
}

interface Loop {
  source: AudioBufferSourceNode;
  filter: BiquadFilterNode;
  gain: GainNode;
}
export class TownAudio {
  private context?: AudioContext;
  private master?: GainNode;
  private cricketGain?: GainNode;
  private marketGain?: GainNode;
  private nextMarketChime = 0;
  private loops: Loop[] = [];
  private noise?: AudioBuffer;
  private settings = defaultAudioSettings(false);
  private world: Pick<
    Town,
    "tick" | "weather" | "season" | "market_day"
  > | null = null;
  private lastEventId = -1;
  private seeded = false;
  private installed = false;
  private disposed = false;
  private chirpTimer?: ReturnType<typeof setInterval>;
  private nextSoundAt = 0;
  private activeSources = new Set<AudioScheduledSourceNode>();
  private targets = new WeakMap<AudioParam, number>();

  constructor(
    private createContext: () => AudioContext = () => new AudioContext(),
  ) {}

  install() {
    if (this.installed || this.disposed) return;
    this.installed = true;
    document.addEventListener("pointerdown", this.unlock);
    document.addEventListener("keydown", this.unlock);
    document.addEventListener("click", this.unlock);
    document.addEventListener("visibilitychange", this.visibility);
  }

  private unlock = () => {
    if (
      this.disposed ||
      !this.settings.enabled ||
      !this.world ||
      document.hidden
    )
      return;
    try {
      if (!this.context) {
        const ctx = this.createContext();
        this.context = ctx;
        this.master = ctx.createGain();
        this.master.gain.value = 0;
        this.master.connect(ctx.destination);
        this.noise = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate);
        const channel = this.noise.getChannelData(0);
        for (let i = 0; i < channel.length; i++)
          channel[i] = Math.random() * 2 - 1;
        this.loops = [
          this.loop("lowpass"),
          this.loop("bandpass"),
          this.loop("lowpass"),
        ];
        this.marketGain = ctx.createGain();
        this.marketGain.gain.value = 0;
        this.marketGain.connect(this.master);
        this.cricketGain = ctx.createGain();
        this.cricketGain.gain.value = 0;
        this.cricketGain.connect(this.master);
        this.chirpTimer = setInterval(() => this.chirp(), 1700);
        this.sync();
      }
      if (this.context.state !== "running")
        void this.context.resume().catch(() => {});
    } catch {
      /* Unsupported/denied audio must never interrupt world updates. */
    }
  };

  private visibility = () => {
    if (document.hidden) {
      this.stopVoices();
      if (this.context?.state === "running")
        void this.context.suspend().catch(() => {});
    } else if (this.context) this.unlock();
  };

  configure(
    settings: AudioSettings,
    world: Pick<Town, "tick" | "weather" | "season" | "market_day"> | null,
  ) {
    this.settings = {
      ...settings,
      volume: Number.isFinite(settings.volume)
        ? Math.max(0, Math.min(1, settings.volume))
        : 0,
    };
    this.world = world;
    if (!world || !settings.enabled || !settings.volume) this.stopVoices();
    this.sync();
  }

  private ramp(param: AudioParam, value: number, duration = 0.7) {
    if (!this.context || this.targets.get(param) === value) return;
    this.targets.set(param, value);
    const now = this.context.currentTime;
    // Hold the *current* interpolated value when a transition is interrupted.
    if (typeof param.cancelAndHoldAtTime === "function")
      param.cancelAndHoldAtTime(now);
    else {
      param.cancelScheduledValues(now);
      param.setValueAtTime(param.value, now);
    }
    param.linearRampToValueAtTime(value, now + duration);
  }

  private sync() {
    if (!this.master) return;
    const env = environmentFor(this.world, this.settings);
    this.ramp(
      this.master.gain,
      this.world && this.settings.enabled ? this.settings.volume : 0,
      0.06,
    );
    this.ramp(this.loops[0].gain.gain, env.rain);
    this.ramp(this.loops[0].filter.frequency, env.rainHz);
    this.ramp(this.loops[1].gain.gain, env.wind);
    this.ramp(this.loops[1].filter.frequency, env.windHz);
    this.ramp(this.cricketGain!.gain, env.crickets);
    this.ramp(this.loops[2].gain.gain, env.market);
    this.ramp(this.loops[2].filter.frequency, 430);
    this.ramp(this.marketGain!.gain, env.market);
  }

  private loop(type: BiquadFilterType): Loop {
    const ctx = this.context!;
    const source = ctx.createBufferSource(),
      filter = ctx.createBiquadFilter(),
      gain = ctx.createGain();
    source.buffer = this.noise!;
    source.loop = true;
    filter.type = type;
    filter.Q.value = 0.5;
    gain.gain.value = 0;
    source.connect(filter);
    filter.connect(gain);
    gain.connect(this.master!);
    source.start();
    return { source, filter, gain };
  }

  // Consume every accepted packet, even muted/locked, so old sounds never replay.
  consume(events: TownEvent[], self: string | undefined) {
    const previous = this.lastEventId;
    for (const event of events)
      this.lastEventId = Math.max(this.lastEventId, event.id);
    if (!this.seeded) {
      this.seeded = true;
      return;
    }
    let count = 0;
    const seen = new Set<number>();
    for (const event of [...events].sort((a, b) => a.id - b.id)) {
      if (
        event.id <= previous ||
        seen.has(event.id) ||
        !self ||
        (event.actor_id !== self && event.type !== "family")
      )
        continue;
      seen.add(event.id);
      const sound = soundForEvent(event);
      if (sound && count++ < 3) this.play(sound);
    }
  }

  play(sound: Sound) {
    const ctx = this.context;
    if (
      !ctx ||
      ctx.state !== "running" ||
      document.hidden ||
      !this.world ||
      !this.settings.enabled ||
      this.settings.volume === 0
    )
      return;
    // Bound burst playback to <= 3 short cues, with no growing backlog.
    if (this.nextSoundAt > ctx.currentTime + 0.45) return;
    const at = Math.max(ctx.currentTime, this.nextSoundAt);
    this.nextSoundAt = at + 0.18;
    for (const voice of sound.voices) this.voice(voice, at, this.master!);
  }

  private voice(voice: Voice, at: number, destination: AudioNode) {
    const ctx = this.context!,
      start = at + voice.delay;
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0, start);
    gain.gain.linearRampToValueAtTime(voice.gain, start + 0.006);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + voice.duration);
    gain.gain.linearRampToValueAtTime(0, start + voice.duration + 0.01);
    gain.connect(destination);
    let source: AudioScheduledSourceNode;
    let filter: BiquadFilterNode | undefined;
    if (voice.wave === "noise") {
      const noise = ctx.createBufferSource();
      noise.buffer = this.noise!;
      filter = ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.value = voice.hz;
      noise.connect(filter);
      filter.connect(gain);
      source = noise;
    } else {
      const oscillator = ctx.createOscillator();
      oscillator.type = voice.wave;
      oscillator.frequency.setValueAtTime(voice.hz, start);
      if (voice.endHz)
        oscillator.frequency.exponentialRampToValueAtTime(
          voice.endHz,
          start + voice.duration,
        );
      oscillator.connect(gain);
      source = oscillator;
    }
    this.activeSources.add(source);
    source.onended = () => {
      source.disconnect();
      filter?.disconnect();
      gain.disconnect();
      this.activeSources.delete(source);
    };
    source.start(start);
    source.stop(start + voice.duration + 0.015);
  }

  private chirp() {
    const ctx = this.context;
    if (
      !ctx ||
      ctx.state !== "running" ||
      document.hidden ||
      this.settings.volume === 0
    )
      return;
    const env = environmentFor(this.world, this.settings);
    if (env.market > 0 && ctx.currentTime >= this.nextMarketChime) {
      this.voice(tone(1568, 0.14, 0.22), ctx.currentTime, this.marketGain!);
      this.nextMarketChime = ctx.currentTime + 6.8;
    }
    if (env.crickets === 0) return;
    for (let i = 0; i < 3; i++)
      this.voice(
        tone(3600, 0.045, 0.3, i * 0.085, "sine", 4100),
        ctx.currentTime,
        this.cricketGain!,
      );
  }

  private stopVoices() {
    for (const source of this.activeSources) {
      try {
        source.stop();
      } catch {
        /* Already ended. */
      }
    }
    this.nextSoundAt = 0;
  }

  reset() {
    this.lastEventId = -1;
    this.seeded = false;
    this.configure(this.settings, null);
  }

  dispose() {
    this.disposed = true;
    document.removeEventListener("pointerdown", this.unlock);
    document.removeEventListener("keydown", this.unlock);
    document.removeEventListener("click", this.unlock);
    document.removeEventListener("visibilitychange", this.visibility);
    clearInterval(this.chirpTimer);
    this.stopVoices();
    for (const loop of this.loops) {
      loop.source.stop();
      loop.source.disconnect();
      loop.filter.disconnect();
      loop.gain.disconnect();
    }
    this.master?.disconnect();
    this.cricketGain?.disconnect();
    this.marketGain?.disconnect();
    if (this.context) void this.context.close().catch(() => {});
  }
}
