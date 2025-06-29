import pandas as pd
import pymupdf4llm
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import pdfplumber
import time
import google.generativeai as genai
import re
import ast
import os
from io import BytesIO

#Extraccion texto del pdf


def clean_text(text, *args):
    for change in args:
        text = text.replace(change, '')
        
        return text


def extract_text(path):
    try:
        with open(path, 'rb') as file:
            md_text = pymupdf4llm.to_markdown(path, ignore_images= True, ignore_graphics= True, force_text=True)
            text = '\n'.join(line for line in md_text.split('\n') if line.strip())
            text = clean_text(text, "#", "*")

            return text
    except Exception as e:
        print(f'Error al procesar el PDF: {e}')
        return None



#Extracción del texto página por página


def text_per_page(path):
    pdf = pdfplumber.open(path)

    dct_pages = {}

    for i in enumerate(pdf.pages):
        dct_pages.update({f'page_{i+1}' : pymupdf4llm.to_markdown(path, pages = [i])})
    
    return dct_pages


#Dividir el texto en chunks


def split_text_into_chunks(path, chunk_size = 100, chunk_overlap = 10):
    print('Vamos a extraer el texto...')
    text = extract_text(path)
    print('\n texto extraído')

    if text:
        print('Dividiendo el texto en chunks...')
        text_splitter = RecursiveCharacterTextSplitter(chunk_size = chunk_size, chunk_overlap = chunk_overlap)

        
        chunks = text_splitter.split_text(text)

        print('Texto divido en chunks correctamente!')
        return chunks
    
    else:
        print('No se pudo procesar el PDF')


#Crear embenddings de los chunksS
_model = None

def get_model():
    
    global _model

    if _model is None:
        print("Cargando modelo...")
        
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    
    return _model

def embedded_chunks(chunks:list = None ):
    model = get_model()
    if chunks:
        
        embenddings = model.encode(chunks, convert_to_numpy= True)

        
        #Creamos un dataframe de los chunks y los embenddings
        df = pd.DataFrame({
            'chunk' : chunks,
            'embendding' : embenddings.tolist()
        })
        print("Chunks procesados correctamente")
        
    else:
        print("No se encontraron chunks para procesar")
    
    return df



#Similitud de cosenos


def search_content(df: pd.DataFrame, querys:list = []) -> pd.DataFrame:
  
  model = get_model()
  dct = {}
  count = 0
  for item in querys:
      count += 1

      emb_query = model.encode(item, convert_to_numpy = True)

      temp_df = df.copy()
      temp_df['similarity'] = temp_df['embendding'].apply(lambda x: cosine_similarity([emb_query], [x])[0][0])

      temp_df.sort_values(by = 'similarity', ascending = False, inplace = True)
      temp_df.reset_index(drop = True, inplace = True)
      top_chunks= temp_df.iloc[:5]['chunk'].to_list()
      

      dct[f'{count}. ' + item] = top_chunks

  return dct



################## EXTRAER INFORMACIÓN DEL EXCEL ##################

def extract_requeriments(excel_path):
    req = pd.read_excel(excel_path)
    specifications = req['Especificaciones técnicas mínimas viabilizadadas'].to_list()

    return specifications


def output(path:str, list_output:list):
    df = pd.read_excel(path)
    i = 0

    for dic in list_output:

        for cumple, motivo in dic.items():

            df.iloc[:, 2] = df.iloc[:, 2]
            df.iloc[:, 4] = df.iloc[:, 4]
            
            df.iloc[i, 2] = cumple
            df.iloc[i, 4] = motivo
        
        i+=1
    
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    
    
    return excel_buffer

################## MODELO DE GOOGLE ##################
# Configuración de la API
genai.configure(api_key="AIzaSyCrg4rqN__GDI6c8YWmxhLIqKLBOtTke2c")

instrucciones = (
    "Eres un agente virtual que evalúa si un requisito técnico se cumple o no según una lista de evidencias. "
    "Para cada requisito (clave del diccionario), analiza si alguna de las evidencias (valores de la lista) lo cumple. Deberas analizar el requisito, evaluar entre rangos, evaluar si se cumple mínimamente con lo que se piden e incluso evaluar entre rangos o evaluar si una tecnología es superior a otra, tambien podrás realizar conversiones numéricas en caso de que te pidan en una unidad y las evidencias estén en otras. Tambien manejaras sinónimos de las palabras, es decir, si te dicen recien nacidos tambien entenderás que es neonato y así con cuantos ejemplos aplique"
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

def evaluar_bloques(df_to_api, excel_path):
    bloques = dividir_diccionario(df_to_api, tamano_bloque= 25)
    respuestas_dict = {}

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
    

    return output(excel_path, respuestas_dict.values())
