#!/usr/bin/env python3
"""Lag reel av en schittymd-karusell: 7 slides (1080x1350) i 1080x1920 med livlig original musikk.
usage: reelify.py SLIDE_PREFIX OUT.mp4"""
import sys, os, subprocess, math, wave
import numpy as np
SR = 44100
DUR = [2.2, 3.2, 5.5, 4.8, 3.8, 4.4, 4.4]

def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def add(buf, sig, at):
    i = int(at * SR)
    if i >= len(buf): return
    j = min(len(buf), i + len(sig)); buf[i:j] += sig[:j - i]

def lowpass(x, fc):
    a = math.exp(-2 * math.pi * fc / SR); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y

def music(dur, bpm=124):
    """Upbeat original groove: four-on-the-floor, offbeat hats, claps, bouncy bass, pluck melody. C-G-Am-F."""
    n = int(dur * SR); rng = np.random.default_rng(7); beat = 60 / bpm
    drums, bass, lead, chords = (np.zeros(n) for _ in range(4)); duck = np.ones(n)
    kn = int(0.28 * SR); kt = np.arange(kn) / SR
    kick = np.sin(2 * np.pi * (50 * kt + 90 * (1 - np.exp(-kt * 35)) / 35)) * np.exp(-kt * 11)
    cn = int(0.16 * SR); clap = lowpass(rng.standard_normal(cn), 3200) * env(cn, 0.001, 0.04) * 1.8
    hn = int(0.06 * SR); hat = np.diff(rng.standard_normal(hn + 1)) * env(hn, 0.0005, 0.018) * 0.35
    prog = [(261.63, (0, 4, 7)), (196.00, (0, 4, 7)), (220.00, (0, 3, 7)), (174.61, (0, 4, 7))]
    melody = [0, 4, 7, 12, 7, 4, 9, 7]  # semitones over chord root, 8th notes
    b = 0
    while b * beat < dur:
        t = b * beat
        add(drums, kick, t)
        d0, d1 = int(t * SR), min(n, int((t + 0.18) * SR)); duck[d0:d1] = np.minimum(duck[d0:d1], np.linspace(0.35, 1, d1 - d0))
        if b % 2 == 1: add(drums, clap * 0.6, t)
        add(drums, hat, t + beat / 2); add(drums, hat * 0.45, t + beat / 4); add(drums, hat * 0.45, t + 3 * beat / 4)
        root, ivs = prog[(b // 4) % 4]
        # bouncy octave bass on 8ths
        for k in range(2):
            bn = int(beat / 2 * 0.85 * SR); bt = np.arange(bn) / SR
            f = root / 2 * (2 if k else 1)
            sq = np.sign(np.sin(2 * np.pi * f * bt)) * 0.5 + np.sin(2 * np.pi * f * bt) * 0.5
            add(bass, sq * env(bn, 0.003, 0.12) * 0.35, t + k * beat / 2)
        # pluck melody
        for k in range(2):
            step = melody[(b * 2 + k) % len(melody)]
            mn = int(0.25 * SR); mt = np.arange(mn) / SR; f = root * 2 ** (step / 12)
            tone = np.sin(2 * np.pi * f * mt) + 0.4 * np.sin(2 * np.pi * 2 * f * mt) + 0.15 * np.sin(2 * np.pi * 3 * f * mt)
            add(lead, tone * env(mn, 0.002, 0.09) * 0.22, t + k * beat / 2)
        if b % 4 == 0:  # stab chord each bar
            cnn = int(beat * 4 * SR); ct = np.arange(cnn) / SR
            ch = sum(np.sin(2 * np.pi * root * 2 ** (iv / 12) * ct) for iv in ivs) / 3
            add(chords, ch * env(cnn, 0.01, 1.2) * 0.18, t)
        b += 1
    mix = drums * 0.85 + (lowpass(bass, 900) + lead + lowpass(chords, 2500)) * duck
    fi, fo = int(0.02 * SR), int(0.8 * SR)
    mix[:fi] *= np.linspace(0, 1, fi); mix[-fo:] *= np.linspace(1, 0, fo)
    return mix / (np.max(np.abs(mix)) + 1e-9) * 0.89

def main(prefix, out):
    tmp = out + ".d"; os.makedirs(tmp, exist_ok=True)
    parts = []
    for i, d in enumerate(DUR, 1):
        p = f"{tmp}/s{i}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", f"{prefix}_{i}.png",
                        "-vf", f"scale=1080:1350,pad=1080:1920:0:285:black,format=yuv420p,loop=-1:1,trim=duration={d}",
                        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", "30", p], check=True)
        parts.append(p)
    with open(f"{tmp}/list.txt", "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-c", "copy", f"{tmp}/v.mp4"], check=True)
    pcm = (np.clip(music(sum(DUR)), -1, 1) * 32767).astype(np.int16)
    with wave.open(f"{tmp}/a.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", out + ".part.mp4"], check=True)
    os.replace(out + ".part.mp4", out)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
