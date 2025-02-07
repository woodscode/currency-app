document.addEventListener("DOMContentLoaded", () => {
    // Initialize USD tracking components
    loadHistoricalData();
    fetchNews();
    fetchAnalysis();
    setupModeToggle();
    setupTimeRangeSelector();
    // Uncomment the next line if background music is desired.
    // setupBackgroundMusic();
  });
  
  //////////////////////////////////
  // USD Tracking Functions
  //////////////////////////////////
  async function loadHistoricalData() {
    const rangeSelect = document.getElementById("timeRangeSelect");
    const range = rangeSelect.value; // "24h", "7d", or "30d"
    const endpoints = {
      "24h": "/historical-data/24h",
      "7d": "/historical-data/7d",
      "30d": "/historical-data"
    };
    const endpoint = endpoints[range] || "/historical-data";
  
    try {
      const response = await fetch(endpoint);
      const data = await response.json();
      if (data.error) {
        console.error("Historical data error:", data.error);
        return;
      }
  
      const { dates: labels, cad: cadData, mxn: mxnData, cny: cnyData, jpy: jpyData } = data;
  
      // Chart 1: Actual Exchange Rates
      const ctxExchange = document.getElementById('currencyChart').getContext('2d');
      new Chart(ctxExchange, {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: 'USD to CAD',
              data: cadData,
              borderColor: 'blue',
              backgroundColor: 'rgba(0, 0, 255, 0.1)',
              fill: true,
              tension: 0.2
            },
            {
              label: 'USD to MXN',
              data: mxnData,
              borderColor: 'green',
              backgroundColor: 'rgba(0, 128, 0, 0.1)',
              fill: true,
              tension: 0.2
            },
            {
              label: 'USD to CNY',
              data: cnyData,
              borderColor: 'red',
              backgroundColor: 'rgba(255, 0, 0, 0.1)',
              fill: true,
              tension: 0.2
            },
            {
              label: 'USD to JPY',
              data: jpyData,
              borderColor: 'gold',
              backgroundColor: 'rgba(255, 215, 0, 0.1)',
              fill: true,
              tension: 0.2
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { title: { display: true, text: "Date" } },
            y: { title: { display: true, text: "Exchange Rate" } }
          }
        }
      });
  
      // Helper for normalization: convert the first value to 100%
      const normalize = (arr) =>
        arr.map(val => parseFloat(((val / arr[0]) * 100).toFixed(2)));
      const cadNormalized = normalize(cadData);
      const mxnNormalized = normalize(mxnData);
      const cnyNormalized = normalize(cnyData);
      const jpyNormalized = normalize(jpyData);
  
      // Composite: average of normalized values for all four currencies.
      const composite = labels.map((_, idx) => {
        const avg = (cadNormalized[idx] + mxnNormalized[idx] + cnyNormalized[idx] + jpyNormalized[idx]) / 4;
        return parseFloat(avg.toFixed(2));
      });
  
      // Chart 2: USD Strength Index (Composite)
      const ctxStrength = document.getElementById('strengthChart').getContext('2d');
      new Chart(ctxStrength, {
        type: 'line',
        data: {
          labels,
          datasets: [{
            label: 'USD Strength Index',
            data: composite,
            borderColor: 'purple',
            backgroundColor: 'rgba(128, 0, 128, 0.1)',
            fill: true,
            tension: 0.2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { title: { display: true, text: "Date" } },
            y: { 
              title: { display: true, text: "Composite Strength (%)" },
              ticks: { callback: value => `${value}%` }
            }
          }
        }
      });
  
      // Chart 3: Normalized Currency Strength (Separate Lines)
      const ctxNormalized = document.getElementById('normalizedChart').getContext('2d');
      new Chart(ctxNormalized, {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: 'USD vs. CAD (Normalized)',
              data: cadNormalized,
              borderColor: 'orange',
              backgroundColor: 'rgba(255, 165, 0, 0.1)',
              fill: true,
              tension: 0.2
            },
            {
              label: 'USD vs. MXN (Normalized)',
              data: mxnNormalized,
              borderColor: 'teal',
              backgroundColor: 'rgba(0, 128, 128, 0.1)',
              fill: true,
              tension: 0.2
            },
            {
              label: 'USD vs. CNY (Normalized)',
              data: cnyNormalized,
              borderColor: 'red',
              backgroundColor: 'rgba(255, 0, 0, 0.1)',
              fill: true,
              tension: 0.2
            },
            {
              label: 'USD vs. JPY (Normalized)',
              data: jpyNormalized,
              borderColor: 'gold',
              backgroundColor: 'rgba(255, 215, 0, 0.1)',
              fill: true,
              tension: 0.2
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { title: { display: true, text: "Date" } },
            y: { 
              title: { display: true, text: "Normalized Strength (%)" },
              ticks: { callback: value => `${value}%` }
            }
          }
        }
      });
    } catch (error) {
      console.error("Error fetching historical data:", error);
    }
  }
  
  async function fetchNews() {
    try {
      const response = await fetch("/news");
      const articles = await response.json();
      const newsDiv = document.getElementById("news");
      newsDiv.innerHTML = "";
      articles.forEach(article => {
        const articleDiv = document.createElement("div");
        articleDiv.className = "news-article";
        articleDiv.innerHTML = `
          <h3><a href="${article.url}" target="_blank">${article.title}</a></h3>
          <p>${article.description || ""}</p>
        `;
        newsDiv.appendChild(articleDiv);
      });
    } catch (error) {
      console.error("Error fetching news:", error);
    }
  }
  
  async function fetchAnalysis() {
    try {
      const response = await fetch("/analysis");
      const data = await response.json();
      const analysisDiv = document.getElementById("analysis");
      if (data.error) {
        analysisDiv.innerHTML = `<p>${data.error}</p>`;
        return;
      }
      let html = "";
      for (const metric in data) {
        const stats = data[metric];
        html += `
          <div class="analysis-block">
            <h3>${metric}</h3>
            <p><strong>First Value:</strong> ${stats.first}</p>
            <p><strong>Latest Value:</strong> ${stats.latest}</p>
            <p><strong>Highest Value:</strong> ${stats.highest}</p>
            <p><strong>Lowest Value:</strong> ${stats.lowest}</p>
            <p><strong>Percent Change:</strong> ${stats.percent_change}%</p>
            <p><strong>Trend:</strong> ${stats.trend}</p>
          </div>
        `;
      }
      analysisDiv.innerHTML = html;
    } catch (error) {
      console.error("Error fetching analysis:", error);
    }
  }
  
  //////////////////////////////////
  // Time Range Selector Setup
  //////////////////////////////////
  function setupTimeRangeSelector() {
    const rangeSelect = document.getElementById("timeRangeSelect");
    rangeSelect.addEventListener("change", () => {
      loadHistoricalData();
      fetchAnalysis();
    });
  }
  
  //////////////////////////////////
  // Dark Mode Toggle Setup
  //////////////////////////////////
  function setupModeToggle() {
    const modeToggle = document.getElementById("modeToggle");
    const modeLabel = document.getElementById("modeLabel");
    modeToggle.addEventListener("change", () => {
      document.body.classList.toggle("dark-mode", modeToggle.checked);
      modeLabel.textContent = modeToggle.checked ? "Only Dark Mode" : "No Light Mode";
    });
  }
  
  //////////////////////////////////
  // Background Music Setup
  //////////////////////////////////
  function setupBackgroundMusic() {
    const bgMusic = document.getElementById("bgMusic");
    if (!bgMusic) return;
    bgMusic.volume = 0.2; // Set volume to 20%
    const playMusic = () => {
      bgMusic.play().catch(err => console.error("Music play error:", err));
      document.removeEventListener("click", playMusic);
    };
    document.addEventListener("click", playMusic);
  }
  