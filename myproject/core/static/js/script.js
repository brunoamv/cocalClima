



    
    // iCHAVE['text_icon']['text']['phrase']['reduced']

   

document.addEventListener("DOMContentLoaded", () => {

    function checkYouTubeLive() {
        fetch("/check-youtube-live/")
            .then(response => response.json())
            .then(data => {
                let btn = document.getElementById("payBtn");
                let msg = document.getElementById("statusMsg");
                let btn2 = document.getElementById("payBtn2");
                let msg2 = document.getElementById("statusMsg2");
                if (data.live) {
                    btn.disabled = false;
                    btn.textContent = "Participar do Evento";
                    msg.textContent = "Transmissão ao vivo disponível!";
                    btn2.disabled = false;
                    btn2.textContent = "Participar do Evento";
                    msg2.textContent = "Transmissão ao vivo disponível!";
                } else {
                    btn.disabled = true;
                    btn.textContent = "Evento ainda não começou";
                    msg.textContent = "A transmissão ainda não começou. Aguarde.";
                    btn2.disabled = true;
                    btn2.textContent = "Evento ainda não começou";
                    msg2.textContent = "A transmissão ainda não começou. Aguarde.";
                }
            });
    }
    
    
    document.getElementById("payBtn").addEventListener("click", function () {
        fetch("/create-payment/")
            .then(response => response.json())
            .then(data => {
                if (data.init_point) {
                    window.location.href = data.init_point;
                } else {
                    alert("Erro ao processar pagamento.");
                }
            });
    });
    
    checkYouTubeLive();
    setInterval(checkYouTubeLive, 30000);

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
        const date = new Date(dateString);
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


  

