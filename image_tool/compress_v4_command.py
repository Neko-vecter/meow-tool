import argparse
from pathlib import Path
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing


def convert_one(
    png_path: Path,
    input_dir: Path,
    output_dir: Path,
    skip_exists: bool,
    verbose: bool
):
    rel_path = png_path.parent.relative_to(input_dir)
    target_dir = output_dir / rel_path
    target_dir.mkdir(parents=True, exist_ok=True)

    webp_path = target_dir / (png_path.stem + ".webp")

    if skip_exists and webp_path.exists():
        return (0, 0, True)

    try:
        png_size = png_path.stat().st_size

        with Image.open(png_path) as img:
            img = img.convert("RGBA")
            img.save(
                webp_path,
                format="WEBP",
                lossless=True
            )

        webp_size = webp_path.stat().st_size

        if verbose:
            ratio = webp_size / png_size if png_size else 0
            print(f"[SUCCESS] {png_path} -> {webp_path} ({ratio:.2%})")

        return (png_size, webp_size, False)

    except Exception as e:
        print(f"[ERROR] {png_path} {e}")
        return (0, 0, False)


def main():
    parser = argparse.ArgumentParser(
        description="png to webp"
    )
    parser.add_argument("-i", "--input", type=Path, required=True, help="PNG dir")
    parser.add_argument("-o", "--output", type=Path, required=True, help="WebP dir")
    parser.add_argument(
        "-t", "--threads",
        type=int,
        default=multiprocessing.cpu_count(),
        help="cpu threads"
    )
    parser.add_argument("--skip-exists", action="store_true", help="skip exists webp")
    parser.add_argument("--verbose", action="store_true", help="output log")

    args = parser.parse_args()

    png_files = list(args.input.rglob("*.png"))
    total_png = len(png_files)

    if total_png == 0:
        print("PNG not found")
        return

    total_png_size = 0
    total_webp_size = 0
    skipped = 0

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = [
            executor.submit(
                convert_one,
                png_path,
                args.input,
                args.output,
                args.skip_exists,
                args.verbose
            )
            for png_path in png_files
        ]

        for future in as_completed(futures):
            png_size, webp_size, was_skipped = future.result()
            total_png_size += png_size
            total_webp_size += webp_size
            if was_skipped:
                skipped += 1

    print("\n===== convert data =====")
    print(f"PNG file number: {total_png}")
    print(f"skip file: {skipped}")
    print(f"PNG size:  {total_png_size / 1000 / 1000:.2f} MB")
    print(f"WebP size: {total_webp_size / 1000 / 1000:.2f} MB")
    print("====================")
    print("done")


if __name__ == "__main__":
    main()

# python3 compress_v4_command.py -i img -o output -t 1 --skip-exists --verbose
