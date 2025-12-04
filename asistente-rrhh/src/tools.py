import json
import os
from langchain_core.tools import tool

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "src", "data", "empleados.json")

@tool
def calcular_vacaciones(id_empleado: str) -> str:
    """
    Consulta los días de vacaciones disponibles para un empleado dado su ID.
    Retorna un mensaje con el total de días, días usados y días restantes.
    """
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            empleados = json.load(f)
            
        empleado = next((e for e in empleados if e["id"] == id_empleado), None)
        
        if not empleado:
            return f"No se encontró ningún empleado con el ID {id_empleado}."
            
        total = empleado["vacaciones_totales"]
        usados = empleado["vacaciones_usadas"]
        restantes = total - usados
        
        return (f"Empleado: {empleado['nombre']} (ID: {id_empleado})\n"
                f"Vacaciones Totales: {total}\n"
                f"Vacaciones Usadas: {usados}\n"
                f"Vacaciones Restantes: {restantes}")
                
    except FileNotFoundError:
        return "Error: No se encontró la base de datos de empleados."
    except Exception as e:
        return f"Error al consultar vacaciones: {str(e)}"

if __name__ == "__main__":
    print(calcular_vacaciones.invoke("E001"))
