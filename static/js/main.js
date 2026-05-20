async function getECGDataStats() {
    try {
        const response = await fetch("http://127.0.0.1:5000/ecg-stats");
        const ecgPredObj = await response.json();
        
        return ecgPredObj;
    }
    catch(error) {
        console.log(error)
    }
} 

async function getECGData(start, end) {
    try {
        let url;
        if(!start && !end) {
            url = "/ecg-predictions-resample"
        }
        else {
            url = `/ecg-predictions-resample?start=${start}&end=${end}`;
        }
        // console.log("URL: ", url)
        const response = await fetch(url);
        const ecgData = await response.json();
        // console.log("Start datetime: ", start);
        // console.log("End datetime: ", end);
        // console.log(ecgData);
        return ecgData;
    }
    catch(error) {
        console.log(error)
    }
}

function renderPlot(data) {
    const t = data.map(data => data["Time"]);
    const y = data.map(data => Number(data["240507_complete:ECG"]));
    const p = data.map(data => data["Prediction"]);
    
    const shapes = buildShapes(data);
    
    Plotly.newPlot("chart", [{
        mode: "line",
        x: t,
        y: y,
        line: {color: "light-blue", width: 1}
    }], {
        xaxis: { autorange: true },
        yaxis: { autorange: true },
        margin: {t: 20, r: 20, b: 40, l: 50},
        shapes: shapes
        }, {
        scrollZoom: true
    });
}

function updatePlot(data) {
    const t = data.map(data => data["Time"]);
    const y = data.map(data => Number(data["240507_complete:ECG"]));
    const p = data.map(data => data["Prediction"]);
    // console.log("Start after update: ", t[0]);
    // console.log("End after update: ", t[t.length - 1]);
    
    const shapes = buildShapes(data);

    Plotly.update("chart", {
        x: [t],
        y: [y],
    }, {
        xaxis: { autorange: true },
        yaxis: { autorange: true },
        shapes: shapes
    });
}

function buildShapes(data) {
    let arrythmiaStart = null;
    let arrythmiaEnd = null;
    let shapes = [];

    /*
        Sinus   red
        IVR     green
        Noise   blue
        Other   orange
        PVCs    purple
    */
    const colors = {
        "Sinus": "rgba(230, 25, 75, 0)",     
        "IVR": "rgba(60, 180, 75, 0.50)",      
        "Noise": "rgba(0, 130, 200, 0.50)",   
        "Other": "rgba(245, 130, 48, 0.50)",    
        "PVCs": "rgba(145, 30, 180, 0.50)"      
    };

    for(let i = 0; i < data.length; i++) {
        let prediction = data[i]["Prediction"];
        let time = data[i]["Time"];
        
        if(prediction !== "Sinus") {
            if(arrythmiaStart === null) {
                arrythmiaStart = time;
            }

            const nextPrediction = (i + 1 < data.length) ? data[i + 1]["Prediction"] : null;
            
            if(prediction !== nextPrediction) {
                arrythmiaEnd = time;

                shapes.push({
                    type: "rect",
                    xref: "x",
                    yref: "paper",
                    x0: arrythmiaStart,
                    x1: arrythmiaEnd,
                    y0: 0,
                    y1: 1,
                    fillcolor: colors[data[i]["Prediction"]] || "rgba(200,200,200,0.25)",
                    opacity: 0.7,
                    line: {width: 0},
                    layer: "below",
                    /*label: {
                        text: prediction,
                        font: { size: 10, color: 'black' },
                        textposition: 'top center',
                    }*/
                });

                arrythmiaStart = null;
                arrythmiaEnd = null;
            }
        }
        else {
            continue;
        }
    }

    return shapes;
}

function listArythmia(data) {
    let arrythmiaStart = null;
    let arrythmiaEnd = null;
    arythmiaList = [];

    const listArythmia = document.getElementById("list-arythmia");
    listArythmia.innerHTML = "";
    
    for(let i = 0; i < data.length; i++) {
        let prediction = data[i]["Prediction"];
        let time = data[i]["Time"];
        
        if(prediction !== "Sinus") {
            if(arrythmiaStart === null) {
                arrythmiaStart = time;
            }

            const nextPrediction = (i + 1 < data.length) ? data[i + 1]["Prediction"] : null;
            
            if(prediction !== nextPrediction) {
                arrythmiaEnd = time;

                const article = document.createElement("article");
                article.innerHTML = `
                    <div class="entry-header">
                    <h2 class="entry-title">${prediction}</h2>
                    <span class="entry-range">${new Date(arrythmiaStart).toJSON()} - ${new Date(arrythmiaEnd).toJSON()}</span>
                    <button onClick="viewArythmia('${encodeURIComponent(arrythmiaStart)}', '${encodeURIComponent(arrythmiaEnd)}')">View</button>
                    </div>
                `;
                listArythmia.appendChild(article);
                arythmiaList.push({
                    "Prediction": prediction,
                    "Start": arrythmiaStart,
                    "End": arrythmiaEnd
                });
                arrythmiaStart = null;
                arrythmiaEnd = null;
            }
        }
        else {
            continue;
        }
    }
}

async function viewArythmia(start, end) {
    start = decodeURIComponent(start);
    end = decodeURIComponent(end);
    
    const viewData = await getECGData(start, end);

    updatePlot(viewData);
}

function statsArythmia(data) {
    const t = data.map(data => data["Time"]);
    const y = data.map(data => Number(data["240507_complete:ECG"]));
    const p = data.map(data => data["Prediction"]);

    const statsArythmia = document.getElementById("stats-arythmia");

    let sinusCount = 0;
    let ivrCount = 0;
    let pvcCount = 0;
    let otherCount = 0;
    let noiseCount = 0; 

    let start = null;
    for(i = 0; i < data.length; i++) {
        if(i === 0 || p[i] !== p[i - 1]) {
            start = t[i];
        }

        if(i === data.length || p[i] !== p[i + 1]) {
            let end = t[i];
            
            if(p[i] === "Sinus") {
                sinusCount++;
            }
            
            if(p[i] === "IVR") {
                ivrCount++;
            }
            
            if(p[i] === "PVCs") {
                pvcCount++;
            }

            if(p[i] === "Other") {
                otherCount++;
            }

            if(p[i] === "Noise") {
                noiseCount++;
            }
        }
    }

    const div = document.createElement("div");
    div.innerHTML = `
        <div>
            <h2>Number of arythmia</h2>
            <ul>
                <li>Sinus: ${sinusCount}</li>
                <li>IVR: ${ivrCount}</li>
                <li>PVCs: ${pvcCount}</li>
                <li>Other: ${otherCount}</li>
                <li>Noise: ${noiseCount}</li>
            </ul>
        </div>
    `;
    statsArythmia.appendChild(div);
}

function colourArythmia(ecgStats) {
    const colourArythmia = document.getElementById("colour-arythmia");
    colourArythmia.innerHTML = `
        <div class="entry-header">
            <h3 class="entry-title">Arythmia type and number of episodes</h3>
        </div>
        <ul class="arythmia-list">
            <li><span class="label"><span class="dot none"></span>Sinus</span> ${ecgStats["Sinus"]}</li>
            <li><span class="label"><span class="dot green"></span>IVR</span> ${ecgStats["IVR"]}</li>
            <li><span class="label"><span class="dot blue"></span>Noise</span> ${ecgStats["Noise"]}</li>
            <li><span class="label"><span class="dot orange"></span>Other</span> ${ecgStats["Other"]}</li>
            <li><span class="label"><span class="dot purple"></span>PVCs</span> ${ecgStats["PVCs"]}</li>
        </ul>
    `;
}

function listArythmiaGroup(data) {
    const listArythmia = document.getElementById("list-arythmia");
    listArythmia.innerHTML = "";
    for(i = 0; i < data.length; i++) {
        const article = document.createElement("article");
        article.innerHTML = `
            <div class="entry-header">
                <h2 class="entry-title">${data[i]["Prediction"]}</h2>
                <span class="entry-range">${data[i]["Start"]} - ${data[i]["End"]}</span>
                <button onClick="viewArythmia('${encodeURIComponent(data[i]["Start"])}', '${encodeURIComponent(data[i]["End"])}')">View</button>
            </div>
        `;
        listArythmia.appendChild(article);
    }
}

function searchArythmiaList() {
    const searchArythmia = document.getElementById("search-arythmia");
    const filter = searchArythmia.value.toLowerCase();
    const listArythmiaElement = document.getElementById("list-arythmia");
    let filteredList = [];

    filteredList = arythmiaList.filter(data => 
        data["Prediction"].toLowerCase().includes(filter)
    );

    // console.log("Filtered:", filteredList.map(currentData => currentData["Prediction"]));
    // console.log("Filtered:", filteredList);

    if(filteredList.length === 0) {
        listArythmiaElement.innerHTML = `
            <div>${filter} is not present.</div>
        `;

        return;
    }

    listArythmiaGroup(filteredList);
}

let currentData = [];
let arythmiaList = [];
async function main() {
    const initialStart = performance.now();
    
    const ecgPredData = await getECGData();
    const ecgStats = await getECGDataStats();
    
    if(typeof WebGLWorker === "undefined") {
        console.log("WebGL not supported")
    }

    document.getElementById("search-arythmia").addEventListener("input", searchArythmiaList);
    
    renderPlot(ecgPredData);
    listArythmia(ecgPredData);
    colourArythmia(ecgStats);
    currentData = ecgPredData;
    searchArythmiaList();

    const initalEnd = performance.now();
    console.log(`Initial load took ${initalEnd - initialStart} miliseconds.`);

    let zoomTimer = null;
    let loading = false;
    document.getElementById("chart").on("plotly_relayout", (eventData) => {
        const reloadStart = performance.now();
        // Only react to x-axis zoom events
        const start = eventData["xaxis.range[0]"];
        const end = eventData["xaxis.range[1]"];
        // console.log("Start relayout: ", start);
        // console.log("End relayout: ", end);
        console.log(`${start} ${end}`);
        if (!start || !end) return;
        clearTimeout(zoomTimer);
    
        zoomTimer = setTimeout(async () => {
            if (loading) return;
            loading = true;
            
            const data = await getECGData(
                start,
                end
            );

            currentData = data;
            
            updatePlot(currentData);
            listArythmia(currentData);
            searchArythmiaList();

            loading = false;

            const reloadEnd = performance.now();
            // console.log(`Reload took ${reloadEnd - reloadStart} miliseconds.`);
        }, 300); // debounce delay
    });
}
main();