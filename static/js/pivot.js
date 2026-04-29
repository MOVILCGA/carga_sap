// =========================
// 🔥 CARGAR RESUMEN
// =========================
function cargarResumen() {

    fetch("/api/resumen_subproceso")
    .then(res => res.json())
    .then(data => {

        const tbody = document.querySelector("#tablaPivot tbody");
        tbody.innerHTML = "";

        data.forEach(row => {

            let fila = `
                <tr class="fila-resumen" data-sub="${row.sub_proceso}">
                    <td style="cursor:pointer;">➕</td>
                    <td>${row.sub_proceso}</td>
                    <td>${Number(row.ABIE).toFixed(2)}</td>
                    <td>${Number(row.IMPR).toFixed(2)}</td>
                    <td>${Number(row.NOTP).toFixed(2)}</td>
                    <td><strong>${Number(row.TOTAL).toFixed(2)}</strong></td>
                </tr>

                <tr class="detalle" id="detalle-${row.sub_proceso}" style="display:none;">
                    <td colspan="6">
                        <div class="contenido-detalle"></div>
                    </td>
                </tr>
            `;

            tbody.innerHTML += fila;
        });

        activarExpandibles();
    });
}


// =========================
// 🔥 EXPANDIR DETALLE
// =========================
function activarExpandibles() {

    document.querySelectorAll(".fila-resumen").forEach(fila => {

        fila.onclick = function () {

            let sub = this.dataset.sub;
            let detalleRow = document.getElementById(`detalle-${sub}`);

            if (detalleRow.style.display === "none") {

                fetch(`/api/detalle_subproceso?sub_proceso=${encodeURIComponent(sub)}`)
                .then(res => res.json())
                .then(data => {

                    let html = `
                        <table class="table table-sm table-striped">
                        <thead>
                        <tr>
                            <th>Nombre</th>
                            <th>Pedido</th>
                            <th>Pos</th>
                            <th>Orden</th>
                            <th>ABIE</th>
                            <th>IMPR</th>
                            <th>NOTP</th>
                            <th>TOTAL</th>
                        </tr>
                        </thead>
                        <tbody>
                    `;

                    data.forEach(d => {
                        html += `
                            <tr>
                                <td>${d.Nombre || ''}</td>
                                <td>${d["Pedido de cliente"] || ''}</td>
                                <td>${d.PosPedClte || ''}</td>
                                <td>${d.Orden || ''}</td>
                                <td>${Number(d.ABIE).toFixed(2)}</td>
                                <td>${Number(d.IMPR).toFixed(2)}</td>
                                <td>${Number(d.NOTP).toFixed(2)}</td>
                                <td>${Number(d.TOTAL).toFixed(2)    }</td>
                            </tr>
                        `;
                    });

                    html += "</tbody></table>";

                    detalleRow.querySelector(".contenido-detalle").innerHTML = html;
                    detalleRow.style.display = "table-row";
                });

            } else {
                detalleRow.style.display = "none";
            }
        };
    });
}


// =========================
// 🚀 INIT
// =========================
document.addEventListener("DOMContentLoaded", function () {
    cargarResumen();
});