document.addEventListener("DOMContentLoaded", () => {

    const accion = document.getElementById("accion");
    const crearDiv = document.getElementById("crearDiv");
    const agregarDiv = document.getElementById("agregarDiv");
    const btnPreview = document.getElementById("btnPreview");
    const form = document.getElementById("formExcel");

    accion.addEventListener("change", () => {
        crearDiv.classList.add("d-none");
        agregarDiv.classList.add("d-none");

        if (accion.value === "crear") {
            crearDiv.classList.remove("d-none");
        } else if (accion.value === "agregar") {
            agregarDiv.classList.remove("d-none");
        }
    });

    btnPreview.addEventListener("click", () => {
        if (!validarFormulario()) return;

        form.action = "/preview";
        document.getElementById("loader").classList.remove("d-none");
        form.submit();
    });

});


function mostrarAlerta(msg, tipo = "danger") {
    let alerta = document.getElementById("alerta");
    alerta.className = `alert alert-${tipo}`;
    alerta.innerText = msg;
    alerta.classList.remove("d-none");
}


function validarFormulario() {
    let accion = document.getElementById("accion").value;
    let archivo = document.querySelector('input[name="file"]').value;

    if (!archivo) {
        mostrarAlerta("Selecciona un archivo primero");
        return false;
    }

    if (!accion) {
        mostrarAlerta("Selecciona una acción");
        return false;
    }

    if (accion === "crear") {
        let tabla = document.getElementById("tabla_crear").value;
        if (!tabla) {
            mostrarAlerta("Escribe el nombre de la tabla");
            return false;
        }
    }

    if (accion === "agregar") {
        let tabla = document.getElementById("tabla_existente").value;
        if (!tabla) {
            mostrarAlerta("Selecciona una tabla");
            return false;
        }
    }

    return true;
}