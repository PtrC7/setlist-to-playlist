import { useState } from "react";
import ArtistSearch from "./components/ArtistSearch";
import SetlistList from "./components/SetlistList";
import SetlistDetail from "./components/SetlistDetail";
import "./App.css";

function App() {
  const [selectedArtist, setSelectedArtist] = useState(null);
  const [selectedSetlist, setSelectedSetlist] = useState(null);

  return (
    <div className="app-container">
      <div className="sidebar">
        <ArtistSearch onSelectArtist={(a) => { setSelectedArtist(a); setSelectedSetlist(null); }} />
        <SetlistList artist={selectedArtist} onSelectSetlist={setSelectedSetlist} />
      </div>
      <div className="main-content">
        <SetlistDetail setlist={selectedSetlist} />
      </div>
    </div>
  );
}

export default App;
