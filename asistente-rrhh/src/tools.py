import json
from pathlib import Path
from langchain_core.tools import tool

# Obtener la ruta del directorio actual donde se encuentra este archivo (tools.py)
# Esto asegura que la ruta al JSON sea siempre correcta, sin importar desde dónde se ejecute el script.
_CURRENT_DIR = Path(__file__).parent

@tool
def calcular_vacaciones(id_empleado: str) -> str:
    """
    Calcula y devuelve los días de vacaciones restantes para un empleado específico.
    
    Esta función es útil cuando un usuario pregunta sobre sus días de vacaciones disponibles
    o cuántos días le quedan.

    Args:
        id_empleado: El identificador único del empleado (ej. 'E001', 'E002').
    
    Returns:
        Un string con la información de las vacaciones restantes del empleado
        o un mensaje de error si el empleado no se encuentra.
    """
    # Construir la ruta completa al archivo de datos de empleados
    file_path = _CURRENT_DIR / "data" / "empleados.json"

    # Leer y cargar los datos del archivo JSON
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return "Error: No se pudo encontrar el archivo de datos de empleados."
    except json.JSONDecodeError:
        return "Error: El formato del archivo de datos de empleados es inválido."

    # Buscar al empleado por su ID
    empleado = data.get(id_empleado)

    # Si no se encuentra el empleado, devolver un mensaje informativo
    if not empleado:
        return f"No se encontró ningún empleado con el ID '{id_empleado}'."

    # Calcular los días restantes
    try:
        restantes = int(empleado["dias_totales"]) - int(empleado["dias_usados"])
        nombre_empleado = empleado.get("nombre", "desconocido")
        
        # Devolver el resultado formateado
        return (f"Al empleado {nombre_empleado} (ID: {id_empleado}) le quedan "
                f"{restantes} días de vacaciones.")
    except (KeyError, ValueError) as e:
        return f"Error en los datos del empleado {id_empleado}: {e}"
