import { useEffect, useState } from "react";

export default function SetlistDetail({ setlist }) {
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!setlist) return;
    setLoading(true);
    fetch(`/api/setlists/${setlist.id}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success) setSongs(data.data.songs);
      })
      .catch((err) => console.error("Error fetching setlist details:", err))
      .finally(() => setLoading(false));
  }, [setlist]);

  if (!setlist) return <p>Select a setlist to view details</p>;

  return (
    <div className="setlist-detail">
      <h2>{setlist.display_title || `${setlist.venue}, ${setlist.city}`}</h2>
      {loading && <p>Loading...</p>}
      <ol>
        {songs.map((song) => (
          <li key={song.position}>
            {song.name}
            {song.is_cover && <span> (cover of {song.original_artist})</span>}
            {song.is_encore && <span> – Encore {song.encore}</span>}
          </li>
        ))}
      </ol>
    </div>
  );
}
