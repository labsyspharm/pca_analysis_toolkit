from pathlib import Path


def check_overwrite(overwrite: bool, path: Path):
    """
    Check file existence and either raise exception or delete it.

    Args:
        overwrite: bool
            Overwrite flag.
        path: pathlib.Path object
            File/folder path to check.
    """
    if overwrite:
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
    elif path.exists():
        raise ValueError(f"{path} exists but overwrite is set to {overwrite}")
