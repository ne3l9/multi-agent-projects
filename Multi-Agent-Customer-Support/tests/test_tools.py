"""Tests for music catalog and invoice tools."""

import json
import pytest
from src.tools.music_catalog import (
    get_albums_by_artist,
    get_tracks_by_artist,
    get_songs_by_genre,
    check_for_songs,
    get_track_details,
)
from src.tools.invoice import (
    get_invoices_by_customer_sorted_by_date,
    get_invoice_line_items_sorted_by_price,
    get_employee_by_invoice_and_customer,
    get_invoice_line_items,
)


class TestMusicCatalogTools:
    def test_get_albums_by_artist_found(self):
        result = get_albums_by_artist.invoke({"artist": "AC/DC"})
        data = json.loads(result)
        assert len(data) >= 1
        assert any("AC/DC" in album["ArtistName"] for album in data)
        assert "AlbumId" in data[0]

    def test_get_albums_by_artist_not_found(self):
        result = get_albums_by_artist.invoke({"artist": "NonexistentArtistXYZ"})
        assert "No albums found" in result

    def test_get_tracks_by_artist_found(self):
        result = get_tracks_by_artist.invoke({"artist": "AC/DC"})
        assert "Total tracks found" in result
        assert "Sample" in result

    def test_get_tracks_by_artist_not_found(self):
        result = get_tracks_by_artist.invoke({"artist": "NonexistentArtistXYZ"})
        assert "No tracks found" in result

    def test_get_songs_by_genre_found(self):
        result = get_songs_by_genre.invoke({"genre": "Rock"})
        assert "Total Rock tracks" in result
        assert "Representative sample" in result

    def test_get_songs_by_genre_deterministic(self):
        """Verify the same query returns the same results (deterministic)."""
        r1 = get_songs_by_genre.invoke({"genre": "Rock"})
        r2 = get_songs_by_genre.invoke({"genre": "Rock"})
        assert r1 == r2

    def test_get_songs_by_genre_not_found(self):
        result = get_songs_by_genre.invoke({"genre": "NonexistentGenreXYZ"})
        assert "No songs found" in result

    def test_check_for_songs_found(self):
        result = check_for_songs.invoke({"song_title": "Balls to the Wall"})
        assert result != "[]"
        assert "No songs found" not in result

    def test_check_for_songs_not_found(self):
        result = check_for_songs.invoke({"song_title": "ThisSongDoesNotExist12345"})
        assert "No songs found" in result

    def test_get_track_details_found(self):
        result = get_track_details.invoke({"track_id": "1"})
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["TrackId"] == 1

    def test_get_track_details_not_found(self):
        result = get_track_details.invoke({"track_id": "99999"})
        assert "No track found" in result

    def test_get_track_details_invalid_id(self):
        result = get_track_details.invoke({"track_id": "abc"})
        assert "Error" in result or "Invalid" in result


class TestInvoiceTools:
    def test_get_invoices_by_customer(self):
        result = get_invoices_by_customer_sorted_by_date.invoke({"customer_id": "1"})
        data = json.loads(result)
        assert len(data) >= 1
        assert data[0]["CustomerId"] == 1
        # Verify sorted by date DESC
        dates = [d["InvoiceDate"] for d in data]
        assert dates == sorted(dates, reverse=True)

    def test_get_invoices_no_customer(self):
        result = get_invoices_by_customer_sorted_by_date.invoke({"customer_id": "99999"})
        assert "No invoices found" in result

    def test_get_invoice_line_items_sorted_by_price(self):
        result = get_invoice_line_items_sorted_by_price.invoke({"customer_id": "1"})
        data = json.loads(result)
        assert len(data) >= 1
        assert "TrackName" in data[0]
        assert "UnitPrice" in data[0]

    def test_get_employee_by_invoice(self):
        # First get an invoice for customer 1
        invoices = json.loads(
            get_invoices_by_customer_sorted_by_date.invoke({"customer_id": "1"})
        )
        invoice_id = str(invoices[0]["InvoiceId"])
        result = get_employee_by_invoice_and_customer.invoke(
            {"invoice_id": invoice_id, "customer_id": "1"}
        )
        data = json.loads(result)
        assert len(data) >= 1
        assert "FirstName" in data[0]

    def test_get_invoice_line_items(self):
        invoices = json.loads(
            get_invoices_by_customer_sorted_by_date.invoke({"customer_id": "1"})
        )
        invoice_id = str(invoices[0]["InvoiceId"])
        result = get_invoice_line_items.invoke(
            {"invoice_id": invoice_id, "customer_id": "1"}
        )
        data = json.loads(result)
        assert len(data) >= 1
        assert "TrackName" in data[0]
