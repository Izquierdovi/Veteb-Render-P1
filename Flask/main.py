import google.generativeai as genai
from logica import *
import cProfile
import time
import re
import ast
import json

# Rutas
path = 'D:\\DIZQUIERDOV\\Desktop\\API DE GOOGLE\\ficha_tecnica.pdf'
excel_path = "D:\\DIZQUIERDOV\\Desktop\\API DE GOOGLE\\Formato.xlsx"

# Procesamiento inicial
chunks = split_text_into_chunks(path=path)
df = embedded_chunks(chunks=chunks)
querys = extract_requeriments(excel_path)
df_to_api = search_content(df, querys)

# Configuración de la API
genai.configure(api_key="AIzaSyCrg4rqN__GDI6c8YWmxhLIqKLBOtTke2c")

# Instrucciones al modelo
instrucciones = (
    "Eres un agente virtual que evalúa si un requisito técnico se cumple o no según una lista de evidencias. "
    "Para cada requisito (clave del diccionario), analiza si alguna de las evidencias (valores de la lista) lo cumple. Deberas analizar el requisito, evaluar entre rangos, evaluar si se cumple mínimamente con lo que se piden e incluso evaluar entre rangos o evaluar si una tecnología es superior a otra, . Ten en cuenta que los requisitos que vas a evaluar son requisitos que se deben cumplir MINIMAMENTE es decir, cualquier cosa que encuentres y que sea superior a lo que te piden cumpliría no te puedes ceñir a que debe cumplir tal cual como te lo piden, tambien podrás realizar conversiones numéricas en caso de que te pidan en una unidad y las evidencias estén en otras. Tambien manejaras sinónimos de las palabras, es decir, si te dicen recien nacidos tambien entenderás que es neonato y así con cuantos ejemplos aplique. Deberas hacer evaluaciones de tecnológia pues deberas evaluar si algo que te piden mínimamente si se cumple o no, porque te pueden pedir una tecnología inferior a la que se pide verificar entonces sabrás que si cumple"
    "Devuelve un diccionario de Python donde cada clave sea el requisito, y su valor sea un diccionario con UNA SOLA clave: 'Si' o 'No'. "
    "El valor de 'Si' o 'No' debe ser una explicación basada en el texto analizado. "
    "Ejemplo:\n"
    "{ 'El equipo debe tener pantalla de 8 pulgadas o más': { 'Si': 'El modelo X tiene una pantalla de 10 pulgadas, por lo tanto cumple.' } } "
    "\nNo agregues ningún texto antes ni después del diccionario."
)




model = genai.GenerativeModel("gemini-2.0-flash", system_instruction=instrucciones)

# Función para dividir en bloques
def dividir_diccionario(diccionario, tamano_bloque=25):
    claves = list(diccionario.keys())
    return [dict((k, diccionario[k]) for k in claves[i:i+tamano_bloque])
            for i in range(0, len(claves), tamano_bloque)]

# Evaluar por bloques
respuestas_dict = {}
bloques = dividir_diccionario(df_to_api, tamano_bloque=25)

for i, bloque in enumerate(bloques):
    bloque_texto = "\n\n".join(
        [f'"{key}": [\n' + "\n".join(f'- {v}' for v in value) + "\n]" for key, value in bloque.items()]
    )

    prompt = f"""
Analiza los siguientes requisitos con sus evidencias. Para cada uno, responde con un diccionario donde la clave sea el requisito y el valor sea otro diccionario con una sola clave 'Si' o 'No' y su explicación. Solo responde con el diccionario.

{{
{bloque_texto}
}}
    """

    response = model.generate_content(prompt)

    try:
        # Extraer el primer bloque tipo diccionario
        match = re.search(r"\{[\s\S]*\}", response.text)
        if match:
            dict_text = match.group(0)
            bloque_resultado = ast.literal_eval(dict_text)

            # Validación del formato
            if isinstance(bloque_resultado, dict):
                for req, val in bloque_resultado.items():
                    if isinstance(val, dict) and list(val.keys()) in [['Si'], ['No']]:
                        razon = val.get('Si') if 'Si' in val else val.get('No')
                        if isinstance(razon, str):
                            respuestas_dict[req] = val
        else:
            print(f"No se encontró diccionario válido en el bloque {i}")
            print("Texto completo:\n", response.text)

    except Exception as e:
        print(f"Error general en el bloque {i}:", e)
        print("Texto completo devuelto:\n", response.text)

    time.sleep(1)  # evitar sobrecarga

# Guardar los resultados en JSON
with open("respuestas_dict.json", "w", encoding="utf-8") as f:
    json.dump(respuestas_dict, f, ensure_ascii=False, indent=2)

# Mostrar resultados

print(output(excel_path, respuestas_dict.values()))
