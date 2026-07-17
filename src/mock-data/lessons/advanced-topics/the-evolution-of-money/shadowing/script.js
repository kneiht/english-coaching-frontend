
document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const audioSpeed = window.audioSpeed || 1.0;

    // Set audio speed for all audio elements
    document.querySelectorAll('audio').forEach(audio => {
        audio.playbackRate = audioSpeed;
        // When one audio plays, pause others
        audio.addEventListener('play', () => {
            document.querySelectorAll('audio').forEach(otherAudio => {
                if (otherAudio !== audio) {
                    otherAudio.pause();
                }
            });
        });
    });

    // Tab switching logic
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.tab;

            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            tabContents.forEach(content => {
                if (content.id === target) {
                    content.classList.remove('hidden');
                } else {
                    content.classList.add('hidden');
                }
            });
             // Pause all audio when switching tabs
            document.querySelectorAll('audio').forEach(audio => audio.pause());
        });
    });

    // Trigger click on the first tab to initialize view
    if (tabs.length > 0) {
        tabs[0].click();
    }
});
