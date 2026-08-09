#!/usr/bin/env bash
# Turn the rendered frames into every asset the launch needs.
#
#   bash tools/make_video.sh
#
# Produces, in build/demo/:
#   bulkhead.mp4           landscape, for Gumroad / X / the README
#   bulkhead.gif           looping, for Reddit and forums
#   bulkhead-vertical.mp4  9:16, for Shorts and TikTok
#   cover.png             storefront cover still
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRAMES="$ROOT/build/demo/frames"
OUT="$ROOT/build/demo"
FPS=24

count=$(find "$FRAMES" -name 'f*.png' | wc -l)
if [ "$count" -lt 2 ]; then
  echo "only $count frames in $FRAMES — run tools/render_demo.py first" >&2
  exit 1
fi
echo "assembling $count frames"

# Ping-pong so the loop returns to its start instead of jump-cutting. The demo ends
# with the sphere lifted and the cable draped, which is the most interesting frame to
# rest on, so playing it back down and round reads as continuous.
ffmpeg -y -loglevel error -framerate $FPS -i "$FRAMES/f%04d.png" \
  -filter_complex "[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1[v]" \
  -map "[v]" -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart \
  "$OUT/bulkhead.mp4"

# Vertical: centre-crop to 9:16 and pad to 1080x1920.
ffmpeg -y -loglevel error -i "$OUT/bulkhead.mp4" \
  -vf "crop=ih*9/16:ih,scale=1080:1920:flags=lanczos" \
  -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart \
  "$OUT/bulkhead-vertical.mp4"

# GIF via a generated palette: without one, a dark scene bands badly.
#
# Dense greebling is high-entropy and compresses poorly as GIF: at 720px/18fps
# this came out at 16 MB, past what Reddit and X will happily inline. Fewer
# frames, a smaller frame and a reduced palette carry the motion just as well at
# a fraction of the size. The mp4 stays the high-quality asset.
ffmpeg -y -loglevel error -i "$OUT/bulkhead.mp4" \
  -vf "fps=12,scale=560:-1:flags=lanczos,palettegen=max_colors=128:stats_mode=diff" \
  "$OUT/palette.png"
ffmpeg -y -loglevel error -i "$OUT/bulkhead.mp4" -i "$OUT/palette.png" \
  -lavfi "fps=12,scale=560:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4" \
  -loop 0 "$OUT/bulkhead.gif"
rm -f "$OUT/palette.png"

# Cover still: a quarter into the orbit, where the key light rakes hardest across
# the plating and the depth reads best.
cover=$(find "$FRAMES" -name 'f*.png' | sort | awk 'NR==15')
cp "$cover" "$OUT/cover.png"

echo
ls -lh "$OUT"/bulkhead.mp4 "$OUT"/bulkhead.gif "$OUT"/bulkhead-vertical.mp4 \
       "$OUT"/cover.png | awk '{print "  "$9"  "$5}'
