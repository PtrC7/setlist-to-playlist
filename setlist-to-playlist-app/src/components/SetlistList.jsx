import { useEffect, useMemo, useState } from "react";

function parseSetlistDate(dateStr) {
  if (!dateStr) return null;
  const parts = dateStr.split("-");
  if (parts.length !== 3) return null;

  let day, month, year;
  if (parseInt(parts[0], 10) > 12) {
    [day, month, year] = parts.map((p) => parseInt(p, 10)); // DD-MM-YYYY
  } else {
    [month, day, year] = parts.map((p) => parseInt(p, 10)); // MM-DD-YYYY
  }

  const dt = new Date(year, month - 1, day);
  return isNaN(dt.getTime()) ? null : dt;
}

function formatDatePretty(dt) {
  if (!dt) return "";
  return dt.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function SetlistList({ artist, onSelectSetlist }) {
  const [setlists, setSetlists] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState(null); // ✅ track selected concert

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

  const today = useMemo(() => {
    const t = new Date();
    t.setHours(0, 0, 0, 0);
    return t;
  }, []);

  if (!artist) return <p className="muted">Search an artist to view setlists</p>;

  const handleSelect = (setlist) => {
    setSelectedId(setlist.id); // ✅ update selection
    onSelectSetlist(setlist);
  };

  return (
    <div className="setlist-pane">
      <h3 className="setlist-pane-title">{artist.name} – Setlists</h3>

      {loading && <p className="muted">Loading…</p>}

      <ul className="setlist-ul">
        {setlists.map((s) => {
          const dt = parseSetlistDate(s.date);
          const isFuture = dt ? dt.getTime() > today.getTime() : false;
          const formattedDate = formatDatePretty(dt);
          const isSelected = s.id === selectedId; // ✅

          return (
            <li
              key={s.id}
              className={`setlist-li ${isFuture ? "future" : ""} ${
                isSelected ? "selected" : ""
              }`}
              onClick={() => handleSelect(s)}
              title={s.display_title || ""}
            >
              <div className="setlist-li-main">
                <div className="setlist-venue">
                  {s.venue}
                  {s.city ? `, ${s.city}` : ""}
                </div>
                {formattedDate && (
                  <div className="setlist-date">{formattedDate}</div>
                )}
              </div>

              {typeof s.songs_count === "number" && (
                <div className="setlist-count">{s.songs_count} songs</div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
