let chart = null;
let procesoActivo = null;
let subprocesoActivo = null;


// =========================
// 📊 CARGAR GRÁFICA
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
        .then(data => {

            const ctx = document.getElementById("graficaProceso");
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

                        // 🔥 TOOLTIP CON HORAS
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
                            title: {
                                display: true,
                                text: 'Horas'
                            }
                        }
                    }
                }
            });

        })
        .catch(err => {
            console.error(err);
            alert("Error cargando la gráfica");
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

    fetch(`/api/subprocesos?proceso=${encodeURIComponent(proceso)}`)
        .then(res => res.json())
        .then(data => {

            container.innerHTML = "";

            if (data.length === 0) {
                container.innerHTML = "<p class='text-muted'>No hay subprocesos</p>";
                return;
            }

            data.forEach((sub, index) => {

                const btn = document.createElement("button");

                // 🔥 ESTILO TIPO CHIP
                btn.className = "sub-btn";
                btn.innerText = sub;

                btn.onclick = () => seleccionarSubproceso(proceso, sub, btn);

                container.appendChild(btn);

                // 🔥 AUTO-SELECCIONAR EL PRIMERO
                if (index === 0) {
                    seleccionarSubproceso(proceso, sub, btn);
                }

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

    // 🔥 quitar selección anterior
    document.querySelectorAll("#subprocesos-container .sub-btn").forEach(btn => {
        btn.classList.remove("active");
    });

    // 🔥 marcar activo
    boton.classList.add("active");

    // 📊 cargar gráfica filtrada
    cargarGrafica(proceso, sub);
}