#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procedurally generate every sound effect and the ambient music
for "The Last 10 Questions".  Standard library only.

Run:  python generate_sounds.py
"""

import math
import os
import random
import wave
from array import array

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(HERE, "sounds")
MUSIC_DIR = os.path.join(HERE, "music")


# ------------------------------------------------------------------
#  helpers
# ------------------------------------------------------------------
def silence(duration):
    return [0.0] * int(duration * SR)


def fade_tail(buf, ms=15):
    n = min(len(buf), int(SR * ms / 1000))
    for i in range(n):
        buf[-(i + 1)] *= i / float(n)


def normalize(buf, peak=0.85):
    peak_now = max(max(buf), -min(buf)) if buf else 0.0
    if peak_now <= 0.0:
        return
    gain = peak / peak_now
    for i in range(len(buf)):
        buf[i] *= gain


def write_wav(path, left, right=None):
    """Write float buffers (-1..1) as 16-bit PCM."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if right is None:
        right = left
    frames = array("h")
    for i in range(len(left)):
        l = max(-32767, min(32767, int(left[i] * 32767)))
        frames.append(l)
        r = max(-32767, min(32767, int(right[i] * 32767)))
        frames.append(r)
    with wave.open(path, "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(frames.tobytes())
    print("  wrote", os.path.basename(path))


def loop_freq(freq, duration=12.0):
    """Round a frequency so whole cycles fit inside the loop."""
    return round(freq * duration) / float(duration)


# ------------------------------------------------------------------
#  sound effects
# ------------------------------------------------------------------
def make_correct():
    dur = 0.55
    buf = silence(dur)

    def note(start, freq, length, amp):
        s = int(start * SR)
        count = int(length * SR)
        for i in range(count):
            idx = s + i
            if idx >= len(buf):
                break
            t = i / float(SR)
            env = min(1.0, t / 0.006) * math.exp(-t * 11.0)
            if t > length - 0.03:
                env *= max(0.0, (length - t) / 0.03)
            buf[idx] += amp * env * (
                math.sin(2 * math.pi * freq * t)
                + 0.35 * math.sin(4 * math.pi * freq * t))

    note(0.00, 783.99, 0.30, 0.50)   # G5
    note(0.14, 1046.50, 0.40, 0.45)  # C6
    normalize(buf, 0.80)
    fade_tail(buf)
    return buf


def make_wrong():
    dur = 0.55
    buf = silence(dur)
    phase = 0.0
    for i in range(len(buf)):
        t = i / float(SR)
        freq = max(60.0, 240.0 - 260.0 * t)
        phase += 2 * math.pi * freq / SR
        saw = 0.0
        for k in range(1, 7):
            saw += math.sin(k * phase) / k
        env = min(1.0, t / 0.004) * math.exp(-t * 5.0)
        if t > dur - 0.05:
            env *= max(0.0, (dur - t) / 0.05)
        tremolo = 0.75 + 0.25 * math.sin(2 * math.pi * 11 * t)
        buf[i] = 0.55 * env * tremolo * (
            0.7 * saw + 0.5 * math.sin(phase * 1.06))
    normalize(buf, 0.85)
    return buf


def make_whisper():
    dur = 0.85
    buf = silence(dur)
    rnd = random.Random(7)
    prev = 0.0
    for i in range(len(buf)):
        t = i / float(SR)
        x = rnd.uniform(-1.0, 1.0)
        high = x - prev          # crude high-pass: breathy hiss
        prev = x
        env = math.sin(math.pi * t / dur) ** 1.6
        wobble = 0.6 + 0.4 * math.sin(2 * math.pi * 6.5 * t)
        low = math.sin(2 * math.pi * 70 * t) * env * 0.25
        buf[i] = 0.55 * env * wobble * (0.8 * high + low)
    normalize(buf, 0.70)
    fade_tail(buf)
    return buf


def make_door_creak():
    dur = 1.25
    buf = silence(dur)
    phase = 0.0
    for i in range(len(buf)):
        t = i / float(SR)
        freq = (150.0 + 260.0 * (t / dur)
                + 18.0 * math.sin(t * 9.0)
                + 10.0 * math.sin(2 * math.pi * 1.7 * t))
        phase += 2 * math.pi * freq / SR
        rich = 0.0
        for k in range(1, 9):
            rich += math.sin(k * phase) / k
        stutter = 0.15 + 0.85 * max(
            0.0, math.sin(2 * math.pi * 4.5 * t
                          + 0.8 * math.sin(2 * math.pi * 0.8 * t))) ** 1.5
        env = min(1.0, t / 0.05) * min(1.0, (dur - t) / 0.12)
        buf[i] = 0.45 * env * stutter * rich
        buf[i] += 0.10 * env * stutter * math.sin(phase * 0.5)
    normalize(buf, 0.80)
    fade_tail(buf)
    return buf


def make_heartbeat():
    dur = 1.0
    buf = silence(dur)

    def thump(start, amp):
        s = int(start * SR)
        count = int(0.30 * SR)
        for i in range(count):
            idx = s + i
            if idx >= len(buf):
                break
            t = i / float(SR)
            # glide 62 Hz -> 7 Hz
            phase = 2 * math.pi * (62.0 * t - 110.0 * t * t)
            env = min(1.0, t / 0.008) * math.exp(-t * 11.0)
            buf[idx] += amp * env * math.sin(phase)

    thump(0.00, 0.95)   # lub
    thump(0.36, 0.65)   # dub
    normalize(buf, 0.90)
    fade_tail(buf)
    return buf


def make_unlock():
    dur = 0.95
    buf = silence(dur)
    rnd = random.Random(11)

    # 1. metal click
    for i in range(int(0.03 * SR)):
        t = i / float(SR)
        buf[i] += rnd.uniform(-1, 1) * math.exp(-t * 160) * 0.6
    # 2. sliding bolt (filtered noise swell)
    s, e = int(0.05 * SR), int(0.24 * SR)
    prev = 0.0
    for i in range(s, e):
        t = (i - s) / float(SR)
        x = rnd.uniform(-1, 1)
        high = x - prev
        prev = x
        env = math.sin(math.pi * t / 0.19) ** 2
        buf[i] += high * env * 0.35
    # 3. low thud
    for i in range(int(0.02 * SR), int(0.35 * SR)):
        t = i / float(SR) - 0.02
        env = math.exp(-t * 20)
        buf[i] += 0.7 * env * math.sin(2 * math.pi * 120 * t)
    # 4. bright chime
    s = int(0.28 * SR)
    for i in range(s, len(buf)):
        t = (i - s) / float(SR)
        env = math.exp(-t * 4.0)
        if t > 0.5:
            env *= max(0.0, (0.6 - t) / 0.1)
        buf[i] += 0.28 * env * (
            math.sin(2 * math.pi * 1318.5 * t)
            + 0.5 * math.sin(2 * math.pi * 1760.0 * t))
    normalize(buf, 0.85)
    fade_tail(buf)
    return buf


def make_sting():
    dur = 1.15
    buf = silence(dur)
    rnd = random.Random(5)

    # dissonant cluster (A3 against Bb3 - the entity's chord)
    for freq, amp in ((220.0, 0.40), (233.08, 0.36),
                      (440.0, 0.26), (466.16, 0.24), (55.0, 0.45)):
        for i in range(len(buf)):
            t = i / float(SR)
            env = min(1.0, t / 0.012) * math.exp(-t * 3.2)
            if t > dur - 0.15:
                env *= max(0.0, (dur - t) / 0.15)
            buf[i] += amp * env * math.sin(2 * math.pi * freq * t)

    # rising noise sweep
    prev = 0.0
    for i in range(len(buf)):
        t = i / float(SR)
        x = rnd.uniform(-1, 1)
        high = x - prev
        prev = x
        env = (t / dur) ** 0.6 * math.exp(-t * 1.6)
        buf[i] += 0.22 * env * high
    normalize(buf, 0.85)
    fade_tail(buf, 25)
    return buf


# ------------------------------------------------------------------
#  ambient music - a seamless 12 second loop
# ------------------------------------------------------------------
def make_music():
    dur = 12.0
    n = int(dur * SR)
    left = [0.0] * n
    right = [0.0] * n
    rng = random.Random(21)

    drone1 = loop_freq(55.0, dur)      # A1
    drone2 = loop_freq(56.0, dur)      # beating partner
    drone3 = loop_freq(110.0, dur)     # A2
    pads = [loop_freq(f, dur)
            for f in (110.0, 110.5, 130.833, 164.833, 165.333)]

    # ---- continuous bed ------------------------------------
    pad_phases = [0.0] * len(pads)
    pad_rates = [2 * math.pi * (j + 1) / dur for j in range(len(pads))]
    pad_steps = [2 * math.pi * f / SR for f in pads]
    noise_prev = 0.0
    rnd = random.Random(3)
    for i in range(n):
        t = i / float(SR)
        lfo = 0.13 + 0.035 * math.sin(2 * math.pi * t / dur)
        base = lfo * (
            math.sin(2 * math.pi * drone1 * t)
            + 0.7 * math.sin(2 * math.pi * drone2 * t)
            + 0.35 * math.sin(2 * math.pi * drone3 * t + 0.5))

        pad = 0.0
        for j in range(len(pads)):
            pad_phases[j] += pad_steps[j]
            swell = 0.75 + 0.25 * math.sin(pad_rates[j] * t + j)
            pad += 0.045 * swell * (
                math.sin(pad_phases[j]) + 0.3 * math.sin(2 * pad_phases[j]))

        x = rnd.uniform(-1, 1)
        hiss = 0.6 * (x - noise_prev)
        noise_prev = x

        value = base + pad + 0.012 * hiss
        left[i] = value
        right[i] = value

    # ---- music-box notes over the top ----------------------
    scale = [440.0, 523.25, 587.33, 659.25, 783.99]
    starts = sorted(rng.uniform(0.4, 10.2) for _ in range(9))
    for index, start in enumerate(starts):
        freq = loop_freq(rng.choice(scale), dur)
        amp = 0.16
        pan = 0.75 if index % 2 == 0 else 0.25
        length = 1.5
        s = int(start * SR)
        count = int(length * SR)
        for i in range(count):
            idx = s + i
            if idx >= n:
                break
            tl = i / float(SR)
            env = (1.0 - tl / length) ** 2 * min(1.0, tl / 0.004)
            tone = (math.sin(2 * math.pi * freq * tl)
                    + 0.25 * math.sin(4 * math.pi * freq * tl))
            sample = amp * env * tone
            left[idx] += sample * pan
            right[idx] += sample * (1.0 - pan)

    # ---- a distant knock in the middle of the loop --------
    for i in range(int(0.12 * SR)):
        idx = int(6.0 * SR) + i
        if idx >= n:
            break
        t = i / float(SR)
        knock = 0.35 * math.exp(-t * 30) * math.sin(2 * math.pi * 75 * t)
        left[idx] += knock
        right[idx] += knock

    peak = max(max(left), -min(left), max(right), -min(right))
    gain = 0.75 / peak if peak > 0 else 1.0
    for i in range(n):
        left[i] *= gain
        right[i] *= gain
    return left, right


# ------------------------------------------------------------------
def main():
    print("Generating sounds ...")
    write_wav(os.path.join(SOUNDS_DIR, "correct.wav"), make_correct())
    write_wav(os.path.join(SOUNDS_DIR, "wrong.wav"), make_wrong())
    write_wav(os.path.join(SOUNDS_DIR, "whisper.wav"), make_whisper())
    write_wav(os.path.join(SOUNDS_DIR, "door_creak.wav"), make_door_creak())
    write_wav(os.path.join(SOUNDS_DIR, "heartbeat.wav"), make_heartbeat())
    write_wav(os.path.join(SOUNDS_DIR, "unlock.wav"), make_unlock())
    write_wav(os.path.join(SOUNDS_DIR, "sting.wav"), make_sting())
    print("Generating music ...")
    left, right = make_music()
    write_wav(os.path.join(MUSIC_DIR, "haunted_music.wav"), left, right)
    print("Done.")


if __name__ == "__main__":
    main()
