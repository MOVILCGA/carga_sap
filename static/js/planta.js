let chart = null;

function cargarGraficaPlanta(centro) {

    let url = `/api/planta_chart?centro=${encodeURIComponent(centro)}`;

    fetch(url)
        .then(res => res.json())
        .then(data => {

            const ctx = document.getElementById("graficaProceso");

            if (chart) chart.destroy();

            chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,   // 🔥 PROCESOS
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
                            title: {
                                display: true,
                                text: 'Horas'
                            }
                        }
                    }
                }
            });

        });
}