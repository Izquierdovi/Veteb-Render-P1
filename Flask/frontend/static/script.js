let archivoDataSheet = null;
let archivoRequerimientos = null;

document.getElementById('uploadDatasheet').addEventListener('click', () => {
    document.getElementById("fileInput").click();
});

document.getElementById('uploadRequeriments').addEventListener('click', () => {
    document.getElementById("requerimentInput").click();
});

// Capturar el archivo seleccionado para datasheet
document.getElementById('fileInput').addEventListener('change', (event) => {
    archivoDataSheet = event.target.files[0];
    event.preventDefault();

    const fileNameSpan = document.getElementById('fileNameDS');

    if (archivoDataSheet) {
        fileNameSpan.textContent = archivoDataSheet.name;
        console.log('Archivo FT:', archivoDataSheet);
        Swal.fire({
            title: 'Cargado',
            text: `Se ha cargado el archivo: ${archivoDataSheet.name}`,
            icon: "success",
            confirmButtonText: 'Listo!'
        });
    }
});

// Capturar el archivo seleccionado para requerimientos
document.getElementById('requerimentInput').addEventListener('change', (event) => {
    archivoRequerimientos = event.target.files[0];
    event.preventDefault();

    const fileNameSpanR = document.getElementById('fileNameRequeriments');

    if (archivoRequerimientos) {
        fileNameSpanR.textContent = archivoRequerimientos.name;
        console.log('Archivo de requerimientos:', archivoRequerimientos);
        Swal.fire({
            title: 'Cargado',
            text: `Se ha cargado el archivo: ${archivoRequerimientos.name}`,
            icon: "success",
            confirmButtonText: 'Listo!'
        });
    }
});

// Configurar botón de envío de datos
const uploadButton = document.getElementById('sendFilesBtn');

uploadButton.addEventListener('click', async () => {
    const formData = new FormData();

    if (archivoDataSheet) {
        formData.append('data_sheet', archivoDataSheet);
    }
    if (archivoRequerimientos) {
        formData.append('requeriments', archivoRequerimientos);
    }

    try {
        let timerInterval;
        Swal.fire({
            title: "Procesando...",
            html: "La descarga se realizará en breve, espere un momento... <b></b>",
            timer: 4000,
            timerProgressBar: true,
            didOpen: () => {
                Swal.showLoading();
                const timer = Swal.getPopup().querySelector("b");
                timerInterval = setInterval(() => {
                    timer.textContent = `${Swal.getTimerLeft()}`;
                }, 100);
            },
            willClose: () => {
                clearInterval(timerInterval);
            }
        });

        const backendUrl = window.location.hostname.includes('render.com')
            ? 'https://veteb-p2.onrender.com'
            : '';

        const response = await fetch(`${backendUrl}/upload`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = 'resultado_veteb.xlsx';
            document.body.appendChild(a);
            a.click();

            setTimeout(() => {
                document.body.removeChild(a);
                window.URL.revokeObjectURL(downloadUrl);
            }, 100);

            console.log('✅ Descarga iniciada');
        } else {
            // Manejo de errores incluso si no es JSON
            let errorMessage = 'Error desconocido';
            const contentType = response.headers.get("content-type");

            if (contentType && contentType.includes("application/json")) {
                const errorData = await response.json();
                errorMessage = errorData.message || errorMessage;
            } else {
                errorMessage = await response.text();
            }

            throw new Error(errorMessage);
        }

    } catch (error) {
        console.error('❌ Error en la solicitud', error);
        Swal.fire({
            icon: 'error',
            title: 'Ocurrió un error',
            text: error.message
        });
    }
});
