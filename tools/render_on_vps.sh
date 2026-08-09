#!/usr/bin/env bash
# Render the demo on the VPS instead of locally.
#
#   bash tools/render_on_vps.sh [KEY=VALUE ...]
#   bash tools/render_on_vps.sh BULKHEAD_FRAMES=60 BULKHEAD_W=1280 BULKHEAD_H=720
#
# Why: this workstation has 7.8 GB of RAM, and headless EEVEE has no GL context, so
# it falls back to software rasterisation - slow, and heavy enough that a long render
# can exhaust the machine. The VPS has 12 cores and renders with Cycles, which needs
# no GL at all and is both faster and better looking.
#
# The VPS also runs production (the CRM among other things) and has NO SWAP, so an
# out-of-memory event there kills real services rather than just the render. Hence
# the free-memory precondition, the capped thread count, and nice.
#
# Remote commands go over stdin as heredocs rather than as quoted ssh arguments:
# nesting single quotes (the grep pattern) inside a double-quoted ssh string breaks
# in ways that are invisible until a later line silently fails to run.
set -euo pipefail

HOST="${VPS_HOST:-contabo}"
LOCAL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="$(basename "$LOCAL_ROOT")"
REMOTE="/root/render/$PROJECT"
BLENDER="/root/blender-portable/blender-4.5.9-linux-x64/blender"

# Leave headroom. The box has 12 cores but idles around load 8-10 serving
# production, so 8 render threads pushed it to load 16. Six keeps the render
# comfortably in the slack; nice(15) means production preempts it either way.
THREADS="${RENDER_THREADS:-6}"
MIN_FREE_MB="${MIN_FREE_MB:-6000}"
EXTRA_ENV="$*"

cd "$LOCAL_ROOT"

echo "==> checking headroom on $HOST"
ssh "$HOST" bash -s <<EOF
set -e
test -x $BLENDER || { echo '    blender missing on VPS'; exit 1; }
AVAIL=\$(free -m | awk '/^Mem:/ {print \$7}')
echo "    available: \${AVAIL} MB (need $MIN_FREE_MB)"
if [ "\$AVAIL" -lt $MIN_FREE_MB ]; then
  echo '    refusing: too little free memory, and this box has no swap'
  exit 1
fi
EOF

echo "==> pushing source"
tar -czf - addon tools | ssh "$HOST" "mkdir -p $REMOTE && tar -xzf - -C $REMOTE"

echo "==> rendering (Cycles, $THREADS threads, niced)"
ssh "$HOST" bash -s <<EOF
set -e
cd $REMOTE
rm -rf build/demo/frames
export RENDER_ENGINE=CYCLES RENDER_THREADS=$THREADS $EXTRA_ENV
nice -n 15 $BLENDER --background --factory-startup --python tools/render_demo.py 2>&1 |
  grep -Ev '^(Fra:|Read blend|Blender quit|Saved:)' | tail -25
EOF

echo "==> pulling frames back"
mkdir -p build/demo
rm -rf build/demo/frames
ssh "$HOST" "cd $REMOTE/build/demo && tar -czf - frames" | tar -xzf - -C build/demo

echo "==> done: $(find build/demo/frames -name 'f*.png' | wc -l) frames"
