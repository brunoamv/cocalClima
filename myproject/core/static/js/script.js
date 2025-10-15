



    
    // iCHAVE['text_icon']['text']['phrase']['reduced']

   

document.addEventListener("DOMContentLoaded", () => {

    // Enhanced camera status check with new streaming API
    function checkCameraStatus() {
        fetch("/streaming/api/status/")
            .then(response => response.json())
            .then(data => {
                let btn = document.getElementById("payBtn");
                let msg = document.getElementById("statusMsg");
                let btn2 = document.getElementById("payBtn2");
                let msg2 = document.getElementById("statusMsg2");
                
                // Update UI based on access status
                if (data.access_granted) {
                    btn.disabled = false;
                    btn.textContent = "Assistir Ao Vivo";
                    msg.textContent = "✅ " + data.message;
                    btn2.disabled = false;
                    btn2.textContent = "Assistir Ao Vivo";
                    msg2.textContent = "✅ " + data.message;
                } else if (data.payment_status === "pending") {
                    btn.disabled = false;
                    btn.textContent = "Pagar para Assistir";
                    msg.textContent = "💳 " + data.message;
                    btn2.disabled = false;
                    btn2.textContent = "Pagar para Assistir";
                    msg2.textContent = "💳 " + data.message;
                } else {
                    btn.disabled = true;
                    btn.textContent = "Câmera Indisponível";
                    msg.textContent = "📷 " + data.message;
                    btn2.disabled = true;
                    btn2.textContent = "Câmera Indisponível";
                    msg2.textContent = "📷 " + data.message;
                }
                
                // Store stream URL for later use
                if (data.stream_url) {
                    window.streamUrl = data.stream_url;
                }
            })
            .catch(error => {
                console.error('Error checking camera status:', error);
                let btn = document.getElementById("payBtn");
                let msg = document.getElementById("statusMsg");
                btn.disabled = true;
                btn.textContent = "Erro de Conexão";
                msg.textContent = "Erro ao verificar status da câmera";
            });
    }
    
    // Legacy YouTube check (keeping for backward compatibility)
    function checkYouTubeLive() {
        fetch("/check-youtube-live/")
            .then(response => response.json())
            .then(data => {
                // This is now deprecated - use checkCameraStatus instead
                console.warn('checkYouTubeLive is deprecated, use checkCameraStatus');
            });
    }
    
    
    // Enhanced payment button click handler
    function handlePaymentClick() {
        // Check current status first
        fetch("/streaming/api/status/")
            .then(response => response.json())
            .then(data => {
                if (data.access_granted) {
                    // User has access, show stream
                    showVideoStream(data.stream_url);
                } else if (data.payment_status === "pending") {
                    // User needs to pay
                    fetch("/create-payment/")
                        .then(response => response.json())
                        .then(paymentData => {
                            if (paymentData.init_point) {
                                window.location.href = paymentData.init_point;
                            } else {
                                alert("Erro ao processar pagamento.");
                            }
                        });
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error handling payment click:', error);
                alert("Erro de conexão. Tente novamente.");
            });
    }
    
    // Show HLS video stream
    function showVideoStream(streamUrl) {
        // Create video player modal
        const modal = document.createElement('div');
        modal.id = 'videoModal';
        modal.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.9); z-index: 1000; display: flex;
            align-items: center; justify-content: center;
        `;
        
        const videoContainer = document.createElement('div');
        videoContainer.style.cssText = `
            position: relative; width: 90%; max-width: 800px;
            background: black; border-radius: 10px; overflow: hidden;
        `;
        
        const video = document.createElement('video');
        video.style.cssText = 'width: 100%; height: auto;';
        video.controls = true;
        video.autoplay = true;
        
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '✕';
        closeBtn.style.cssText = `
            position: absolute; top: 10px; right: 10px; background: rgba(255,255,255,0.8);
            border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer;
            font-size: 16px; z-index: 1001;
        `;
        closeBtn.onclick = () => document.body.removeChild(modal);
        
        // Load HLS stream
        if (typeof Hls !== 'undefined' && Hls.isSupported()) {
            const hls = new Hls();
            hls.loadSource(streamUrl);
            hls.attachMedia(video);
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
            // Safari native HLS support
            video.src = streamUrl;
        } else {
            alert('Seu navegador não suporta streaming HLS.');
            return;
        }
        
        videoContainer.appendChild(video);
        videoContainer.appendChild(closeBtn);
        modal.appendChild(videoContainer);
        document.body.appendChild(modal);
    }

    document.getElementById("payBtn").addEventListener("click", handlePaymentClick);
    document.getElementById("payBtn2").addEventListener("click", handlePaymentClick);

    // Use new camera status check instead of YouTube
    checkCameraStatus();
    setInterval(checkCameraStatus, 15000); // Check every 15 seconds

const iCIDADE = "3137"; // Replace with your city ID
const iTOKEN = "546659d2c8b489261f185e4e10b21d3c"; // Replace with your token

const weatherIcons = {
    "ec": "fa-cloud-sun",  // Parcialmente nublado
    "ci": "fa-cloud-showers-heavy", // Chuvas isoladas
    "ch": "fa-cloud-rain", // Chuvoso
    "t": "fa-bolt", // Tempestade
    "p": "fa-cloud", // Nublado
    "n": "fa-moon", // Noite limpa
    "g": "fa-wind", // Ventos fortes
    "ne": "fa-snowflake" // Neve
};

fetch("/weather/")
  .then(response => response.json())
  .then(data => {
    const iconClass = weatherIcons[data.data.icon] || "fa-cloud";

    document.getElementById("forecast-hoje").innerHTML = `
      <h4>Clima Atual</h4>
      <div class="forecast-grid hoje">
        <div class="forecast-item destaque">
          <i class="fas ${iconClass} fa-3x"></i>
          <div>
            <p><strong>${data.data.condition}</strong></p>
            <p>${data.name}</p>
            <p>🌡 ${data.data.temperature}°C | 💧 ${data.data.humidity}%</p>
            <p>💨 ${data.data.wind_velocity} km/h (${data.data.wind_direction})</p>
            <p>Ultima Atualização: ${data.data.date}</p>
          </div>
        </div>
      </div>
    `;
  })
  .catch(error => console.error("Erro ao buscar dados do clima:", error));



    const forecastContainer = document.getElementById("forecast2");
  
    const climaTempoIcons2 = {
        "2r": "fa-cloud",  // Cloudy
        "2rn": "fa-cloud-moon",  // Cloudy Night
        "1": "fa-sun",  // Clear Sky
        "1n": "fa-moon",  // Clear Night
        "3": "fa-cloud-showers-heavy",  // Rain
        "4": "fa-bolt",  // Storm
    };  
    
    function getWeekday(dateString) {
      const days = ["Domingo", "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado"];
      const [year, month, day] = dateString.split("-").map(Number);
      const date = new Date(year, month - 1, day);  // Mês começa do zero
      return days[date.getDay()];
  }
    
fetch(`https://apiadvisor.climatempo.com.br/api/v1/forecast/locale/${iCIDADE}/days/15?token=${iTOKEN}`)
.then(response => response.json())
.then(data => {
  let html = "<h4>Previsão da Semana</h4><div class='forecast-grid semana'>";

  data.data.slice(1, 8).forEach(day => {
    const icon = climaTempoIcons2[day.text_icon.icon.day] || "fa-cloud";
    const weekday = getWeekday(day.date);

    html += `
      <div class="forecast-item">
        <i class="fas ${icon} fa-2x"></i>
        <div>
          <strong>${weekday} (${day.date_br})</strong>
          <p>🌡 ${day.temperature.max}°C / ${day.temperature.min}°C</p>
          <p>💧 ${day.rain.probability}% - ${day.text_icon.text.phrase.reduced}</p>
        </div>
      </div>`;
  });

  html += "</div>";
  forecastContainer.innerHTML = html;
})
.catch(error => {
  forecastContainer.innerHTML = "<p class='text-danger'>Erro ao carregar a previsão do tempo.</p>";
  console.error("Erro na previsão:", error);
});

  
      const menuToggle = document.getElementById("menuToggle");
      const menuDropdown = document.getElementById("menuDropdown");
  
     menuToggle?.addEventListener("click", () => {
     menuDropdown.style.display =
     menuDropdown.style.display === "block" ? "none" : "block";
  });

    
    
  });


  

