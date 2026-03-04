const API_URL = "http://127.0.0.1:8000/api";
const DEFAULT_LOGO = "https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green.png";

async function loadStats() {
    try {
        const res = await fetch(`${API_URL}/stats`);
        const data = await res.json();
        document.getElementById('total-tracks').innerText = data.total_tracks || 0;
        document.getElementById('unique-artists').innerText = data.unique_artists || 0;
    } catch (e) {
        console.error("Erreur stats:", e);
    }
}

async function loadHistory() {
    try {
        const res = await fetch(`${API_URL}/history`);
        const tracks = await res.json();
        const list = document.getElementById('history-list');
        list.innerHTML = "";
        
        if (tracks.length === 0) {
            list.innerHTML = "<p>Aucun historique disponible.</p>";
            return;
        }

        tracks.slice(0, 20).forEach(track => {
            const date = new Date(track.played_at).toLocaleString('fr-FR');
            list.innerHTML += `
                <div class="track-card">
                    <img src="${track.album_cover_url || DEFAULT_LOGO}" alt="Cover">
                    <div class="track-info">
                        <h4>${track.track_name}</h4>
                        <p>${track.artist_name} • <i>${date}</i></p>
                    </div>
                </div>
            `;
        });
    } catch (e) {
        console.error("Erreur historique:", e);
    }
}

async function loadPodiums() {
    try {
        const [artistsRes, tracksRes] = await Promise.all([
            fetch(`${API_URL}/top-artists?limit=3`),
            fetch(`${API_URL}/top-tracks?limit=3`)
        ]);

        const topArtists = await artistsRes.json();
        const topTracks = await tracksRes.json();

        const generatePodiumHTML = (data, isArtist) => {
            if (data.length === 0) return "<p style='color: #777;'>Aucune donnée</p>";

            const displayOrder = [data[1], data[0], data[2]].filter(Boolean);
            const medals = { 0: '🥈', 1: '🥇', 2: '🥉' };
            const classes = { 0: 'second', 1: 'first', 2: 'third' };

            return displayOrder.map((item, index) => {
                const podiumClass = classes[index];
                const medal = medals[index];
                const title = isArtist ? item.artist_name : item.track_name;
                const subtitle = isArtist ? "" : `<p>${item.artist_name}</p>`;

                return `
                    <div class="podium-item ${podiumClass}">
                        <span class="position">${medal}</span>
                        <img src="${item.album_cover_url || DEFAULT_LOGO}" alt="Cover">
                        <h4>${title}</h4>
                        ${subtitle}
                        <p><strong>${item.count}</strong> écoutes</p>
                    </div>
                `;
            }).join('');
        };

        document.getElementById('artists-podium').innerHTML = generatePodiumHTML(topArtists, true);
        document.getElementById('tracks-podium').innerHTML = generatePodiumHTML(topTracks, false);

    } catch (e) {
        console.error("Erreur podiums:", e);
    }
}

async function loadOfficialArchives() {
    try {
        const [artists, tracks] = await Promise.all([
            fetch(`${API_URL}/official-top-artists`).then(r => r.json()),
            fetch(`${API_URL}/official-top-tracks`).then(r => r.json())
        ]);

        document.getElementById('official-artists-list').innerHTML = artists.map((a, i) => `
            <div class="official-item">
                <span class="rank">${i+1}</span>
                <img src="${a.image || DEFAULT_LOGO}" style="border-radius: 50%">
                <div class="official-info">
                    <strong>${a.name}</strong>
                    <small>${a.genres.join(', ')}</small>
                </div>
            </div>
        `).join('');

        document.getElementById('official-tracks-list').innerHTML = tracks.map((t, i) => `
            <div class="official-item">
                <span class="rank">${i+1}</span>
                <img src="${t.cover || DEFAULT_LOGO}">
                <div class="official-info">
                    <strong>${t.name}</strong>
                    <small>${t.artist}</small>
                </div>
            </div>
        `).join('');
    } catch (e) { 
        console.error("Erreur Archives:", e); 
    }
}

async function syncData() {
    const btn = document.querySelector('button');
    btn.innerText = "⏳ Synchro...";
    btn.disabled = true;
    try {
        const res = await fetch(`${API_URL}/sync`, { method: 'POST' });
        const data = await res.json();
        alert(`✅ Ajoutés : ${data.added} morceaux`);
        await init();
    } catch (e) {
        alert("❌ Erreur lors de la synchronisation");
    } finally {
        btn.innerText = "📡 Synchroniser Spotify";
        btn.disabled = false;
    }
}

async function init() {
    await loadStats();
    await loadPodiums();
    await loadOfficialArchives();
    await loadHistory();
}

document.addEventListener('DOMContentLoaded', init);