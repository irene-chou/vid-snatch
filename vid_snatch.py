"""vid-snatch: Download YouTube audio/video and optionally remove vocals."""

import argparse
import re
import shutil
import sys
import uuid
from pathlib import Path

DEFAULT_OUTPUT_DIR = Path("./output")
DEMUCS_MODEL = "htdemucs"

YOUTUBE_PATTERNS = [
    r"(https?://)?(www\.)?youtube\.com/watch\?",
    r"(https?://)?(www\.)?youtube\.com/shorts/",
    r"(https?://)?youtu\.be/",
    r"(https?://)?music\.youtube\.com/watch\?",
]


def check_dependencies() -> bool:
    if not shutil.which("ffmpeg"):
        print("Error: ffmpeg not found.")
        print("Install via: brew install ffmpeg")
        return False
    return True


def validate_url(url: str) -> str:
    for pattern in YOUTUBE_PATTERNS:
        if re.match(pattern, url):
            return url
    raise argparse.ArgumentTypeError(f"Not a valid YouTube URL: {url}")


def download_audio(url: str, output_dir: Path, audio_format: str = "mp3") -> Path:
    import yt_dlp

    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "paths": {"home": str(output_dir)},
        "outtmpl": {"default": "%(title)s.%(ext)s"},
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": "192",
            }
        ],
        "quiet": False,
        "no_warnings": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            audio_path = Path(filename).with_suffix(f".{audio_format}")
            return audio_path
    except yt_dlp.utils.DownloadError as e:
        print(f"\nDownload failed: {e}")
        sys.exit(1)


def download_video(url: str, output_dir: Path) -> Path:
    import yt_dlp

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "noplaylist": True,
        "paths": {"home": str(output_dir)},
        "outtmpl": {"default": "%(title)s.%(ext)s"},
        "merge_output_format": "mp4",
        "quiet": False,
        "no_warnings": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            video_path = Path(filename).with_suffix(".mp4")
            return video_path
    except yt_dlp.utils.DownloadError as e:
        print(f"\nDownload failed: {e}")
        sys.exit(1)


def remove_vocals(
    audio_path: Path,
    output_dir: Path,
    keep_vocals: bool,
) -> Path:
    import demucs.separate

    print(f"Separating vocals using Demucs ({DEMUCS_MODEL})...")
    print("(First run will download the model, ~80MB)")

    # Demucs can't handle special characters in filenames (full-width chars, etc.)
    # Rename to a safe temp name, process, then rename back
    original_stem = audio_path.stem
    safe_name = uuid.uuid4().hex[:8]
    safe_path = audio_path.parent / f"{safe_name}{audio_path.suffix}"
    audio_path.rename(safe_path)

    demucs_dir = output_dir / "_demucs_temp"
    args = [
        "--two-stems", "vocals",
        "-n", DEMUCS_MODEL,
        "-o", str(demucs_dir),
        "--mp3", "--mp3-bitrate", "192",
        str(safe_path),
    ]

    try:
        demucs.separate.main(args)
    except Exception as e:
        safe_path.rename(audio_path)
        print(f"\nVocal removal failed: {e}")
        print(f"The downloaded audio is still available at: {audio_path}")
        sys.exit(1)

    # Demucs outputs to: _demucs_temp/htdemucs/<safe_name>/no_vocals.mp3
    demucs_out = demucs_dir / DEMUCS_MODEL / safe_name
    no_vocals_src = demucs_out / "no_vocals.mp3"
    vocals_src = demucs_out / "vocals.mp3"

    no_vocals_dst = output_dir / f"{original_stem}_no_vocals.mp3"
    shutil.move(str(no_vocals_src), str(no_vocals_dst))

    if keep_vocals and vocals_src.exists():
        vocals_dst = output_dir / f"{original_stem}_vocals.mp3"
        shutil.move(str(vocals_src), str(vocals_dst))
        print(f"Vocals saved: {vocals_dst}")

    # Clean up
    shutil.rmtree(demucs_dir, ignore_errors=True)
    safe_path.unlink(missing_ok=True)

    return no_vocals_dst


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vid-snatch",
        description="Download YouTube audio/video, optionally remove vocals.",
    )
    parser.add_argument("url", type=validate_url, help="YouTube video URL")
    parser.add_argument(
        "-o", "--output", type=Path, default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--video", action="store_true",
        help="Download video (MP4) instead of audio",
    )
    mode.add_argument(
        "--no-vocals", action="store_true",
        help="Download audio and remove vocals using Demucs",
    )

    parser.add_argument(
        "--keep-vocals", action="store_true",
        help="When using --no-vocals, also save the isolated vocals track",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not check_dependencies():
        sys.exit(1)

    args.output.mkdir(parents=True, exist_ok=True)

    if args.video:
        print(f"Downloading video from: {args.url}")
        video_path = download_video(args.url, args.output)
        print(f"Done! Video saved: {video_path}")
    elif args.no_vocals:
        print(f"Downloading audio from: {args.url}")
        audio_path = download_audio(args.url, args.output, audio_format="wav")
        print(f"Downloaded: {audio_path}")
        result_path = remove_vocals(
            audio_path, args.output, keep_vocals=args.keep_vocals,
        )
        print(f"Instrumental saved: {result_path}")
    else:
        print(f"Downloading audio from: {args.url}")
        audio_path = download_audio(args.url, args.output)
        print(f"Done! Audio saved: {audio_path}")


if __name__ == "__main__":
    main()
