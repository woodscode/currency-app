document.addEventListener("DOMContentLoaded", function() {
    // Initialize USD tracking components
    loadHistoricalData();
    fetchNews();
    fetchAnalysis();
    setupModeToggle();
    setupBackgroundMusic();
    setupTimeRangeSelector();
});

//////////////////////////////////
// USD Tracking Functions
//////////////////////////////////
function loadHistoricalData() {
    // Get selected time range from dropdown
    const rangeSelect = document.getElementById("timeRangeSelect");
    let range = rangeSelect.value; // "24h", "7d", or "30d"

    let endpoint = "/historical-data";
    if (range === "24h") {
        endpoint = "/historical-data/24h";
    } else if (range === "7d") {
        endpoint = "/historical-data/7d";
    } else if (range === "30d") {
        endpoint = "/historical-data";
    }

    fetch(endpoint)
        .then(response => response.json())
        .then(data => {
            if(data.error) {
                console.error("Historical data error:", data.error);
                return;
            }
            const labels = data.dates; // e.g., ["2025-01-15", "2025-01-16", ...]
            const cadData = data.cad;
            const mxnData = data.mxn;
            const cnyData = data.cny;
            const jpyData = data.jpy;

            // Chart 1: Actual Exchange Rates
            const ctxExchange = document.getElementById('currencyChart').getContext('2d');
            new Chart(ctxExchange, {
                type: 'line',
                data: {
                    labels: labels,
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

            // Compute normalized values based on the first value.
            const cadNormalized = cadData.map(val => parseFloat((val / cadData[0] * 100).toFixed(2)));
            const mxnNormalized = mxnData.map(val => parseFloat((val / mxnData[0] * 100).toFixed(2)));
            const cnyNormalized = cnyData.map(val => parseFloat((val / cnyData[0] * 100).toFixed(2)));
            const jpyNormalized = jpyData.map(val => parseFloat((val / jpyData[0] * 100).toFixed(2)));
            // Composite: average of normalized values for all four currencies.
            const composite = labels.map((_, idx) => parseFloat(((cadNormalized[idx] + mxnNormalized[idx] + cnyNormalized[idx] + jpyNormalized[idx]) / 4).toFixed(2)));

            // Chart 2: USD Strength Index (Composite)
            const ctxStrength = document.getElementById('strengthChart').getContext('2d');
            new Chart(ctxStrength, {
                type: 'line',
                data: {
                    labels: labels,
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
                            ticks: { callback: value => value + '%' }
                        }
                    }
                }
            });

            // Chart 3: Normalized Currency Strength (Separate Lines)
            const ctxNormalized = document.getElementById('normalizedChart').getContext('2d');
            new Chart(ctxNormalized, {
                type: 'line',
                data: {
                    labels: labels,
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
                            ticks: { callback: value => value + '%' }
                        }
                    }
                }
            });
        })
        .catch(error => console.error("Error fetching historical data:", error));
}

function fetchNews() {
    fetch("/news")
        .then(response => response.json())
        .then(articles => {
            const newsDiv = document.getElementById("news");
            newsDiv.innerHTML = "";
            articles.forEach(article => {
                const articleDiv = document.createElement("div");
                articleDiv.classList.add("news-article");
                articleDiv.innerHTML = `
                    <h3><a href="${article.url}" target="_blank">${article.title}</a></h3>
                    <p>${article.description ? article.description : ""}</p>
                `;
                newsDiv.appendChild(articleDiv);
            });
        })
        .catch(error => console.error("Error fetching news:", error));
}

function fetchAnalysis() {
    fetch("/analysis")
        .then(response => response.json())
        .then(data => {
            const analysisDiv = document.getElementById("analysis");
            if(data.error) {
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
        })
        .catch(error => console.error("Error fetching analysis:", error));
}

//////////////////////////////////
// Time Range Selector Setup
//////////////////////////////////
function setupTimeRangeSelector() {
    const rangeSelect = document.getElementById("timeRangeSelect");
    rangeSelect.addEventListener("change", function() {
        loadHistoricalData();
        fetchAnalysis();
    });
}

//////////////////////////////////
// Background Music Setup
//////////////////////////////////
function setupBackgroundMusic() {
    const bgMusic = document.getElementById("bgMusic");
    bgMusic.volume = 0.2; // Set volume to 20%
    // Play music on first user interaction
    function playMusic() {
        bgMusic.play().catch(err => console.error("Music play error:", err));
        document.removeEventListener("click", playMusic);
    }
    document.addEventListener("click", playMusic);
}

//////////////////////////////////
// Dark Mode Toggle
//////////////////////////////////
function setupModeToggle() {
    const modeToggle = document.getElementById("modeToggle");
    const modeLabel = document.getElementById("modeLabel");
    modeToggle.addEventListener("change", function() {
        if (modeToggle.checked) {
            document.body.classList.add("dark-mode");
            modeLabel.textContent = "Dark Mode";
        } else {
            document.body.classList.remove("dark-mode");
            modeLabel.textContent = "Light Mode";
        }
    });
}
