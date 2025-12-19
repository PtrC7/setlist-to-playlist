import { useEffect, useRef, useState } from "react";

export default function ArtistSearch({ onSelectArtist }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  const today = new Date()
  
  const [month, setMonth] = useState("");
  const [year, setYear] = useState(String(today.getFullYear()));
  const [venue, setVenue] = useState("");
  const [tour, setTour] = useState("");

  const [selectedArtist, setSelectedArtist] = useState(null);
  const debounceRef = useRef(null);
  const isSelectingRef = useRef(false);

  useEffect(() => {
    if (isSelectingRef.current) {
      isSelectingRef.current = false;
      return;
    }

    if (!query || query.length < 2) {
      setResults([]);
      setShowDropdown(false);
      return;
    }

    clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await fetch(
          `/api/artists/search?q=${encodeURIComponent(query)}`
        );
        const data = await res.json();
        if (data.success) {
          setResults(data.data);
          setShowDropdown(true);
        }
      } catch (err) {
        console.error("Artist search error:", err);
      } finally {
        setLoading(false);
      }
    }, 300);
  }, [query]);


  const handleSearchClick = (e) => {
    e.preventDefault();

    if (!selectedArtist) return;

    onSelectArtist({
      ...selectedArtist,
      filters: { month, year, venue, tour },
    });
  };

  const handleSelect = (artist) => {
    isSelectingRef.current = true; 

    const enriched = {
      ...artist,
      filters: { month, year, venue, tour },
    };

    setSelectedArtist(enriched);
    onSelectArtist(enriched);

    setQuery(artist.name);
    setResults([]);
    setShowDropdown(false);
  };

  return (
    <div className="artist-search">
      <form onSubmit={handleSearchClick} className="artist-search-form">
        <div className="artist-search-row">
          <input
            type="text"
            placeholder="Search artist…"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedArtist(null);
            }}
            onFocus={() => results.length && setShowDropdown(true)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && showDropdown) {
                e.preventDefault();
                setShowDropdown(false);
              }
            }}
          />
          <button type="submit">Search</button>
        </div>

        <div className="artist-filter-row">
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
      </form>

      
      {loading && <p>Loading…</p>}

      {showDropdown && results.length > 0 && (
        <ul className="artist-dropdown">
          {results.map((artist) => (
            <li
              key={artist.mbid}
              className="artist-item"
              onClick={() => handleSelect(artist)}
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
