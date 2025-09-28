from fastapi import APIRouter, HTTPException
from typing import Optional
import pandas as pd
import numpy as np
from fastapi.encoders import jsonable_encoder
from app.routes.upload import DATASETS

router = APIRouter()

def convert_numpy_types(obj):
    if isinstance(obj, dict):
        return {convert_numpy_types(k): convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.uint32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    else:
        return obj

def convert_keys_to_str(d):
    if isinstance(d, dict):
        return {str(k): v for k, v in d.items()}
    return d

@router.get("/{dataset_id}")
async def get_dashboard_metrics(dataset_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    if dataset_id not in DATASETS:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = DATASETS[dataset_id].copy()

    start_dt = pd.to_datetime(start_date, utc=True) if start_date else df.index.min()
    end_dt = pd.to_datetime(end_date, utc=True) + pd.Timedelta(days=1) if end_date else df.index.max()
    df = df.loc[start_dt:end_dt]

    if df.empty:
        return {"error": "No data in this timeframe"}

    top_songs = df.groupby("master_metadata_track_name")["ms_played"].sum().sort_values(ascending=False).head(10)
    top_artists = df.groupby("master_metadata_album_artist_name")["ms_played"].sum().sort_values(ascending=False).head(10)
    top_albums = df.groupby("master_metadata_album_album_name")["ms_played"].sum().sort_values(ascending=False).head(10)

    df["date"] = df.index.date

    weekly_group = df.groupby([df.index.isocalendar().year, df.index.isocalendar().week])["ms_played"].sum() / 3600000
    weekly_hours = {f"{year}-W{week}": val for (year, week), val in weekly_group.to_dict().items()}

    monthly_hours = convert_keys_to_str((df.groupby(df.index.to_period("M"))["ms_played"].sum() / 3600000).to_dict())

    dfa = df.tz_convert("Asia/Kolkata")
    hour_minutes = (dfa.groupby(dfa.index.hour)["ms_played"].sum() / 60000).to_dict()
    weekday_minutes = (dfa.groupby(dfa.index.day_name())["ms_played"].sum() / 60000).to_dict()

    short_play_ms = 30 * 1000
    skip_rate = float((df["ms_played"] < short_play_ms).mean())

    track_counts = df["master_metadata_track_name"].value_counts()
    repeat_tracks = track_counts[track_counts > 1].index
    loyalty_playtime = df[df["master_metadata_track_name"].isin(repeat_tracks)]["ms_played"].sum()
    loyalty = float(loyalty_playtime / df["ms_played"].sum())

    new_tracks = int(df["master_metadata_track_name"].nunique())
    new_artists = int(df["master_metadata_album_artist_name"].nunique())

    streaks = []
    for date, g in df.groupby("date"):
        g_sorted = g.sort_values("ms_played")
        current_track = None
        streak_len = 0
        for track in g_sorted["master_metadata_track_name"]:
            if track == current_track:
                streak_len += 1
            else:
                if streak_len > 0:
                    streaks.append({"date": str(date), "track": current_track, "streak": streak_len})
                current_track = track
                streak_len = 1
        if streak_len > 0:
            streaks.append({"date": str(date), "track": current_track, "streak": streak_len})
    top_streaks = sorted(streaks, key=lambda x: x["streak"], reverse=True)[:5]

    histogram_bins = [
        0,
        10*1000,
        20*1000,
        30*1000,
        40*1000,
        50*1000,
        60*1000,
        75*1000,
        90*1000,
        105*1000,
        120*1000,
        150*1000,
        180*1000,
        240*1000,
        300*1000,
        600*1000,
        1800000
    ]
    histogram_counts = convert_keys_to_str(pd.cut(df["ms_played"], bins=histogram_bins).value_counts().sort_index().to_dict())

    platform_percent = (df.groupby("platform")["ms_played"].sum() / df["ms_played"].sum()).to_dict()

    platform_over_time_df = (df.groupby([df.index.to_period("M"), "platform"])["ms_played"].sum() / 3600000).unstack(fill_value=0)
    platform_over_time_df.index = platform_over_time_df.index.map(str)
    platform_over_time = platform_over_time_df.to_dict(orient="index")

    # Loyalty pie charts
    top_10_track_playtime = df.groupby("master_metadata_track_name")["ms_played"].sum().nlargest(10)
    rest_playtime_tracks = df["ms_played"].sum() - top_10_track_playtime.sum()
    loyalty_pie_tracks = pd.concat([top_10_track_playtime, pd.Series({"Rest": rest_playtime_tracks})])
    loyalty_pie_tracks = loyalty_pie_tracks / loyalty_pie_tracks.sum()

    top_10_artist_playtime = df.groupby("master_metadata_album_artist_name")["ms_played"].sum().nlargest(10)
    rest_playtime_artists = df["ms_played"].sum() - top_10_artist_playtime.sum()
    loyalty_pie_artists = pd.concat([top_10_artist_playtime, pd.Series({"Rest": rest_playtime_artists})])
    loyalty_pie_artists = loyalty_pie_artists / loyalty_pie_artists.sum()

    # Exploration charts (new artists/tracks per month)
    df["month"] = df.index.to_period("M")

    first_artist_month = df.groupby("master_metadata_album_artist_name")["month"].min()
    new_artists_per_month = first_artist_month.value_counts().sort_index()
    new_artists_per_month = {str(k): v for k, v in new_artists_per_month.items()}

    first_track_month = df.groupby("master_metadata_track_name")["month"].min()
    new_tracks_per_month = first_track_month.value_counts().sort_index()
    new_tracks_per_month = {str(k): v for k, v in new_tracks_per_month.items()}

    # Section 5: Session metrics
    session_durations = df.groupby("session_id")["ms_played"].sum() / 1000  # seconds
    total_sessions = session_durations.shape[0]
    avg_session_duration = (session_durations / 60).mean() if total_sessions > 0 else 0

    session_bins = [0, 5, 10, 15, 30, 60, 120, 240, 480, 1440]  # minutes
    session_length_histogram = pd.cut(session_durations / 60, bins=session_bins).value_counts().sort_index()
    session_length_histogram = convert_keys_to_str(session_length_histogram.to_dict())

    tracks_per_session = df.groupby("session_id")["master_metadata_track_name"].nunique()
    avg_tracks_per_session = tracks_per_session.mean() if not tracks_per_session.empty else 0

    dashboard_metrics = {
        "section1": {
            "top_songs": top_songs.to_dict(),
            "top_artists": top_artists.to_dict(),
            "top_albums": top_albums.to_dict(),
        },
        "section2": {
            "weekly_hours": weekly_hours,
            "monthly_hours": monthly_hours,
            "hour_minutes": hour_minutes,
            "weekday_minutes": weekday_minutes,
        },
        "section3": {
            "skip_rate": skip_rate,
            "loyalty": loyalty,
            "new_tracks": new_tracks,
            "new_artists": new_artists,
            "top_streaks": top_streaks,
            "ms_played_histogram": histogram_counts,
            "loyalty_pie_tracks": loyalty_pie_tracks.to_dict(),
            "loyalty_pie_artists": loyalty_pie_artists.to_dict(),
            "new_artists_per_month": new_artists_per_month,
            "new_tracks_per_month": new_tracks_per_month,
        },
        "section4": {
            "platform_percent": platform_percent,
            "platform_over_time": platform_over_time,
        },
        "section5": {
            "total_sessions": total_sessions,
            "average_session_duration_minutes": avg_session_duration,
            "session_length_histogram": session_length_histogram,
            "average_tracks_per_session": avg_tracks_per_session,
        },
    }

    converted_metrics = convert_numpy_types(dashboard_metrics)
    return jsonable_encoder(converted_metrics)
