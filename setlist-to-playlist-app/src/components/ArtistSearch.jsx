import { useState } from "react";

export default function ArtistSearch({ onSelectArtist }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  const [month, setMonth] = useState("");
  const [year, setYear] = useState("");
  const [venue, setVenue] = useState("");
  const [tour, setTour] = useState("");

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/artists/search?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      if (data.success) {
        setResults(data.data);
        setShowDropdown(true);
      }
    } catch (err) {
      console.error("Error searching artist:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (artist) => {
    onSelectArtist({
      ...artist,
      filters: {
        month,
        year,
        venue,
        tour,
      },
    });

    setResults([]);
    setShowDropdown(false);
    setQuery(artist.name);
  };

  return (
    <div className="artist-search">
      <form onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search artist…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit">Search</button>
      </form>

      <div style={{ display: "flex", gap: "0.4rem", marginTop: "0.4rem" }}>
        <select value={month} onChange={(e) => setMonth(e.target.value)}>
          <option value="">Month</option>
          {["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
            .map((m, i) => (
              <option key={m} value={i + 1}>{m}</option>
          ))}
        </select>

        <input
          type="number"
          placeholder="Year"
          value={year}
          onChange={(e) => setYear(e.target.value)}
          style={{ width: "80px" }}
        />

        <input
          type="text"
          placeholder="Venue"
          value={venue}
          onChange={(e) => setVenue(e.target.value)}
        />

        <input
          type="text"
          placeholder="Tour"
          value={tour}
          onChange={(e) => setTour(e.target.value)}
        />
      </div>

      {loading && <p>Loading…</p>}

      {showDropdown && results.length > 0 && (
        <ul className="artist-dropdown">
          {results.map((artist) => (
            <li
              key={artist.mbid}
              onClick={() => handleSelect(artist)}
              className="artist-item"
            >
              <div className="artist-name">{artist.name}</div>
              {artist.disambiguation && (
                <div className="artist-meta">{artist.disambiguation}</div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
