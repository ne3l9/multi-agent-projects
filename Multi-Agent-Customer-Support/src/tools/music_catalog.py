"""Music catalog tools for the multi-agent system."""

import logging
from langchain_core.tools import tool
from src.db.database import run_query_safe

logger = logging.getLogger(__name__)


def _safe_int(value: str, label: str = "value") -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid {label}: '{value}'. Please provide a numeric value.")


@tool
def get_albums_by_artist(artist: str) -> str:
    """Get albums by an artist from the music catalog. Uses fuzzy matching on artist name."""
    logger.info(f"TOOL_CALL: get_albums_by_artist | artist={artist}")
    try:
        result = run_query_safe(
            """
            SELECT Album.AlbumId, Album.Title AS AlbumTitle, Artist.Name AS ArtistName
            FROM Album
            JOIN Artist ON Album.ArtistId = Artist.ArtistId
            WHERE Artist.Name LIKE :pattern
            ORDER BY Album.Title;
            """,
            {"pattern": f"%{artist}%"},
        )
        logger.info(f"TOOL_RESULT: get_albums_by_artist | result_length={len(result)}")
        if result == "[]":
            return f"No albums found for artist: {artist}"
        return result
    except Exception as e:
        logger.error(f"Error in get_albums_by_artist: {e}")
        return f"Error looking up albums for '{artist}'. Please try again."


@tool
def get_tracks_by_artist(artist: str) -> str:
    """
    Get songs/tracks by an artist from the catalog.
    Returns total count and a sample of up to 20 tracks with full details.
    """
    logger.info(f"TOOL_CALL: get_tracks_by_artist | artist={artist}")
    try:
        count_result = run_query_safe(
            """
            SELECT COUNT(*) AS total_tracks
            FROM Track
            JOIN Album ON Track.AlbumId = Album.AlbumId
            JOIN Artist ON Album.ArtistId = Artist.ArtistId
            WHERE Artist.Name LIKE :pattern;
            """,
            {"pattern": f"%{artist}%"},
        )

        result = run_query_safe(
            """
            SELECT Track.TrackId,
                   Track.Name AS SongName,
                   Artist.Name AS ArtistName,
                   Album.Title AS AlbumTitle,
                   Genre.Name AS GenreName,
                   Track.Composer,
                   Track.Milliseconds,
                   ROUND(Track.Milliseconds / 60000.0, 1) AS DurationMinutes,
                   Track.Bytes,
                   Track.UnitPrice,
                   MediaType.Name AS MediaType
            FROM Track
            JOIN Album ON Track.AlbumId = Album.AlbumId
            JOIN Artist ON Album.ArtistId = Artist.ArtistId
            LEFT JOIN Genre ON Track.GenreId = Genre.GenreId
            LEFT JOIN MediaType ON Track.MediaTypeId = MediaType.MediaTypeId
            WHERE Artist.Name LIKE :pattern
            ORDER BY Album.Title, Track.Name
            LIMIT 20;
            """,
            {"pattern": f"%{artist}%"},
        )
        logger.info(f"TOOL_RESULT: get_tracks_by_artist | count={count_result} | sample_length={len(result)}")

        if result == "[]":
            return f"No tracks found for artist: {artist}"

        return f"Total tracks found: {count_result}. Sample (up to 20): {result}"
    except Exception as e:
        logger.error(f"Error in get_tracks_by_artist: {e}")
        return f"Error looking up tracks for '{artist}'. Please try again."


@tool
def get_songs_by_genre(genre: str) -> str:
    """
    Fetch a representative sample of songs from a specific genre.
    Returns total count and one song per artist (up to 10), deterministically
    picking each artist's first track by TrackId.
    """
    logger.info(f"TOOL_CALL: get_songs_by_genre | genre={genre}")
    try:
        count_result = run_query_safe(
            """
            SELECT COUNT(*) AS total_tracks
            FROM Track
            JOIN Genre ON Track.GenreId = Genre.GenreId
            WHERE Genre.Name LIKE :pattern;
            """,
            {"pattern": f"%{genre}%"},
        )

        result = run_query_safe(
            """
            WITH ranked AS (
                SELECT Track.TrackId,
                       Track.Name AS SongName,
                       Artist.Name AS ArtistName,
                       Album.Title AS AlbumTitle,
                       Genre.Name AS GenreName,
                       Track.Composer,
                       Track.Milliseconds,
                       ROUND(Track.Milliseconds / 60000.0, 1) AS DurationMinutes,
                       Track.Bytes,
                       Track.UnitPrice,
                       MediaType.Name AS MediaType,
                       ROW_NUMBER() OVER (PARTITION BY Artist.ArtistId ORDER BY Track.TrackId) AS rn
                FROM Track
                JOIN Genre ON Track.GenreId = Genre.GenreId
                JOIN Album ON Track.AlbumId = Album.AlbumId
                JOIN Artist ON Album.ArtistId = Artist.ArtistId
                LEFT JOIN MediaType ON Track.MediaTypeId = MediaType.MediaTypeId
                WHERE Genre.Name LIKE :pattern
            )
            SELECT TrackId, SongName, ArtistName, AlbumTitle, GenreName,
                   Composer, Milliseconds, DurationMinutes, Bytes, UnitPrice, MediaType
            FROM ranked
            WHERE rn = 1
            ORDER BY ArtistName
            LIMIT 10;
            """,
            {"pattern": f"%{genre}%"},
        )
        logger.info(f"TOOL_RESULT: get_songs_by_genre | count={count_result} | sample_length={len(result)}")

        if result == "[]":
            return f"No songs found for the genre: {genre}"

        return (
            f"Total {genre} tracks in catalog: {count_result}. "
            f"Representative sample (one per artist, up to 10): {result}"
        )
    except Exception as e:
        logger.error(f"Error in get_songs_by_genre: {e}")
        return f"Error looking up songs for genre '{genre}'. Please try again."


@tool
def check_for_songs(song_title: str) -> str:
    """
    Check if a song exists in the catalog by its name. Uses fuzzy matching.
    Returns up to 10 matches with full track details.
    """
    logger.info(f"TOOL_CALL: check_for_songs | song_title={song_title}")
    try:
        result = run_query_safe(
            """
            SELECT Track.TrackId,
                   Track.Name AS SongName,
                   Artist.Name AS ArtistName,
                   Album.Title AS AlbumTitle,
                   Genre.Name AS GenreName,
                   Track.Composer,
                   Track.Milliseconds,
                   ROUND(Track.Milliseconds / 60000.0, 1) AS DurationMinutes,
                   Track.Bytes,
                   Track.UnitPrice,
                   MediaType.Name AS MediaType
            FROM Track
            JOIN Album ON Track.AlbumId = Album.AlbumId
            JOIN Artist ON Album.ArtistId = Artist.ArtistId
            LEFT JOIN Genre ON Track.GenreId = Genre.GenreId
            LEFT JOIN MediaType ON Track.MediaTypeId = MediaType.MediaTypeId
            WHERE Track.Name LIKE :pattern
            ORDER BY Track.Name
            LIMIT 10;
            """,
            {"pattern": f"%{song_title}%"},
        )
        logger.info(f"TOOL_RESULT: check_for_songs | result_length={len(result)}")
        if result == "[]":
            return f"No songs found matching: {song_title}"
        return result
    except Exception as e:
        logger.error(f"Error in check_for_songs: {e}")
        return f"Error looking up song '{song_title}'. Please try again."


@tool
def get_track_details(track_id: str) -> str:
    """
    Get complete details for a specific track by its TrackId.
    Use this when the customer needs detailed info about a specific known track.
    """
    logger.info(f"TOOL_CALL: get_track_details | track_id={track_id}")
    try:
        result = run_query_safe(
            """
            SELECT Track.TrackId,
                   Track.Name AS SongName,
                   Artist.Name AS ArtistName,
                   Album.Title AS AlbumTitle,
                   Genre.Name AS GenreName,
                   Track.Composer,
                   Track.Milliseconds,
                   ROUND(Track.Milliseconds / 60000.0, 1) AS DurationMinutes,
                   Track.Bytes,
                   ROUND(Track.Bytes / 1048576.0, 1) AS SizeMB,
                   Track.UnitPrice,
                   MediaType.Name AS MediaType
            FROM Track
            LEFT JOIN Album ON Track.AlbumId = Album.AlbumId
            LEFT JOIN Artist ON Album.ArtistId = Artist.ArtistId
            LEFT JOIN Genre ON Track.GenreId = Genre.GenreId
            LEFT JOIN MediaType ON Track.MediaTypeId = MediaType.MediaTypeId
            WHERE Track.TrackId = :track_id;
            """,
            {"track_id": _safe_int(track_id, "track ID")},
        )
        logger.info(f"TOOL_RESULT: get_track_details | result_length={len(result)}")
        if result == "[]":
            return f"No track found with TrackId: {track_id}"
        return result
    except Exception as e:
        logger.error(f"Error in get_track_details: {e}")
        return f"Error looking up track {track_id}. Please try again."


music_tools = [
    get_albums_by_artist,
    get_tracks_by_artist,
    get_songs_by_genre,
    check_for_songs,
    get_track_details,
]
