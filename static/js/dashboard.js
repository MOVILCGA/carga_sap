// =========================
// ➕ AGREGAR FILTRO
// =========================
function addFilter() {

    const container = document.getElementById("filters-container");

    const div = document.createElement("div");
    div.className = "filter-row d-flex gap-2 mb-2";

    div.innerHTML = `
        <select name="column[]" class="form-select filter-select" onchange="cargarValores(this)">
            <option value="">Columna</option>
            ${getColumnOptions()}
        </select>

        <select name="search[]" class="form-select filter-input">
            <option value="">Selecciona valor</option>
        </select>

        <button type="button" class="btn btn-danger btn-sm" onclick="removeFilter(this)">
            ✖
        </button>
    `;

    container.appendChild(div);
}


// =========================
// ❌ ELIMINAR FILTRO
// =========================
function removeFilter(btn) {
    btn.parentElement.remove();
}


// =========================
// 🔥 CARGAR VALORES DINÁMICOS
// =========================
function cargarValores(selectColumna) {

    const fila = selectColumna.closest(".filter-row");
    const columna = selectColumna.value;

    const selectValor = fila.querySelector("select[name='search[]']");

    if (!columna) return;

    fetch(`/api/valores_columna?columna=${encodeURIComponent(columna)}`)
        .then(res => res.json())
        .then(data => {

            selectValor.innerHTML = '<option value="">Selecciona valor</option>';

            data.forEach(val => {
                const option = document.createElement("option");
                option.value = val;
                option.textContent = val;
                selectValor.appendChild(option);
            });

        })
        .catch(err => {
            console.error("Error cargando valores:", err);
        });
}


// =========================
// 📊 GRAFICA (ARREGLADA)
// =========================
let chart = null;

function cargarGrafica(proceso) {

    fetch(`/api/proceso_chart?proceso=${encodeURIComponent(proceso)}`)
        .then(res => res.json())
        .then(data => {

            const ctx = document.getElementById("graficaProceso");

            if (!ctx) return;

            if (chart) chart.destroy();

            chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Cantidad',
                        data: data.values
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: true
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });

        })
        .catch(err => {
            console.error(err);
            alert("Error cargando gráfica");
        });
}


// =========================
// 🔧 AYUDA: obtener columnas
// =========================
function getColumnOptions() {

    const select = document.querySelector(".filter-select");

    if (!select) return "";

    return [...select.options]
        .map(opt => `<option value="${opt.value}">${opt.text}</option>`)
        .join("");
}