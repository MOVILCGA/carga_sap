let chart = null;
let procesoActivo = null;
let subprocesoActivo = null;


// =========================
// 📊 GRAFICA POR PROCESO
// =========================
function cargarGrafica(proceso, sub_proceso = null) {

    let url = `/api/proceso_chart?proceso=${encodeURIComponent(proceso)}`;

    if (sub_proceso) {
        url += `&sub_proceso=${encodeURIComponent(sub_proceso)}`;
    }

    fetch(url)
        .then(res => {
            if (!res.ok) throw new Error("Error en la API");
            return res.json();
        })
        .then(data => renderGrafica(data, "graficaProceso"))
        .catch(err => {
            console.error(err);
            alert("Error cargando la gráfica");
        });
}


// =========================
// 🏭 GRAFICA POR PLANTA
// =========================
function cargarGraficaPorPlanta(centro) {

    fetch(`/api/planta_chart?centro=${encodeURIComponent(centro)}`)
        .then(res => {
            if (!res.ok) throw new Error("Error en la API");
            return res.json();
        })
        .then(data => renderGrafica(data, "graficaProceso"))
        .catch(err => {
            console.error(err);
            alert("Error cargando gráfica por planta");
        });
}


// =========================
// 🎨 RENDER GRAFICA
// =========================
function renderGrafica(data, canvasId) {

    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (chart) chart.destroy();

    chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: data.datasets
        },
        options: {
            responsive: true,

            plugins: {
                legend: {
                    position: 'right'
                },

                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw + ' horas';
                        }
                    }
                }
            },

            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return Math.round(value);
                        }
                    },
                    title: {
                        display: true,
                        text: 'Horas'
                    }
                }
            }
        }
    });
}


// =========================
// 🔥 CARGAR SUBPROCESOS
// =========================
function cargarSubprocesos(proceso) {

    procesoActivo = proceso;
    subprocesoActivo = null;

    const container = document.getElementById("subprocesos-container");

    container.innerHTML = "<p class='text-muted'>Cargando subprocesos...</p>";

    // 🔥 PRIMERO: cargar TODO el proceso (SIN filtro)
    cargarGrafica(proceso, null);

    fetch(`/api/subprocesos?proceso=${encodeURIComponent(proceso)}`)
        .then(res => res.json())
        .then(data => {

            container.innerHTML = "";

            if (data.length === 0) {
                container.innerHTML = "<p class='text-muted'>No hay subprocesos</p>";
                return;
            }

            data.forEach((sub) => {

                const btn = document.createElement("button");

                btn.className = "sub-btn";
                btn.innerText = sub;

                btn.onclick = () => seleccionarSubproceso(proceso, sub, btn);

                container.appendChild(btn);
            });

        })
        .catch(err => {
            console.error(err);
            container.innerHTML = "Error cargando subprocesos";
        });
}


// =========================
// 🔥 SELECCIONAR SUBPROCESO
// =========================
function seleccionarSubproceso(proceso, sub, boton) {

    subprocesoActivo = sub;

    document.querySelectorAll("#subprocesos-container .sub-btn").forEach(btn => {
        btn.classList.remove("active");
    });

    boton.classList.add("active");

    cargarGrafica(proceso, sub);
}