import argparse
import math
import random
import struct
import wave
from pathlib import Path

import pygame


SAMPLE_RATE = 22050
AMP = 0.45


def clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v


def tri(freq: float, t: float) -> float:
    return (2.0 / math.pi) * math.asin(math.sin(2 * math.pi * freq * t))


def sq(freq: float, t: float) -> float:
    return 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0


def build_track(path: Path, seed: int) -> None:
    rng = random.Random(seed)
    bpm = rng.randint(95, 145)
    beat_sec = 60.0 / bpm
    steps = 128
    total_samples = int(SAMPLE_RATE * beat_sec * steps)

    # ii-V-I flavored progressions in different keys.
    roots = [110.0, 116.54, 123.47, 130.81, 146.83, 164.81]
    root = roots[seed % len(roots)]
    ii = root * 1.12246
    v = root * 1.33484
    i = root
    vi = root * 1.68179
    progression = [(ii, 3), (v, 3), (i, 6), (vi, 2), (v, 2)]

    timeline = []
    for chord_root, bars in progression:
        # minor7 / dominant7 / major7 voicing approximation.
        timeline.extend([chord_root] * (bars * 4))

    pcm = bytearray()
    swing = 0.58 + (seed % 4) * 0.03

    for n in range(total_samples):
        t = n / SAMPLE_RATE
        beat = t / beat_sec
        bar_beat = int(beat) % len(timeline)
        c = timeline[bar_beat]

        # Chord tones.
        third = c * (1.18921 if (bar_beat % 4) in (0, 1) else 1.25992)
        fifth = c * 1.49831
        seventh = c * (1.7818 if (bar_beat % 4) in (0, 1) else 1.88775)

        # Swing timing for lead accents.
        frac = beat - int(beat)
        swung = frac / swing if frac < swing else (frac - swing) / (1.0 - swing)
        pulse = max(0.0, 1.0 - swung * 3.5)

        bass = 0.22 * tri(c / 2.0, t)
        keys = 0.11 * sq(c, t) + 0.09 * sq(third * 0.997, t) + 0.08 * sq(fifth * 1.003, t) + 0.06 * sq(seventh, t)
        lead_freq = [c * 2.0, third * 2.0, fifth * 2.0, seventh * 2.0][(int(beat * 2) + seed) % 4]
        lead = 0.12 * tri(lead_freq, t) * pulse

        # Brush-like drums.
        local = frac
        kick_env = max(0.0, 1.0 - local * 8.0) if int(beat) % 4 == 0 else 0.0
        kick = 0.30 * math.sin(2 * math.pi * (50 + 40 * kick_env) * t) * kick_env
        snare_hit = int(beat) % 4 in (1, 3)
        snare_env = max(0.0, 1.0 - local * 16.0) if snare_hit else 0.0
        brush = (math.sin(2 * math.pi * 1800 * t) + math.sin(2 * math.pi * 2400 * t)) * 0.5
        snare = 0.10 * brush * snare_env
        hat_env = max(0.0, 1.0 - ((beat * 2) % 1.0) * 14.0)
        hat = 0.05 * math.sin(2 * math.pi * 3500 * t) * hat_env

        sample = (bass + keys + lead + kick + snare + hat) * AMP
        sample = clamp(sample, -1.0, 1.0)
        pcm.extend(struct.pack("<h", int(sample * 32767)))

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(bytes(pcm))


def play_tracks(paths: list[Path], volume: float) -> None:
    pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
    pygame.mixer.music.set_volume(clamp(volume, 0.0, 1.0))
    for i, p in enumerate(paths, start=1):
        print(f"Playing {i}/10: {p.name}")
        pygame.mixer.music.load(str(p))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(80)
    pygame.mixer.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and play 10 different jazz tracks.")
    parser.add_argument("--out-dir", default="src/jazz_tracks", help="Directory where WAV files are stored.")
    parser.add_argument("--volume", type=float, default=0.45, help="Playback volume (0.0-1.0).")
    parser.add_argument("--no-play", action="store_true", help="Generate only, do not play.")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tracks = []
    for i in range(10):
        track_path = out_dir / f"jazz_track_{i + 1:02d}.wav"
        build_track(track_path, seed=100 + i * 17)
        tracks.append(track_path)
    print(f"Generated {len(tracks)} tracks in {out_dir}")

    if not args.no_play:
        play_tracks(tracks, volume=args.volume)


if __name__ == "__main__":
    main()
