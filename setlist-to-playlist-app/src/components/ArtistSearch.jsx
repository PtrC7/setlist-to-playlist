import { useState } from "react";

export default function ArtistSearch({ onSelectArtist }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

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
    onSelectArtist(artist);
    setResults([]);
    setShowDropdown(false);
    setQuery(artist.name);
  };

  return (
    <div className="artist-search">
      <form onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search artist..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setShowDropdown(true)}
        />
        <button type="submit">Search</button>
      </form>

      {loading && <p>Loading...</p>}

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
