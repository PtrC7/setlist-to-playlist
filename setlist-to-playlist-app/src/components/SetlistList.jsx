import { useEffect, useState } from "react";

export default function SetlistList({ artist, onSelectSetlist }) {
  const [setlists, setSetlists] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!artist) return;
    setLoading(true);
    fetch(`/api/artists/${artist.mbid}/setlists`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success) setSetlists(data.data);
      })
      .catch((err) => console.error("Error fetching setlists:", err))
      .finally(() => setLoading(false));
  }, [artist]);

  if (!artist) return <p>Select an artist to view setlists</p>;

  return (
    <div className="setlist-list">
      <h3>{artist.name} – Setlists</h3>
      {loading && <p>Loading...</p>}
      <ul>
        {setlists.map((s) => (
          <li
            key={s.id}
            onClick={() => onSelectSetlist(s)}
            className="setlist-item"
          >
            {s.display_title || `${s.venue}, ${s.city} (${s.date})`}
          </li>
        ))}
      </ul>
    </div>
  );
}
