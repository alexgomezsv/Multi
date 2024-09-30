document.addEventListener("DOMContentLoaded", function () {
    const videoGrid = document.getElementById("video-grid");
    const addScreenButton = document.getElementById("add-screen");
    const maxScreens = 15;

    // Función para agregar un nuevo reproductor de video
    function addVideoScreen(url = '') {
        if (videoGrid.children.length >= maxScreens) {
            alert('Has alcanzado el número máximo de pantallas (15).');
            return;
        }

        const videoContainer = document.createElement("div");
        videoContainer.className = "video-container";

        const videoElement = document.createElement("video");
        videoElement.className = "video-js vjs-default-skin";
        videoElement.setAttribute("controls", "true");
        videoElement.setAttribute("preload", "auto");

        videoContainer.appendChild(videoElement);

        // Campo de texto para la URL
        const urlInput = document.createElement("input");
        urlInput.type = "text";
        urlInput.placeholder = "Ingrese URL del canal...";
        urlInput.value = url;
        urlInput.addEventListener("change", function () {
            setupVideoPlayer(videoElement, urlInput.value);  // Configurar el reproductor con la nueva URL
        });
        videoContainer.appendChild(urlInput);

        // Botones de control
        const controlsDiv = document.createElement("div");
        controlsDiv.className = "controls";

        const playButton = document.createElement("button");
        playButton.textContent = "Play";
        playButton.onclick = () => {
            try {
                videoElement.play();
            } catch (error) {
                console.error("Error al intentar reproducir el video:", error);
                alert('No se puede reproducir el video. Verifica la URL o el formato.');
            }
        };

        const pauseButton = document.createElement("button");
        pauseButton.textContent = "Pause";
        pauseButton.onclick = () => videoElement.pause();

        const stopButton = document.createElement("button");
        stopButton.textContent = "Stop";
        stopButton.onclick = () => {
            videoElement.pause();
            videoElement.currentTime = 0;
        };

        controlsDiv.appendChild(playButton);
        controlsDiv.appendChild(pauseButton);
        controlsDiv.appendChild(stopButton);
        videoContainer.appendChild(controlsDiv);

        videoGrid.appendChild(videoContainer);

        // Configurar el reproductor de video con la URL inicial
        setupVideoPlayer(videoElement, url);
    }

    function setupVideoPlayer(videoElement, url) {
        const player = videojs(videoElement);

        if (url.endsWith('.m3u8')) {
            // Usar HLS.js para manejar archivos HLS si el navegador no lo soporta de forma nativa
            if (Hls.isSupported()) {
                const hls = new Hls();
                hls.loadSource(url);
                hls.attachMedia(videoElement);
            } else if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
                // Soporte nativo de HLS en Safari
                videoElement.src = url;
            } else {
                alert('Este navegador no soporta HLS.');
            }
        } else if (url.startsWith('http://') || url.startsWith('https://')) {
            // Manejar URLs HTTP directas (MP4)
            player.src({ src: url, type: 'video/mp4' });
        } else {
            alert('Formato no soportado o URL incorrecta.');
        }

        // Manejar errores de reproducción
        videoElement.onerror = function () {
            console.error(`Error al cargar el video desde la URL: ${url}`);
            alert('Error al cargar el video. Verifica la URL o la configuración del servidor.');
        };
    }

    // Manejar el botón para agregar pantallas
    addScreenButton.addEventListener("click", function () {
        addVideoScreen();
    });

    // Agregar pantallas iniciales
    addVideoScreen();
});
