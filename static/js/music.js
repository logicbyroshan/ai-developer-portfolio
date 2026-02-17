// js/music.js - Manual Playlist Integration
document.addEventListener('DOMContentLoaded', () => {
    setupPlaylistInteractions();
});

/**
 * Setup playlist card interactions
 */
function setupPlaylistInteractions() {
    // Handle playlist image clicks with loading feedback
    document.querySelectorAll('.playlist-image').forEach(link => {
        link.addEventListener('click', () => {
            const playlistCard = link.closest('.playlist-card');
            if (playlistCard) {
                playlistCard.classList.add('loading');
                setTimeout(() => playlistCard.classList.remove('loading'), 2000);
            }
        });
    });
}