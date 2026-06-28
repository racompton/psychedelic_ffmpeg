#!/usr/bin/env python3
import argparse, random, subprocess, json, shlex, math
from pathlib import Path

EFFECTS = [
    "hue=h=360*t/12:s=2.2,eq=contrast=1.25:saturation=2.4",
    "edgedetect=mode=colormix:high=0.25,eq=saturation=2.5",
    "gblur=sigma=3,hue=h=360*t/8:s=2.8,eq=contrast=1.35",
    "negate,hue=h=360*t/10:s=2.5",
    "sobel,eq=saturation=2.8:contrast=1.4",
    "vignette=PI/5,eq=saturation=2.5:contrast=1.3,hue=h=360*t/9",
    "lagfun=decay=0.92,hue=h=360*t/7:s=2.4",
    "tblend=all_mode=average,eq=saturation=2.7:contrast=1.3,hue=h=360*t/11",
]

def run(cmd):
    return subprocess.check_output(cmd, text=True).strip()

def get_duration(path):
    out = run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(path)
    ])
    return float(json.loads(out)["format"]["duration"])

def timestamp_name(seconds):
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}h{m:02d}m{s:02d}s"

def process_clip(input_file, output_file, start, duration, fade):
    effect = random.choice(EFFECTS)
    fade = min(fade, duration / 3)

    weight = (
        f"if(lt(t,{fade}),t/{fade},"
        f"if(gt(t,{duration - fade}),({duration}-t)/{fade},1))"
    )

    filter_complex = (
        f"[0:v]split=2[base][fx];"
        f"[fx]{effect},format=rgba[fxout];"
        f"[base]format=rgba[baseout];"
        f"[baseout][fxout]"
        f"blend=all_expr='A*(1-({weight}))+B*({weight})',"
        f"format=yuv420p[vout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-t", str(duration),
        "-i", str(input_file),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_file)
    ]

    print("Running:")
    print(" ".join(shlex.quote(x) for x in cmd))
    subprocess.run(cmd, check=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("input_file")
    p.add_argument("output_dir")
    p.add_argument("--clip-length", type=int, default=60)
    p.add_argument("--fade", type=int, default=8)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--include-partial", action="store_true")
    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    input_file = Path(args.input_file)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    duration = get_duration(input_file)
    base_name = input_file.stem

    full_chunks = int(duration // args.clip_length)
    starts = [i * args.clip_length for i in range(full_chunks)]

    if args.include_partial:
        remainder = duration % args.clip_length
        if remainder > 5:
            starts.append(full_chunks * args.clip_length)

    random.shuffle(starts)

    for start in starts:
        actual_duration = min(args.clip_length, duration - start)
        ts = timestamp_name(start)
        output_file = output_dir / f"{base_name}_{ts}_psychedelic.mp4"

        print(f"\nProcessing clip starting at {ts}")
        process_clip(
            input_file=input_file,
            output_file=output_file,
            start=start,
            duration=actual_duration,
            fade=args.fade,
        )

    print("\nDone.")

if __name__ == "__main__":
    main()
