import subprocess
from pathlib import Path


def get_git_activity(
    project_paths: list[str],
    date: str,
    hour: int | None = None,
) -> dict[str, list[dict]]:
    """
    Run git log for each project path and return commits on the given date/hour.

    Returns {project_path: [{"hash", "time", "subject", "author"}]}
    Only paths that exist, are git repos, and have commits are included.
    """
    if hour is not None:
        after  = f"{date} {hour:02d}:00:00"
        before = f"{date} {hour:02d}:59:59"
    else:
        after  = f"{date} 00:00:00"
        before = f"{date} 23:59:59"

    result: dict[str, list[dict]] = {}
    for path_str in project_paths:
        p = Path(path_str)
        if not p.is_dir() or not (p / ".git").is_dir():
            continue
        try:
            proc = subprocess.run(
                [
                    "git", "-C", str(p),
                    "log",
                    "--format=%h|||%ad|||%s|||%an",
                    "--date=format:%H:%M",
                    f"--after={after}",
                    f"--before={before}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            commits = []
            for line in proc.stdout.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split("|||", 3)
                if len(parts) == 4:
                    commits.append({
                        "hash":    parts[0],
                        "time":    parts[1],
                        "subject": parts[2],
                        "author":  parts[3],
                    })
            if commits:
                result[path_str] = commits
        except (subprocess.TimeoutExpired, OSError):
            continue

    return result
