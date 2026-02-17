# vid-snatch

Download YouTube audio/video and optionally remove vocals using Demucs.

## Quick Start

Double-click `vid-snatch.command`.

## Usage (Docker CLI)

```bash
# Build once
docker build -t vid-snatch .

# Download audio (MP3)
docker run --rm -v ~/Music/vid-snatch:/app/output vid-snatch "URL"

# Download audio + remove vocals
docker run --rm -v ~/Music/vid-snatch:/app/output vid-snatch "URL" --no-vocals

# Download audio + keep both vocals and instrumental
docker run --rm -v ~/Music/vid-snatch:/app/output vid-snatch "URL" --no-vocals --keep-vocals

# Download video (MP4)
docker run --rm -v ~/Music/vid-snatch:/app/output vid-snatch "URL" --video
```

Files are saved to `~/Music/vid-snatch/`.

## Options

| Flag | Description |
|------|-------------|
| `-o, --output` | Output directory (default: `./output`) |
| `--video` | Download video (MP4) instead of audio |
| `--no-vocals` | Remove vocals with Demucs |
| `--keep-vocals` | Also save isolated vocals track |

> First time running vocal removal will auto-download the Demucs model (~80MB).
