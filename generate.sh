#!/usr/bin/env bash
set -e

# Default parameters
USER="${1:-princegupta}"
FULL_NAME="${2:-Prince Gupta}"
PHOTO="${3:-source-photo.png}"

echo "==> Generating profile assets for ${USER} (${FULL_NAME})..."

# 1. Fetch contributions
echo "==> [1/4] Scraping contribution data..."
python3 scripts/fetch_contributions.py "$USER"

# 2. Render heatmap SVG
echo "==> [2/4] Rendering contrib-heatmap.svg..."
python3 scripts/generate_streak_svg.py "$USER" contrib-heatmap.svg

# 3. Render stats card SVG
echo "==> [3/4] Rendering stats.svg..."
python3 scripts/render_stats_svg.py data/contributions.json stats.svg

# 4. Prepare portrait and render ASCII SVG
if [ -f "$PHOTO" ]; then
    echo "==> [4/4] Preparing photo and generating profile-ascii.svg..."
    python3 scripts/prep_photo.py "$PHOTO" source-prepped.png
    python3 scripts/make_ascii_svg.py source-prepped.png profile-ascii.svg "$USER" "$FULL_NAME"
else
    echo "==> [4/4] Skipping photo (file $PHOTO not found)."
fi

echo "==> All assets generated successfully!"
