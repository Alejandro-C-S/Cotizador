// Función para seleccionar una fila y llenar los campos del formulario con sus valores
function seleccionarFila(id, tipo_perfil, material, precio) {
    document.getElementById('idProducto').value = id; 
    document.getElementById('taskPerfil').value = tipo_perfil;
    document.getElementById('taskMaterial').value = material;
    document.getElementById('taskPrecio').value = precio; 
}

// Seleccionar una fila de fabricación.html
function seleccionarFila2(id, tipo, precio) {
    document.getElementById('idFabricacion').value = id;
    document.getElementById('taskPerfil').value = tipo;
    document.getElementById('taskPrecio').value = precio;
}

// Espera a que el DOM esté completamente cargado antes de ejecutar el código
document.addEventListener("DOMContentLoaded", function () {
    const taskPerfilSelect = document.getElementById("taskPerfil"); 
    const nuevoPerfilInput = document.getElementById("nuevoPerfil"); 
    const agregarBtn = document.querySelector("button[value='agregar']"); 

    function toggleFields() {
        if (taskPerfilSelect.value) {
            nuevoPerfilInput.disabled = true; 
        } else {
            nuevoPerfilInput.disabled = false;
        }
    }

    // Función para deshabilitar el dropdown si hay texto en el input de nuevo perfil
    function disablePerfilSelection() {
        if (nuevoPerfilInput.value.trim()) {
            taskPerfilSelect.disabled = true; 
        } else {
            taskPerfilSelect.disabled = false; 
        }
    }

    taskPerfilSelect.addEventListener("change", toggleFields);
    nuevoPerfilInput.addEventListener("input", disablePerfilSelection);
});

// Función para mostrar el botón de eliminar perfil si hay un perfil seleccionado
function mostrarEliminarPerfil() {
    let perfilSeleccionado = document.getElementById("taskPerfil").value; 
    let btnEliminar = document.getElementById("btnEliminarPerfil");

    if (perfilSeleccionado) {
        btnEliminar.classList.remove("d-none");
    } else {
        btnEliminar.classList.add("d-none"); 
    }
}

// Función para eliminar un perfil seleccionado
function eliminarPerfil() {
    let perfilSeleccionado = document.getElementById("taskPerfil").value;

    if (perfilSeleccionado) {
        if (confirm(`¿Seguro que deseas eliminar el perfil "${perfilSeleccionado}"?`)) {
            fetch(`/eliminar_perfil/${perfilSeleccionado}`, { method: "DELETE" }) 
                .then(response => response.json())
                .then(data => {
                    alert(data.mensaje); 
                    location.reload();
                })
                .catch(error => console.error("Error al eliminar:", error)); 
        }
    }
}

//Mensajes por tiempo
document.addEventListener("DOMContentLoaded", function () {
    // Selecciona los mensajes de éxito y error
    let mensajeExito = document.querySelector(".alert-success");
    let mensajeError = document.querySelector(".alert-danger");

    // Función para ocultar el mensaje después de 5 segundos
    function ocultarMensaje(mensaje) {
        if (mensaje) {
            setTimeout(() => {
                mensaje.style.display = "none";
            }, 3000);
        }
    }
    // Ejecuta la función para ambos mensajes
    ocultarMensaje(mensajeExito);
    ocultarMensaje(mensajeError);
});

