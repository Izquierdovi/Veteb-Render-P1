from flask import Flask, request, send_file, render_template, jsonify
import os
from werkzeug.utils import secure_filename
from logica import split_text_into_chunks, embedded_chunks, extract_requeriments, search_content, evaluar_bloques
from pathlib import Path
import time

#New



app = Flask(__name__, template_folder= 'frontend/templates', static_folder= 'frontend/static')



UPLOAD_FOLDER = Path(__file__).parent / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True, parents=True)
print(f"✔ Carpeta 'uploads' creada en: {UPLOAD_FOLDER.resolve()}")


@app.route('/')
def index():
    return render_template('index2.html')


@app.route('/test-style')
def test_style():
    return '<link rel="stylesheet" href="/static/style2.css">'


@app.route('/upload', methods = ['POST'])
def upload():
    data_sheet = request.files.get('data_sheet')
    requeriments = request.files.get('requeriments')

    if not data_sheet or not requeriments:
        return jsonify({'success': False, 'message': 'Faltan archivos'}), 400
    
    print('Datasheet recibido:', data_sheet.filename)
    print('Tipo MIME del Datasheet:', data_sheet.mimetype)
    
    print('Excel recibido: ', requeriments.filename)
    print('Tipo MIME del Excel:', requeriments.mimetype)

    excel_path = UPLOAD_FOLDER / secure_filename(requeriments.filename)
    pdf_path = UPLOAD_FOLDER / secure_filename(data_sheet.filename)

    print(f'Ruta del PDF: {pdf_path}')
    print('\n' * 2)
    if os.path.exists(pdf_path):
        print("El archivo PDF se encontró y está disponible.")
    else:
        print(f"No se pudo encontrar el archivo: {pdf_path}")

    data_sheet.save(str(pdf_path))
    requeriments.save(str(excel_path))

    print('\n')
    print(f'PDF guardado en {pdf_path}')
    print(f'Tamaño {os.path.getsize(pdf_path)}')

    try:
        chunks = split_text_into_chunks(str(pdf_path))
        df = embedded_chunks(chunks)
        querys = extract_requeriments(excel_path)
        df_to_api = search_content(df, querys)
        
        excel_buffer = evaluar_bloques(df_to_api, str(excel_path))


       
        return send_file(
            excel_buffer,
            mimetype= 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment= True,
            download_name= 'resultado_evaluacion.xlsx'
        ) 

    except Exception as e:
        print(f'Error interno en /upload: {str(e)}')
        return jsonify({'success' : False, 'message' : f'Error: {str(e)}'}), 500
    
    finally:
    # Eliminar solo los archivos subidos (PDF y Excel)
        for file_path in [pdf_path, excel_path]:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"🗑️ Archivo eliminado: {file_path}")
            except Exception as e:
                print(f"⚠️ Error eliminando {file_path}: {str(e)}")

    # No elimines output_path (se envía como respuesta)



#ACÁ SE CAMBIÓ EL DEBUG DE True a False
if __name__ == "__main__":
    app.run(debug = True)