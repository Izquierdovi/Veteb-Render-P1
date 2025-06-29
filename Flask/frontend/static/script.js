let archivoDataSheet = null;
let archivoRequerimientos = null;

document.getElementById('uploadDatasheet').addEventListener('click', () => {
    document.getElementById("fileInput").click();
})


document.getElementById('uploadRequeriments').addEventListener('click', () => {
    document.getElementById("requerimentInput").click();
})


//Capturar el archivo seleccionado para datasheet

document.getElementById('fileInput').addEventListener('change', (event)=>{
    archivoDataSheet = event.target.files[0];
    event.preventDefault();
    

    const fileNameSpan = document.getElementById('fileNameDS');


    if (archivoDataSheet){
        fileNameSpan.textContent = archivoDataSheet.name;
        console.log('Archivo FT:', archivoDataSheet);
        Swal.fire({
            title: 'Cargado',
            text : `Se ha cargado el archivo: ${archivoDataSheet.name}`,
            icon : "success",
            confirmButtonText : 'Listo!'
        })
    }
});

//Capturar el archivo seleccionado para requrimientos

document.getElementById('requerimentInput').addEventListener('change', (event) =>{
    archivoRequerimientos = event.target.files[0];
    event.preventDefault()
    

    const fileNameSpanR = document.getElementById('fileNameRequeriments');

    if (archivoRequerimientos){
        fileNameSpanR.textContent = archivoRequerimientos.name;
        console.log('Archivo de requerimientos:', archivoRequerimientos);
        Swal.fire({
            title: 'Cargado',
            text : `Se ha cargado el archivo: ${archivoRequerimientos.name}`,
            icon : "success",
            confirmButtonText : 'Listo!'
        })
    }
});


//Configurar boton de envio de datos

const uploadButton = document.getElementById('sendFilesBtn');


uploadButton.addEventListener('click', async() =>{

    //creamos un objeto FormData para enviar los archivos
    const formData = new FormData();
    
    //Agregar los archivos seleccionados en los otros 2 btns al FormData
    if (archivoDataSheet){
        formData.append('data_sheet', archivoDataSheet);
    }
    if (archivoRequerimientos){
        formData.append('requeriments', archivoRequerimientos)
    }

    try{
        
        let timerInterval;
        Swal.fire({
        title: "Procesando...",
        html: "La descarga se realizará en breve, espere un momento...",
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
        }).then((result) => {
        /* Read more about handling dismissals below */
        if (result.dismiss === Swal.DismissReason.timer) {
            console.log("I was closed by the timer");
        }
        });



        //Enviar los archivos al backend usando fetch

        // Detectar si estamos en render o en local
    
        const backendUrl = window.location.hostname.includes('render.com')
            ? 'https://veteb-p2.onrender.com'
            : '';
        

        const response = await fetch(`${backendUrl}/upload`, {
            method : 'POST',
            body : formData
        });

        //Verificar la respuesta del servidor
        if (response.ok){
            
            const blob = await response.blob();

            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = 'resultado_veteb.xlsx';
            document.body.appendChild(a);
            a.click();

            setTimeout(() =>{
                document.body.removeChild(a);
                window.URL.revokeObjectURL(downloadUrl);
            },100);

            console.log('Descarga Iniciada')

        } else{
            const errorData = await response.json()
            throw new Error(errorData.message || 'Error al procesar los archivos');
        }
    }catch (error){
        console.error('Error en la solicitud', error)
        alert(`Error: ${error.message}`);
    }

});