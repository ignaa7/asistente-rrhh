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

@tool
def solicitar_vacaciones(id_empleado: str, fecha_inicio: str, fecha_fin: str, comentarios: str = "") -> str:
    """
    Permite a un empleado solicitar días de vacaciones.
    Valida que el empleado tenga días suficientes disponibles antes de guardar la solicitud.
    
    Args:
        id_empleado: ID del empleado (ej: E001, E002)
        fecha_inicio: Fecha de inicio de las vacaciones en formato YYYY-MM-DD (ej: 2025-12-15)
        fecha_fin: Fecha de fin de las vacaciones en formato YYYY-MM-DD (ej: 2025-12-22)
        comentarios: Comentarios opcionales sobre la solicitud
    
    Returns:
        Mensaje confirmando la solicitud o indicando error si no hay días suficientes
    """
    from datetime import datetime
    
    SOLICITUDES_PATH = os.path.join(BASE_DIR, "src", "data", "solicitudes_vacaciones.json")
    
    try:
        # 1. Cargar datos del empleado
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            empleados = json.load(f)
        
        empleado = next((e for e in empleados if e["id"] == id_empleado), None)
        
        if not empleado:
            return f"❌ No se encontró ningún empleado con el ID {id_empleado}."
        
        # 2. Calcular días solicitados
        try:
            inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
            
            if fin < inicio:
                return "❌ Error: La fecha de fin no puede ser anterior a la fecha de inicio."
            
            # Calcular días laborables (aproximado: total de días)
            dias_solicitados = (fin - inicio).days + 1
            
        except ValueError:
            return "❌ Error: Las fechas deben estar en formato YYYY-MM-DD (ejemplo: 2025-12-15)."
        
        # 3. Validar días disponibles
        total = empleado["vacaciones_totales"]
        usados = empleado["vacaciones_usadas"]
        restantes = total - usados
        
        if dias_solicitados > restantes:
            return (f"❌ Solicitud rechazada: No tienes días suficientes.\n"
                   f"Días solicitados: {dias_solicitados}\n"
                   f"Días disponibles: {restantes} (de {total} totales)")
        
        # 4. Crear la solicitud
        # Cargar solicitudes existentes
        if os.path.exists(SOLICITUDES_PATH):
            with open(SOLICITUDES_PATH, 'r', encoding='utf-8') as f:
                solicitudes = json.load(f)
        else:
            solicitudes = []
        
        # Generar ID único
        id_solicitud = f"SOL{str(len(solicitudes) + 1).zfill(3)}"
        
        nueva_solicitud = {
            "id_solicitud": id_solicitud,
            "id_empleado": id_empleado,
            "nombre_empleado": empleado["nombre"],
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "dias_solicitados": dias_solicitados,
            "comentarios": comentarios,
            "estado": "pendiente",
            "fecha_solicitud": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 5. Guardar la solicitud
        solicitudes.append(nueva_solicitud)
        
        with open(SOLICITUDES_PATH, 'w', encoding='utf-8') as f:
            json.dump(solicitudes, f, ensure_ascii=False, indent=2)
        
        return (f"✅ Solicitud de vacaciones creada exitosamente\n\n"
               f"📋 ID de Solicitud: {id_solicitud}\n"
               f"👤 Empleado: {empleado['nombre']} ({id_empleado})\n"
               f"📅 Período: {fecha_inicio} a {fecha_fin}\n"
               f"⏱️ Días solicitados: {dias_solicitados}\n"
               f"📊 Estado: Pendiente de aprobación\n"
               f"💬 Comentarios: {comentarios if comentarios else 'N/A'}\n\n"
               f"Después de esta solicitud te quedarán {restantes - dias_solicitados} días disponibles.")
        
    except FileNotFoundError:
        return "❌ Error: No se encontró la base de datos de empleados."
    except Exception as e:
        return f"❌ Error al procesar la solicitud de vacaciones: {str(e)}"


@tool
def reportar_baja_medica(
    id_empleado: str, 
    fecha_inicio: str, 
    fecha_fin_estimada: str = "", 
    motivo: str = "", 
    notas: str = ""
) -> str:
    """
    Permite a un empleado reportar una baja médica.
    Valida que no existan bajas activas solapadas para el mismo empleado.
    
    Args:
        id_empleado: ID del empleado (ej: E001, E002) - OBLIGATORIO
        fecha_inicio: Fecha de inicio de la baja en formato YYYY-MM-DD (ej: 2025-12-05) - OBLIGATORIO
        fecha_fin_estimada: Fecha estimada de fin en formato YYYY-MM-DD (opcional)
        motivo: Motivo de la baja (ej: "Gripe", "Lesión") - opcional
        notas: Notas adicionales sobre la baja - opcional
    
    Returns:
        Mensaje confirmando el reporte o indicando error si hay bajas solapadas
    """
    from datetime import datetime
    
    BAJAS_PATH = os.path.join(BASE_DIR, "src", "data", "bajas_medicas.json")
    
    try:
        # 1. Cargar datos del empleado
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            empleados = json.load(f)
        
        empleado = next((e for e in empleados if e["id"] == id_empleado), None)
        
        if not empleado:
            return f"❌ No se encontró ningún empleado con el ID {id_empleado}."
        
        # 2. Validar formato de fechas
        try:
            inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            
            fin_estimada = None
            if fecha_fin_estimada:
                fin_estimada = datetime.strptime(fecha_fin_estimada, "%Y-%m-%d")
                
                if fin_estimada < inicio:
                    return "❌ Error: La fecha de fin estimada no puede ser anterior a la fecha de inicio."
        except ValueError:
            return "❌ Error: Las fechas deben estar en formato YYYY-MM-DD (ejemplo: 2025-12-05)."
        
        # 3. Cargar bajas existentes y validar solapamiento
        if os.path.exists(BAJAS_PATH):
            with open(BAJAS_PATH, 'r', encoding='utf-8') as f:
                bajas = json.load(f)
        else:
            bajas = []
        
        # Buscar bajas activas del mismo empleado
        bajas_activas = [b for b in bajas if b["id_empleado"] == id_empleado and b["estado"] == "activa"]
        
        for baja in bajas_activas:
            baja_inicio = datetime.strptime(baja["fecha_inicio"], "%Y-%m-%d")
            
            # Si la baja activa tiene fecha de fin estimada
            if baja.get("fecha_fin_estimada"):
                baja_fin = datetime.strptime(baja["fecha_fin_estimada"], "%Y-%m-%d")
                
                # Verificar solapamiento
                # Hay solapamiento si:
                # - La nueva baja empieza antes de que termine la activa
                # - La nueva baja con fecha fin se solapa con la activa
                if fin_estimada:
                    # Ambas tienen fecha fin: verificar solapamiento completo
                    if not (fin_estimada < baja_inicio or inicio > baja_fin):
                        return (f"❌ Error: Ya tienes una baja médica activa que se solapa con estas fechas.\n"
                               f"Baja activa: {baja['id_baja']} del {baja['fecha_inicio']} al {baja['fecha_fin_estimada']}\n"
                               f"Por favor, contacta con RRHH si necesitas modificar tu baja existente.")
                else:
                    # La nueva no tiene fin: verificar que no empiece antes de que termine la activa
                    if inicio <= baja_fin:
                        return (f"❌ Error: Ya tienes una baja médica activa que se solapa con esta fecha.\n"
                               f"Baja activa: {baja['id_baja']} del {baja['fecha_inicio']} al {baja['fecha_fin_estimada']}\n"
                               f"Por favor, contacta con RRHH si necesitas modificar tu baja existente.")
            else:
                # La baja activa no tiene fecha fin: cualquier nueva baja se consideraría solapada
                return (f"❌ Error: Ya tienes una baja médica activa sin fecha de fin.\n"
                       f"Baja activa: {baja['id_baja']} desde {baja['fecha_inicio']}\n"
                       f"Por favor, contacta con RRHH si necesitas reportar una nueva baja.")
        
        # 4. Crear el reporte de baja
        # Generar ID único
        id_baja = f"BM{str(len(bajas) + 1).zfill(3)}"
        
        nueva_baja = {
            "id_baja": id_baja,
            "id_empleado": id_empleado,
            "nombre_empleado": empleado["nombre"],
            "fecha_inicio": fecha_inicio,
            "fecha_fin_estimada": fecha_fin_estimada if fecha_fin_estimada else None,
            "motivo": motivo if motivo else "No especificado",
            "tiene_justificante": False,
            "estado": "activa",
            "fecha_reporte": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "notas": notas if notas else ""
        }
        
        # 5. Guardar el reporte
        bajas.append(nueva_baja)
        
        with open(BAJAS_PATH, 'w', encoding='utf-8') as f:
            json.dump(bajas, f, ensure_ascii=False, indent=2)
        
        # Mensaje personalizado según si tiene fecha fin o no
        periodo_text = f"{fecha_inicio} a {fecha_fin_estimada}" if fecha_fin_estimada else f"desde {fecha_inicio} (fecha fin no especificada)"
        
        return (f"✅ Baja médica reportada exitosamente\n\n"
               f"📋 ID de Baja: {id_baja}\n"
               f"👤 Empleado: {empleado['nombre']} ({id_empleado})\n"
               f"📅 Período: {periodo_text}\n"
               f"🏥 Motivo: {nueva_baja['motivo']}\n"
               f"📊 Estado: Activa\n"
               f"💬 Notas: {nueva_baja['notas'] if nueva_baja['notas'] else 'N/A'}\n\n"
               f"⚠️ Recuerda: Debes presentar el justificante médico en un plazo máximo de 3 días.")
        
    except FileNotFoundError:
        return "❌ Error: No se encontró la base de datos de empleados."
    except Exception as e:
        return f"❌ Error al procesar el reporte de baja médica: {str(e)}"


if __name__ == "__main__":
    print(calcular_vacaciones.invoke("E001"))
    print("\n" + "="*50 + "\n")
    print(solicitar_vacaciones.invoke({
        "id_empleado": "E001",
        "fecha_inicio": "2025-12-15",
        "fecha_fin": "2025-12-22",
        "comentarios": "Vacaciones de Navidad"
    }))
    print("\n" + "="*50 + "\n")
    print(reportar_baja_medica.invoke({
        "id_empleado": "E001",
        "fecha_inicio": "2025-12-10",
        "fecha_fin_estimada": "2025-12-12",
        "motivo": "Gripe",
        "notas": "Reposo en casa"
    }))
