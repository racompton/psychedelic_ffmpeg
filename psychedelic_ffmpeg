#!/usr/bin/env python3
import argparse, random, subprocess, json, shlex

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
        path
    ])
    return float(json.loads(out)["format"]["duration"])

def esc(expr):
    return expr.replace(",", "\\,")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--min", type=int, default=60, help="minimum effect duration seconds")
    p.add_argument("--max", type=int, default=180, help="maximum effect duration seconds")
    p.add_argument("--fade", type=int, default=8, help="fade in/out duration seconds")
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    total = get_duration(args.input)
    t = 0
    parts = []
    filters = []

    i = 0
    while t < total:
        dur = random.randint(args.min, args.max)
        end = min(t + dur, total)
        segdur = end - t
        fade = min(args.fade, segdur / 3)

        effect = random.choice(EFFECTS)

        weight = (
            f"if(lt(T,{fade}),T/{fade},"
            f"if(gt(T,{segdur - fade}),({segdur}-T)/{fade},1))"
        )

        filters.append(
            f"[0:v]trim=start={t}:end={end},setpts=PTS-STARTPTS,format=rgba[base{i}];"
            f"[0:v]trim=start={t}:end={end},setpts=PTS-STARTPTS,{effect},format=rgba[fx{i}];"
            f"[base{i}][fx{i}]blend=all_expr='A*(1-({esc(weight)}))+B*({esc(weight)})',format=yuv420p[v{i}]"
        )

        parts.append(f"[v{i}]")
        t = end
        i += 1

    concat = "".join(parts) + f"concat=n={i}:v=1:a=0[vout]"
    filter_complex = ";".join(filters + [concat])

    cmd = [
        "ffmpeg", "-y",
        "-i", args.input,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "copy",
        "-movflags", "+faststart",
        args.output
    ]

    print("Running:")
    print(" ".join(shlex.quote(x) for x in cmd))
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
