import { useEffect, useState } from "react";

export default function SetlistDetail({ setlist }) {
  const [songs, setSongs] = useState([]);
  const [selectedSongs, setSelectedSongs] = useState({});
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [playlistUrl, setPlaylistUrl] = useState(null);
  const [error, setError] = useState(null);
  const [artistImage, setArtistImage] = useState(null);
  const [isPublic, setIsPublic] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    if (!setlist) return;
    setLoading(true);
    setPlaylistUrl(null);
    setError(null);

    fetch(`/api/setlists/${setlist.id}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setSongs(data.data.songs);
          setArtistImage(data.data.artist_image || null);

          const defaults = {};
          data.data.songs.forEach((song) => {
            defaults[song.position] = !(
              song.is_cover ||
              song.is_encore ||
              song.spotify_uri == null ||
              song.spotify_uri == undefined
            );
          });
          setSelectedSongs(defaults);
        }
      })
      .catch((err) => console.error("Error fetching setlist details:", err))
      .finally(() => setLoading(false));
  }, [setlist]);

  async function checkAuth() {
    const res = await fetch("/api/auth/me");
    const data = await res.json();
    if (data.authenticated) {
      setUser(data.user);
      return data.user;
    } else {
      setUser(null);
      return null;
    }
  }

  function openSpotifyLoginPopup() {
    const w = 500, h = 700;
    const left = window.screenX + (window.outerWidth - w) / 2;
    const top = window.screenY + (window.outerHeight - h) / 2;
    const popup = window.open(
      "/api/auth/login",
      "Spotify Login",
      `width=${w},height=${h},left=${left},top=${top},resizable=yes,scrollbars=yes`
    );
    return new Promise((resolve) => {
      function handler(evt) {
        if (evt.data && typeof evt.data === "object" && "success" in evt.data) {
          window.removeEventListener("message", handler);
          if (evt.data.success) {
            checkAuth().then(() => resolve(true));
          } else {
            resolve(false);
          }
        }
      }
      window.addEventListener("message", handler);
    });
  }

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    setUser(null);
  }

  const toggleSong = (pos) => {
    setSelectedSongs((prev) => ({
      ...prev,
      [pos]: !prev[pos],
    }));
  };

  const handleCreatePlaylist = async () => {
    if (!setlist) return;
    setCreating(true);
    setError(null);

    try {
      const loggedInUser = await checkAuth();
      if (!loggedInUser) {
        await openSpotifyLoginPopup();
        const newUser = await checkAuth();
        if (!newUser) {
          setCreating(false);
          setError("Spotify login is required to create a playlist.");
          return;
        }
      }
      const selectedKeys = songs
        .filter((s) => selectedSongs[s.position])
        .map((s) => ({ position: s.position, set_number: s.set_number }));

      const res = await fetch(`/api/playlists/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          setlist_id: setlist.id,
          selected: selectedKeys,
          date: setlist.date,
          venue: setlist.venue,
          city: setlist.city,
          country: setlist.country,
          tour: setlist.tour,
          public: isPublic,
        }),
      });

      const data = await res.json();
      if (data.success) {
        setPlaylistUrl(data.data.playlist_url);
      } else {
        setError(data.error || "Failed to create playlist");
      }
    } catch (err) {
      console.error("Error creating playlist:", err);
      setError("An unexpected error occurred.");
    } finally {
      setCreating(false);
    }
  };

  if (!setlist) return <p>Select a setlist to view details</p>;

  const total = songs.length;
  const selectedCount = songs.filter((s) => selectedSongs[s.position]).length;

  return (
    <div className="setlist-detail-wrapper">
      <div className="setlist-card">
        <h2 className="setlist-header">
          {setlist.display_title || `${setlist.venue}, ${setlist.city}`}
        </h2>

        <div className="setlist-content">
          <div className="song-list-column">
            {loading && <p>Loading...</p>}
            {!loading && songs.length > 0 && (
              <ol className="song-list">
                {songs.map((song) => {
                  const isSpotifyMissing = song.spotify_uri == null || song.spotify_uri == undefined;
                  const isSelected = selectedSongs[song.position] && !isSpotifyMissing;

                  return (
                    <li
                      key={song.position}
                      className={`song-item ${isSelected ? "selected" : "faded"}`}
                      onClick={() => {
                        if (!isSpotifyMissing) toggleSong(song.position);
                      }}
                    >
                      <div className="song-entry">
                        {song.album_image && (
                          <img
                            src={song.album_image}
                            alt={`${song.album || "album"} cover`}
                            className="album-thumb"
                          />
                        )}
                        <div className="song-info">
                          <span className="song-name">{song.name}</span>

                          {(song.is_cover || song.is_encore) && (
                            <span className="song-meta">
                              {song.is_cover && `cover of ${song.original_artist}`}
                              {song.is_cover && song.is_encore && " · "}
                              {song.is_encore && `encore ${song.encore}`}
                            </span>
                          )}

                          {song.album && (
                            <span className="song-album">{song.album}</span>
                          )}

                          {isSpotifyMissing && (
                            <span className="song-missing">Not found on Spotify</span>
                          )}
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ol>
            )}
          </div>
          <div className="artist-column">
            {artistImage && (
              <img
                src={artistImage}
                alt={`${setlist.artist} artist`}
                className="artist-banner"
              />
            )}
            <p className="playlist-summary">
              {selectedCount} of {total} songs selected
            </p>

            <div className="toggle-container">
              <span className="toggle-label">Private</span>
              <label className="switch">
                <input
                  type="checkbox"
                  checked={isPublic}
                  onChange={(e) => setIsPublic(e.target.checked)}
                />
                <span className="slider"></span>
              </label>
              <span className="toggle-label">Public</span>
            </div>
            
            <div className="spotify-actions">
              {user ? (
                <>
                  {playlistUrl ? (
                    <a
                      href={playlistUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="spotify-button"
                    >
                      View Playlist on Spotify
                    </a>
                  ) : (
                    <button
                      onClick={handleCreatePlaylist}
                      disabled={creating}
                      className="spotify-button"
                    >
                      {creating ? "Creating..." : "Create Spotify Playlist"}
                    </button>
                  )}

                  <div className="spotify-user-info">
                    Logged in as <b>{user.name}</b>
                    <button onClick={handleLogout} className="logout-button">
                      Log out
                    </button>
                  </div>
                </>
              ) : (
                <button onClick={openSpotifyLoginPopup} className="spotify-button login">
                  Log in with Spotify
                </button>
              )}
              {error && <p className="error-text">{error}</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}