import os
import pandas as pd

def analyze_and_fix_csv_files(folder_path):
    # Lista para almacenar los errores encontrados
    errors = []
    total_questions = 0

    # Iterar sobre todos los archivos en la carpeta
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".csv"):  # Verificar que sea un archivo CSV
            file_path = os.path.join(folder_path, file_name)
            try:
                # Renombrar el archivo al formato correcto
                if file_name.startswith("category_"):
                    # Extraer el nombre de la categoría del archivo
                    category_name = file_name.replace("category_", "").replace(".csv", "")
                    # Reemplazar guiones por espacios y convertir a formato título
                    new_file_name = category_name.replace("-", " ").title() + ".csv"
                    new_file_path = os.path.join(folder_path, new_file_name)

                    # Renombrar el archivo si el nombre es diferente
                    if file_path != new_file_path:
                        os.rename(file_path, new_file_path)
                        print(f"Renamed file: {file_name} -> {new_file_name}")
                        file_path = new_file_path  # Actualizar la ruta del archivo

                # Leer el archivo CSV
                df = pd.read_csv(file_path)
                original_length = len(df)
                rows_to_remove = []

                # Iterar sobre cada fila del archivo
                for index, row in df.iterrows():
                    total_questions += 1
                    question = row['Questions']
                    correct_answer = row['Correct']
                    options = [row['A'], row['B'], row['C'], row['D']]

                    # Verificar si la respuesta correcta no está en las opciones
                    if correct_answer not in options:
                        errors.append({
                            "file": file_name,
                            "row": index,
                            "error": "Correct answer not in options",
                            "question": question,
                            "correct_answer": correct_answer,
                            "options": options
                        })
                        rows_to_remove.append(index)

                    # Verificar si hay opciones repetidas (ignorando valores nulos)
                    non_null_options = [opt for opt in options if pd.notnull(opt)]
                    if len(non_null_options) != len(set(non_null_options)):
                        errors.append({
                            "file": file_name,
                            "row": index,
                            "error": "Duplicate options found",
                            "question": question,
                            "options": options
                        })
                        rows_to_remove.append(index)

                # Eliminar las filas defectuosas
                df_cleaned = df.drop(index=rows_to_remove)

                # Sobrescribir el archivo original con las preguntas válidas
                df_cleaned.to_csv(file_path, index=False)
                print(f"Processed file: {file_name} | Original rows: {original_length} | Cleaned rows: {len(df_cleaned)}")

            except Exception as e:
                errors.append({
                    "file": file_name,
                    "row": "N/A",
                    "error": f"Failed to process file: {e}"
                })

    # Reportar los errores encontrados
    print(f"Total questions analyzed: {total_questions}")
    if errors:
        print(f"Errors found {len(errors)}:")
        for error in errors:
            print(f"File: {error['file']}, Row: {error['row']}, Error: {error['error']}")
            print(f"Question: {error.get('question', 'N/A')}")
            print(f"Correct Answer: {error.get('correct_answer', 'N/A')}")
            print(f"Options: {error.get('options', 'N/A')}")
            print("-" * 50)
    else:
        print("No errors found in the CSV files.")

# Ruta de la carpeta que contiene los archivos CSV
folder_path = "OpenTriviaQAKaggle"

# Llamar a la función para analizar y corregir los archivos
analyze_and_fix_csv_files(folder_path)