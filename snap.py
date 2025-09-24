import os
import datetime

"""Project snapshot utility.

Generates a timestamped markdown file under `snapshots/` that contains a
recursive listing of files in the project with inline code blocks for
text-based files. Binary/media files are listed but contents are skipped.

Excludes common noise like virtual environments, node modules, git metadata,
bytecode caches, and the snapshots directory itself.
"""

# Configuration
PROJECT_DIR = "."  # Scan the repository root
SNAPSHOT_DIR = "snapshots"
IGNORE_DIRS = {
    '__pycache__', '.git', '.idea', '.vscode', 'node_modules',
    'env', 'venv', '.venv', SNAPSHOT_DIR
}
IGNORE_FILES = {'.DS_Store'}
SKIP_CONTENT_EXTS = {
    '.jpg', '.jpeg', '.png', '.gif', '.svg', '.bmp', '.ico',
    '.webp', '.pdf', '.woff', '.woff2', '.ttf', '.otf',
    '.zip', '.gz', '.tar', '.7z', '.rar', '.exe', '.dll'
}

def generate_snapshot():
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    out_filename = f"project-snapshot-{timestamp}.md"
    out_dir = os.path.join(os.getcwd(), SNAPSHOT_DIR)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, out_filename)

    lines = [
        f"# Project Snapshot",
        f"**Root:** {os.path.abspath(PROJECT_DIR)}",
        f"**Generated:** {now.strftime('%Y-%m-%d %I:%M:%S %p')}",
        "\n---\n"
    ]

    root_path = os.path.abspath(PROJECT_DIR)

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Filter out ignored directories in-place so os.walk does not descend
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        rel_dir = os.path.relpath(dirpath, root_path).replace("\\", "/")

        for fname in filenames:
            if fname in IGNORE_FILES:
                continue
            full_path = os.path.join(dirpath, fname)
            ext = os.path.splitext(fname)[1].lower()
            rel_path = os.path.relpath(full_path, root_path).replace("\\", "/")

            lines.append(f"### {rel_path}\n")

            if ext in SKIP_CONTENT_EXTS:
                lines.append("*Binary or media file — skipped.*\n\n")
                continue

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read().replace("```", "``\\`")
                language = ext[1:] if ext else ""
                code = f"```{language}\n{content}\n```\n"
                lines.append(code)
            except Exception as e:
                lines.append(f"*Could not read file: {e}*\n\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"📸 Snapshot saved to: {out_path}")

if __name__ == "__main__":
    generate_snapshot()
