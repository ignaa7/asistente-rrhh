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
    Si no se proporciona fecha_fin_estimada, la baja se considera "abierta".
    
    Args:
        id_empleado: ID del empleado (ej: E001, E002) - OBLIGATORIO
        fecha_inicio: Fecha de inicio de la baja en formato YYYY-MM-DD (ej: 2025-12-05) - OBLIGATORIO
        fecha_fin_estimada: Fecha estimada de fin en formato YYYY-MM-DD (opcional). Si se omite, es indefinida.
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
                # La baja activa NO tiene fecha fin (está abierta): IMPOSIBLE crear nueva
                return (f"❌ Error: Ya tienes una baja médica ABIERTA (sin fecha fin).\n"
                       f"Baja activa: {baja['id_baja']} desde {baja['fecha_inicio']}\n"
                       f"Debes finalizar la baja anterior antes de reportar una nueva.")
        
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
        periodo_text = f"{fecha_inicio} a {fecha_fin_estimada}" if fecha_fin_estimada else f"desde {fecha_inicio} (Indefinida/Abierta)"
        
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

@tool
def actualizar_baja_medica(
    id_empleado: str,
    fecha_inicio: str,
    fecha_fin: str = "",
    motivo: str = "",
    notas: str = ""
) -> str:
    """
    Permite finalizar una baja médica existente o actualizar sus detalles.
    Busca la baja activa del empleado que coincida con la fecha de inicio proporcionada.
    
    Args:
        id_empleado: ID del empleado (ej: E001) - OBLIGATORIO
        fecha_inicio: Fecha de inicio de la baja a modificar (para identificarla) - OBLIGATORIO
        fecha_fin: Si se proporciona, se establece como fecha fin y se considera FINALIZADA la baja.
        motivo: Nuevo motivo (opcional)
        notas: Nuevas notas (opcional)
    """
    from datetime import datetime
    
    BAJAS_PATH = os.path.join(BASE_DIR, "src", "data", "bajas_medicas.json")
    
    try:
        if not os.path.exists(BAJAS_PATH):
            return "❌ Error: No hay registro de bajas médicas."
            
        with open(BAJAS_PATH, 'r', encoding='utf-8') as f:
            bajas = json.load(f)
            
        # Buscar la baja (sin filtrar por estado para permitir editar finalizadas)
        baja_encontrada = None
        for b in bajas:
            if (b["id_empleado"] == id_empleado and 
                b["fecha_inicio"] == fecha_inicio):
                baja_encontrada = b
                break
        
        if not baja_encontrada:
            return (f"❌ No se encontró ninguna baja para el empleado {id_empleado} "
                   f"que haya comenzado el {fecha_inicio}.")
        
        cambios = []
        
        # Actualizar campos
        if fecha_fin:
            # Validar fecha
            try:
                fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
                inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
                if fin < inicio:
                    return "❌ Error: La fecha de fin no puede ser anterior a la de inicio."
                
                baja_encontrada["fecha_fin_estimada"] = fecha_fin
                baja_encontrada["estado"] = "finalizada" # Asumimos que si pone fecha fin ahora, es que ya terminó
                cambios.append(f"Fecha fin establecida a {fecha_fin} (Baja Finalizada)")
            except ValueError:
                return "❌ Error: Formato de fecha incorrecto (use YYYY-MM-DD)."
                
        if motivo:
            baja_encontrada["motivo"] = motivo
            cambios.append(f"Motivo actualizado a '{motivo}'")
            
        if notas:
            baja_encontrada["notas"] = notas
            cambios.append(f"Notas actualizadas")
            
        if not cambios:
            return "⚠️ No se proporcionaron cambios para realizar."
            
        # Guardar
        with open(BAJAS_PATH, 'w', encoding='utf-8') as f:
            json.dump(bajas, f, ensure_ascii=False, indent=2)
            
        return (f"✅ Baja médica actualizada exitosamente\n"
               f"📋 ID Baja: {baja_encontrada['id_baja']}\n"
               f"Cambios realizados:\n- " + "\n- ".join(cambios))
               
    except Exception as e:
        return f"❌ Error al actualizar la baja: {str(e)}"


@tool
def consultar_bajas_medicas(
    id_empleado: str,
    estado: str = "",
    fecha_inicio: str = "",
    fecha_fin: str = ""
) -> str:
    """
    Consulta el historial de bajas médicas de un empleado.
    
    Args:
        id_empleado: ID del empleado (ej: E001) - OBLIGATORIO
        estado: Filtrar por estado ("activa", "finalizada") - Opcional
        fecha_inicio: Filtrar bajas que comiencen a partir de esta fecha (YYYY-MM-DD) - Opcional
        fecha_fin: Filtrar bajas que terminen antes de esta fecha (YYYY-MM-DD) - Opcional
    """
    from datetime import datetime
    
    BAJAS_PATH = os.path.join(BASE_DIR, "src", "data", "bajas_medicas.json")
    
    try:
        if not os.path.exists(BAJAS_PATH):
            return "ℹ️ No hay registros de bajas médicas en el sistema."
            
        with open(BAJAS_PATH, 'r', encoding='utf-8') as f:
            bajas = json.load(f)
            
        # Filtrar por empleado
        mis_bajas = [b for b in bajas if b["id_empleado"] == id_empleado]
        
        if not mis_bajas:
            return f"ℹ️ No se encontraron bajas médicas para el empleado {id_empleado}."
            
        # Aplicar filtros opcionales
        if estado:
            mis_bajas = [b for b in mis_bajas if b["estado"].lower() == estado.lower()]
            
        if fecha_inicio:
            try:
                filtro_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
                mis_bajas = [b for b in mis_bajas if datetime.strptime(b["fecha_inicio"], "%Y-%m-%d") >= filtro_inicio]
            except ValueError:
                return "❌ Error: Formato de fecha_inicio incorrecto (use YYYY-MM-DD)."

        if fecha_fin:
            try:
                filtro_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
                # Solo filtramos si la baja tiene fecha fin definida
                mis_bajas = [b for b in mis_bajas if b.get("fecha_fin_estimada") and datetime.strptime(b["fecha_fin_estimada"], "%Y-%m-%d") <= filtro_fin]
            except ValueError:
                return "❌ Error: Formato de fecha_fin incorrecto (use YYYY-MM-DD)."
        
        if not mis_bajas:
            return "ℹ️ No se encontraron bajas médicas con los filtros especificados."
            
        # Formatear respuesta
        respuesta = f"🏥 **Historial de Bajas Médicas** ({len(mis_bajas)} encontradas)\n\n"
        for b in mis_bajas:
            estado_icon = "🟢" if b["estado"] == "activa" else "🔴"
            fin = b.get("fecha_fin_estimada") if b.get("fecha_fin_estimada") else "Indefinida"
            respuesta += f"{estado_icon} **{b['fecha_inicio']}** al **{fin}** ({b['estado'].upper()})\n"
            respuesta += f"   Motivo: {b['motivo']}\n"
            if b.get("notas"):
                respuesta += f"   Notas: {b['notas']}\n"
            respuesta += "\n"
            
        return respuesta

    except Exception as e:
        return f"❌ Error al consultar bajas médicas: {str(e)}"


@tool
def consultar_solicitudes_vacaciones(
    id_empleado: str,
    estado: str = "",
    fecha_inicio: str = "",
    fecha_fin: str = ""
) -> str:
    """
    Consulta el historial de solicitudes de vacaciones de un empleado.
    
    Args:
        id_empleado: ID del empleado (ej: E001) - OBLIGATORIO
        estado: Filtrar por estado ("pendiente", "aprobada", "rechazada") - Opcional
        fecha_inicio: Filtrar vacaciones que comiencen a partir de esta fecha (YYYY-MM-DD) - Opcional
        fecha_fin: Filtrar vacaciones que terminen antes de esta fecha (YYYY-MM-DD) - Opcional
    """
    from datetime import datetime
    
    SOLICITUDES_PATH = os.path.join(BASE_DIR, "src", "data", "solicitudes_vacaciones.json")
    
    try:
        if not os.path.exists(SOLICITUDES_PATH):
            return "ℹ️ No hay registros de solicitudes de vacaciones."
            
        with open(SOLICITUDES_PATH, 'r', encoding='utf-8') as f:
            solicitudes = json.load(f)
            
        # Filtrar por empleado
        mis_solicitudes = [s for s in solicitudes if s["id_empleado"] == id_empleado]
        
        if not mis_solicitudes:
            return f"ℹ️ No se encontraron solicitudes de vacaciones para el empleado {id_empleado}."
            
        # Aplicar filtros opcionales
        if estado:
            mis_solicitudes = [s for s in mis_solicitudes if s["estado"].lower() == estado.lower()]
            
        if fecha_inicio:
            try:
                filtro_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
                mis_solicitudes = [s for s in mis_solicitudes if datetime.strptime(s["fecha_inicio"], "%Y-%m-%d") >= filtro_inicio]
            except ValueError:
                return "❌ Error: Formato de fecha_inicio incorrecto (use YYYY-MM-DD)."

        if fecha_fin:
            try:
                filtro_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
                mis_solicitudes = [s for s in mis_solicitudes if datetime.strptime(s["fecha_fin"], "%Y-%m-%d") <= filtro_fin]
            except ValueError:
                return "❌ Error: Formato de fecha_fin incorrecto (use YYYY-MM-DD)."
        
        if not mis_solicitudes:
            return "ℹ️ No se encontraron solicitudes con los filtros especificados."
            
        # Formatear respuesta
        respuesta = f"🏖️ **Historial de Vacaciones** ({len(mis_solicitudes)} encontradas)\n\n"
        for s in mis_solicitudes:
            iconos = {"pendiente": "⏳", "aprobada": "✅", "rechazada": "❌"}
            icono = iconos.get(s["estado"], "❓")
            
            respuesta += f"{icono} **{s['fecha_inicio']}** al **{s['fecha_fin']}** ({s['dias_solicitados']} días)\n"
            respuesta += f"   Estado: **{s['estado'].upper()}**\n"
            if s.get("comentarios"):
                respuesta += f"   Comentarios: {s['comentarios']}\n"
            respuesta += "\n"
            
        return respuesta

    except Exception as e:
        return f"❌ Error al consultar solicitudes de vacaciones: {str(e)}"


@tool
def consultar_nomina(id_empleado: str, mes: str = "") -> str:
    """
    Consulta la nómina/recibo de pago de un empleado.
    Si no se especifica mes, devuelve la última nómina disponible.
    
    Args:
        id_empleado: ID del empleado (ej: E001, E002) - OBLIGATORIO
        mes: Mes de la nómina en formato YYYY-MM (ej: 2025-11) - OPCIONAL
             Si no se especifica, devuelve la última nómina
    
    Returns:
        Información detallada de la nómina solicitada
    """
    NOMINAS_PATH = os.path.join(BASE_DIR, "src", "data", "nominas.json")
    
    try:
        # 1. Cargar datos del empleado para verificar que existe
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            empleados = json.load(f)
        
        empleado = next((e for e in empleados if e["id"] == id_empleado), None)
        
        if not empleado:
            return f"❌ No se encontró ningún empleado con el ID {id_empleado}."
        
        # 2. Cargar nóminas
        if not os.path.exists(NOMINAS_PATH):
            return "❌ Error: No se encontró la base de datos de nóminas."
        
        with open(NOMINAS_PATH, 'r', encoding='utf-8') as f:
            nominas = json.load(f)
        
        # 3. Filtrar nóminas del empleado
        nominas_empleado = [n for n in nominas if n["id_empleado"] == id_empleado]
        
        if not nominas_empleado:
            return f"❌ No se encontraron nóminas para el empleado {empleado['nombre']} ({id_empleado})."
        
        # 4. Seleccionar nómina según criterio
        if mes:
            # Buscar nómina del mes específico
            nomina = next((n for n in nominas_empleado if n["mes"] == mes), None)
            
            if not nomina:
                meses_disponibles = [n["mes"] for n in nominas_empleado]
                return (f"❌ No se encontró nómina para el mes {mes}.\n"
                       f"Meses disponibles: {', '.join(sorted(meses_disponibles))}")
        else:
            # Devolver la última nómina (ordenar por mes descendente)
            nominas_empleado_ordenadas = sorted(nominas_empleado, key=lambda x: x["mes"], reverse=True)
            nomina = nominas_empleado_ordenadas[0]
        
        # 5. Formatear respuesta con toda la información
        conceptos = nomina["conceptos"]
        
        respuesta = f"💰 **Nómina de {nomina['nombre_empleado']}** ({id_empleado})\n\n"
        respuesta += f"📅 **Mes**: {nomina['mes']}\n"
        respuesta += f"📆 **Fecha de pago**: {nomina['fecha_pago']}\n"
        respuesta += f"🆔 **ID Nómina**: {nomina['id_nomina']}\n\n"
        
        respuesta += f"**DESGLOSE SALARIAL**\n"
        respuesta += f"{'─'*40}\n"
        respuesta += f"Salario Base:           {conceptos['base']:>10.2f} €\n"
        respuesta += f"Complementos:           {conceptos['complementos']:>10.2f} €\n"
        respuesta += f"{'─'*40}\n"
        respuesta += f"**Salario Bruto:        {nomina['salario_bruto']:>10.2f} €**\n\n"
        
        respuesta += f"**DEDUCCIONES**\n"
        respuesta += f"{'─'*40}\n"
        respuesta += f"IRPF:                   {conceptos['irpf']:>10.2f} €\n"
        respuesta += f"Seguridad Social:       {conceptos['seguridad_social']:>10.2f} €\n"
        respuesta += f"{'─'*40}\n"
        respuesta += f"Total Deducciones:      {nomina['deducciones']:>10.2f} €\n\n"
        
        respuesta += f"{'═'*40}\n"
        respuesta += f"**💵 SALARIO NETO:      {nomina['salario_neto']:>10.2f} €**\n"
        respuesta += f"{'═'*40}\n"
        
        return respuesta
        
    except FileNotFoundError:
        return "❌ Error: No se encontraron los archivos necesarios."
    except Exception as e:
        return f"❌ Error al consultar la nómina: {str(e)}"




