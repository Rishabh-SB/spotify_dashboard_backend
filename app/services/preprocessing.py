import pandas as pd
from datetime import datetime, timedelta
from typing import List
import orjson


def load_json_file(file_bytes: bytes) -> pd.DataFrame:
    """
    Safely load Spotify JSON export. Handles:
      - JSON array
      - Newline-delimited JSON
    """
    text = file_bytes.decode("utf-8")
    try:
        # Try as array
        data = orjson.loads(text)
        if isinstance(data, list):
            return pd.DataFrame(data)
        else:
            raise ValueError("Expected JSON array")
    except Exception:
        # Try line-delimited
        rows = []
        for line in text.splitlines():
            if line.strip():
                rows.append(orjson.loads(line))
        return pd.DataFrame(rows)


def normalize_platform(platform_str):
    key = platform_str.lower() if platform_str else ""
    if "android" in key:
        return "android"
    elif "ios" in key:
        return "ios"
    elif "windows" in key:
        return "windows"
    elif "tizen" in key:
        return "tizen"
    elif "web_player" in key:
        return "web_player"
    elif "linux" in key:
        return "linux"
    elif "os x" in key or "mac os" in key or "macos" or "osx" in key:
        return "osx"
    else:
        print(f"Unrecognized platform: {platform_str}")
        return "other"


def clean_and_enrich(df: pd.DataFrame) -> pd.DataFrame:
    """
    - Keep only relevant columns
    - Convert timestamp to datetime
    - Extract hour, weekday
    - Compute session_id (continuous listening gap < 30min)
    """
    cols = [
        "ts",
        "username",
        "platform",
        "ms_played",
        "conn_country",
        "ip_addr_decrypted",
        "user_agent_decrypted",
        "master_metadata_track_name",
        "master_metadata_album_artist_name",
        "master_metadata_album_album_name",
    ]
    df = df[cols].copy()

    # Convert timestamp to datetime
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    df = df.dropna(subset=["ts"])

    # Extract hour, weekday
    df["hour"] = df["ts"].dt.hour
    df["weekday"] = df["ts"].dt.day_name()

    # Sort by timestamp
    df = df.sort_values("ts").reset_index(drop=True)

    # Compute sessions: if gap > 30 minutes, new session
    session_gap = timedelta(minutes=30)
    df["prev_ts"] = df["ts"].shift(1)
    df["gap"] = df["ts"] - df["prev_ts"]
    df["new_session"] = (df["gap"] > session_gap) | (df["gap"].isna())
    df["session_id"] = df["new_session"].cumsum()

    # Drop helper columns
    df = df.drop(columns=["prev_ts", "gap", "new_session"])

    # Remove entries with null or empty track names
    df = df[df["master_metadata_track_name"].notna() & (df["master_metadata_track_name"] != "")]
        
    # Normalize platform labels
    df["platform"] = df["platform"].apply(normalize_platform)

    return df


def merge_and_preprocess(file_bytes_list: List[bytes]) -> pd.DataFrame:
    """
    Load multiple files and merge into single DataFrame
    """
    dfs = [load_json_file(fb) for fb in file_bytes_list]
    combined = pd.concat(dfs, ignore_index=True)
    combined = clean_and_enrich(combined)
    return combined
