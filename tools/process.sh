#!/bin/bash
# process.sh IN.wav STEM [SEMITONES] [TEMPO] : turn a raw TTS take into the clip formats the mod needs.
#   trims silence at both ends, optional pitch shift (asetrate+atempo, keeps duration) and speed change, loudnorm two-pass to -16 LUFS,
#   5 ms fades, limiter. Writes STEM.wav (48 kHz), STEM_44k.wav (44.1 kHz, what make-voices wants), STEM.mp3 and STEM.opus into $OUT (default: ./clips).
# Needs ffmpeg, ffprobe and python3. Convert a raw .pcm take first:  ffmpeg -f s16le -ar 24000 -ac 1 -i take.pcm take.wav
set -euo pipefail
in=$1; stem=$2; st=${3:-0}; tempo=${4:-1}
out=${OUT:-./clips}; mkdir -p "$out"; tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
sr=$(ffprobe -v error -show_entries stream=sample_rate -of csv=p=0 "$in")
f=$(python3 -c "print(2**($st/12))")
pre="silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,areverse"
shift="asetrate=$(python3 -c "print(int($sr*$f))"),aresample=48000,atempo=$(python3 -c "print(1/$f*$tempo)")"
base="$pre,$shift,aresample=48000"
m=$(ffmpeg -v info -i "$in" -af "$base,loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p')
g(){ echo "$m" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
ln="loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true"
ffmpeg -v error -y -i "$in" -af "$base,$ln,aresample=48000" -ac 1 -c:a pcm_s16le "$tmp/n.wav"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$tmp/n.wav")
fo=$(python3 -c "print(max(0,$dur-0.005))")
ffmpeg -v error -y -i "$tmp/n.wav" -af "afade=t=in:d=0.005,afade=t=out:st=$fo:d=0.005,alimiter=limit=0.84:level=disabled" -ar 48000 -ac 1 -c:a pcm_s16le "$out/$stem.wav"
ffmpeg -v error -y -i "$out/$stem.wav" -ar 44100 -ac 1 -c:a pcm_s16le "$out/${stem}_44k.wav"
ffmpeg -v error -y -i "$out/$stem.wav" -c:a libmp3lame -b:a 192k "$out/$stem.mp3"
ffmpeg -v error -y -i "$out/$stem.wav" -c:a libopus -b:a 64k -ar 48000 -ac 1 "$out/$stem.opus"
echo "wrote $out/$stem.{wav,mp3,opus} and ${stem}_44k.wav"
