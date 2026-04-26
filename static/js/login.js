// 👁️ Mostrar / ocultar contraseña
function togglePassword() {
    const input = document.getElementById("password");
    input.type = input.type === "password" ? "text" : "password";
}

// ⏳ Loading en botón
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");

    form.addEventListener("submit", () => {
        document.getElementById("btnText").classList.add("d-none");
        document.getElementById("loading").classList.remove("d-none");
    });
});