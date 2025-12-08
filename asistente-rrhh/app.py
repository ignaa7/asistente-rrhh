import streamlit as st
from src.agent import get_agent
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
import os
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

st.set_page_config(
    page_title="Asistente RRHH",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS global para cambiar colores rojos a azul (excepto acciones destructivas)
st.markdown("""
<style>
/* Expanders - azul en hover y la flecha */
div[data-testid="stExpander"] summary:hover {
    color: #0066cc !important;
}
div[data-testid="stExpander"] summary svg {
    fill: #0066cc !important;
}

/* File uploader - traducir a español (ocultar texto original completamente) */
div[data-testid="stFileUploader"] button {
    background-color: #0066cc !important;
    border-color: #0066cc !important;
    color: white !important;
    font-size: 0 !important;
}
div[data-testid="stFileUploader"] button:hover {
    background-color: #0052a3 !important;
    border-color: #0052a3 !important;
    color: white !important;
}
div[data-testid="stFileUploader"] button:active {
    background-color: #003d7a !important;
    border-color: #003d7a !important;
    color: white !important;
}
div[data-testid="stFileUploader"] button::after {
    content: "Examinar archivos";
    font-size: 14px;
    visibility: visible;
}
div[data-testid="stFileUploadDropzone"]:hover {
    border-color: #0066cc !important;
}

/* Download buttons - azul en todos los estados con foco azul */
div[data-testid="stDownloadButton"] button {
    background-color: #0066cc !important;
    border-color: #0066cc !important;
    color: white !important;
}
div[data-testid="stDownloadButton"] button:hover {
    background-color: #0052a3 !important;
    border-color: #0052a3 !important;
    color: white !important;
}
div[data-testid="stDownloadButton"] button:active {
    background-color: #003d7a !important;
    border-color: #003d7a !important;
    color: white !important;
}
div[data-testid="stDownloadButton"] button:focus,
div[data-testid="stDownloadButton"] button:focus-visible {
    box-shadow: 0 0 0 0.2rem rgba(0, 102, 204, 0.5) !important;
    outline: none !important;
}

/* Chat input - azul en focus (contenedor y textarea) */
div[data-baseweb="textarea"]:focus-within {
    border-color: #0066cc !important;
    box-shadow: 0 0 0 0.2rem rgba(0, 102, 204, 0.25) !important;
}
textarea[data-testid="stChatInputTextArea"]:focus,
textarea[data-testid="stChatInputTextArea"]:focus-visible {
    border-color: #0066cc !important;
    box-shadow: none !important;
    outline: none !important;
}

/* Botones generales - sin sobrescribir, dejar que config.toml maneje el color primario */

/* Botones que deben ser azules - forzar azul y foco azul */
button[kind="primary"] {
    outline: none !important;
}
button[kind="primary"]:focus,
button[kind="primary"]:focus-visible {
    box-shadow: 0 0 0 0.2rem rgba(0, 102, 204, 0.5) !important;
    outline: none !important;
}

/* Botones destructivos (secondary) - forzar rojo en hover/active y texto blanco siempre */
button[kind="secondary"] {
    color: white !important;
}
button[kind="secondary"]:hover {
    background-color: #c82333 !important;
    border-color: #bd2130 !important;
    color: white !important;
}
button[kind="secondary"]:active {
    background-color: #a71d2a !important;
    border-color: #9c1c28 !important;
    color: white !important;
}
button[kind="secondary"]:focus,
button[kind="secondary"]:focus-visible {
    box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.5) !important;
    outline: none !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ==================== FUNCIONES DE AUTENTICACIÓN ====================
def cargar_empleados():
    """Carga la base de datos de empleados"""
    empleados_path = os.path.join("src", "data", "empleados.json")
    with open(empleados_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validar_login(id_empleado, password):
    """Valida las credenciales del empleado"""
    empleados = cargar_empleados()
    empleado = next((e for e in empleados if e["id"] == id_empleado), None)
    
    if empleado and empleado["password"] == password:
        # No devolver la contraseña en el objeto de usuario
        return {k: v for k, v in empleado.items() if k != "password"}
    return None

# ==================== PANTALLA DE LOGIN ====================
# ==================== PANTALLA DE LOGIN ====================
if "usuario" not in st.session_state:
    # Crear un placeholder para toda la pantalla de login
    login_placeholder = st.empty()
    
    with login_placeholder.container():
        st.title("👔 Asistente Virtual de RRHH")
        st.markdown("### 🔐 Iniciar Sesión")
        st.markdown("Por favor, ingresa tus credenciales para acceder al sistema.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("---")
            
            # CSS personalizado para el login
            st.markdown("""
            <style>
            /* Inputs - forzar azul en TODOS los estados de focus */
            div[data-testid="stForm"] input:focus,
            div[data-testid="stForm"] input:focus-visible,
            div[data-testid="stForm"] input[type="text"]:focus,
            div[data-testid="stForm"] input[type="password"]:focus {
                border-color: #0066cc !important;
                box-shadow: 0 0 0 0.2rem rgba(0, 102, 204, 0.25) !important;
                outline: none !important;
            }
            
            /* Contenedor de inputs - forzar azul */
            div[data-testid="stForm"] div[data-baseweb="input"]:focus-within {
                border-color: #0066cc !important;
                box-shadow: 0 0 0 0.2rem rgba(0, 102, 204, 0.25) !important;
            }
            
            /* Botón de login - forzar azul en todos los estados */
            div[data-testid="stFormSubmitButton"] button {
                background-color: #0066cc !important;
                color: white !important;
                border-color: #0066cc !important;
            }
            div[data-testid="stFormSubmitButton"] button:hover {
                background-color: #0052a3 !important;
                color: white !important;
                border-color: #0052a3 !important;
            }
            div[data-testid="stFormSubmitButton"] button:active {
                background-color: #003d7a !important;
                color: white !important;
                border-color: #003d7a !important;
            }
            div[data-testid="stFormSubmitButton"] button:focus,
            div[data-testid="stFormSubmitButton"] button:focus-visible {
                background-color: #0052a3 !important;
                color: white !important;
                border-color: #0052a3 !important;
                box-shadow: 0 0 0 0.2rem rgba(0, 102, 204, 0.25) !important;
                outline: none !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Usar formulario para permitir Enter/Intro
            with st.form("login_form"):
                id_empleado = st.text_input("ID de Empleado", placeholder="Ej: E001")
                password = st.text_input("Contraseña", type="password", placeholder="Introduce tu contraseña")
                
                st.markdown("")  # Espacio
                
                # Submit button
                submitted = st.form_submit_button("🔓 Iniciar Sesión", use_container_width=True)
                
                if submitted:
                    if id_empleado and password:
                        with st.spinner("🔄 Validando credenciales..."):
                            usuario = validar_login(id_empleado, password)
                            if usuario:
                                st.session_state.usuario = usuario
                                # Limpiar el placeholder inmediatamente para quitar el formulario
                                login_placeholder.empty()
                                st.rerun()
                            else:
                                st.error("❌ ID de empleado o contraseña incorrectos")
                    else:
                        st.warning("⚠️ Por favor, ingresa tu ID y contraseña")
            
            st.markdown("---")
    
    st.stop()

# ==================== USUARIO AUTENTICADO ====================
usuario = st.session_state.usuario

# Configurar avatar del usuario (foto de perfil o emoji)
# El campo foto_perfil puede ser:
# - Una URL: "https://ejemplo.com/foto.jpg"
# - Una ruta local: "src/data/avatares/E001.jpg"  
# - null o no existir: usa emoji por defecto "👤"
if "user_avatar" not in st.session_state:
    foto_perfil = usuario.get("foto_perfil")
    if foto_perfil:
        # Si existe foto_perfil, usarla (puede ser URL o ruta local)
        st.session_state.user_avatar = foto_perfil
    else:
        # Si no existe, usar emoji por defecto
        st.session_state.user_avatar = "👤"

# Inicializar avatar del asistente
if "assistant_avatar" not in st.session_state:
    st.session_state.assistant_avatar = "🤖"

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []



# ==================== SIDEBAR ====================
with st.sidebar:
    st.title("👔 Asistente RRHH")
    st.markdown("---")
    
    # Información del usuario logueado
    st.subheader(f"👤 {usuario['nombre']}")
    st.markdown(f"**{usuario['cargo']}**")
    st.markdown(f"ID: `{usuario['id']}`")
    
    # Cambiar foto de perfil
    with st.expander("📷 Cambiar foto de perfil"):
        # Mostrar estado actual
        if st.session_state.user_avatar != "👤":
            st.info(f"✅ Tienes una foto de perfil configurada")
            
            # Botón eliminar foto
            if st.button("🗑️ Eliminar foto de perfil", key="btn_eliminar_foto"):
                # Eliminar archivo físico si existe
                if os.path.exists(st.session_state.user_avatar):
                    try:
                        os.remove(st.session_state.user_avatar)
                    except:
                        pass  # Si no se puede eliminar, continuar
                
                # Actualizar empleados.json
                empleados_path = os.path.join("src", "data", "empleados.json")
                with open(empleados_path, 'r', encoding='utf-8') as f:
                    empleados = json.load(f)
                
                for emp in empleados:
                    if emp["id"] == usuario["id"]:
                        emp["foto_perfil"] = None
                        break
                
                with open(empleados_path, 'w', encoding='utf-8') as f:
                    json.dump(empleados, f, indent=2, ensure_ascii=False)
                
                # Actualizar session state
                st.session_state.user_avatar = "👤"
                st.session_state.usuario["foto_perfil"] = None
                
                st.success("✅ Foto eliminada. Ahora usas el avatar por defecto.")
                st.rerun()
            
            st.markdown("---")
        
        # Subir nueva foto
        foto_upload = st.file_uploader(
            "Sube tu foto",
            type=["jpg", "jpeg", "png"],
            help="Formatos aceptados: JPG, PNG. Tamaño máximo: 5MB",
            key="uploader_foto_perfil"
        )
        
        if foto_upload is not None and st.button("💾 Guardar foto", key="btn_guardar_foto"):
            # Crear carpeta de avatares si no existe
            avatares_dir = os.path.join("src", "data", "avatares")
            os.makedirs(avatares_dir, exist_ok=True)
            
            # Guardar la imagen
            extension = foto_upload.name.split('.')[-1]
            nombre_archivo = f"{usuario['id']}.{extension}"
            ruta_foto = os.path.join(avatares_dir, nombre_archivo)
            
            with open(ruta_foto, "wb") as f:
                f.write(foto_upload.getbuffer())
            
            # Actualizar empleados.json
            empleados_path = os.path.join("src", "data", "empleados.json")
            with open(empleados_path, 'r', encoding='utf-8') as f:
                empleados = json.load(f)
            
            for emp in empleados:
                if emp["id"] == usuario["id"]:
                    emp["foto_perfil"] = ruta_foto
                    break
            
            with open(empleados_path, 'w', encoding='utf-8') as f:
                json.dump(empleados, f, indent=2, ensure_ascii=False)
            
            # Actualizar session state
            st.session_state.user_avatar = ruta_foto
            st.session_state.usuario["foto_perfil"] = ruta_foto
            
            st.success("✅ Foto de perfil actualizada!")
            st.rerun()
    
    # Botón cerrar sesión
    if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
        # Limpiar toda la sesión
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.markdown("---")
    
    # Botón para limpiar historial con confirmación
    st.subheader("⚙️ Opciones")
    
    if st.button("🗑️ Limpiar Historial", use_container_width=True):
        st.session_state.show_confirm_clear = True
    
    # Diálogo de confirmación
    if st.session_state.get("show_confirm_clear", False):
        st.warning("⚠️ ¿Estás seguro de que quieres borrar todo el historial?")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Sí", use_container_width=True):
                # Limpiar TODO: historial visual + memoria del agente
                st.session_state.messages = []
                
                # Reinicializar memoria simple
                st.session_state.memory = ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True,
                    output_key="output"
                )
                
                # Reinicializar agente con nueva memoria
                st.session_state.agent = get_agent(memory=st.session_state.memory)
                st.session_state.show_confirm_clear = False
                st.rerun()
        
        with col2:
            if st.button("❌ No", use_container_width=True):
                st.session_state.show_confirm_clear = False
                st.rerun()
    
    st.markdown("---")
    
    # Botones para exportar conversación
    st.subheader("📥 Exportar Conversación")
    
    if st.session_state.messages:
        from datetime import datetime
        
        # Generar contenido para exportar
        def generar_contenido_txt():
            """Genera el contenido en formato .txt"""
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            num_mensajes = len(st.session_state.messages)
            
            contenido = f"CONVERSACIÓN CON ASISTENTE DE RRHH\n"
            contenido += f"Exportado: {timestamp}\n"
            contenido += f"Total de mensajes: {num_mensajes}\n"
            contenido += f"{'='*60}\n\n"
            
            for i, msg in enumerate(st.session_state.messages, 1):
                rol = "USUARIO" if msg["role"] == "user" else "ASISTENTE"
                contenido += f"[{i}] {rol}:\n"
                contenido += f"{msg['content']}\n\n"
                contenido += f"{'-'*60}\n\n"
            
            return contenido
        
        def generar_contenido_md():
            """Genera el contenido en formato .md"""
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            num_mensajes = len(st.session_state.messages)
            
            contenido = f"# Conversación con Asistente de RRHH\n\n"
            contenido += f"**Exportado:** {timestamp}  \n"
            contenido += f"**Total de mensajes:** {num_mensajes}\n\n"
            contenido += f"---\n\n"
            
            for i, msg in enumerate(st.session_state.messages, 1):
                if msg["role"] == "user":
                    contenido += f"## 👤 Usuario (Mensaje {i})\n\n"
                else:
                    contenido += f"## 🤖 Asistente (Mensaje {i})\n\n"
                
                contenido += f"{msg['content']}\n\n"
                contenido += f"---\n\n"
            
            return contenido
        
        # Botón para exportar como .txt
        contenido_txt = generar_contenido_txt()
        st.download_button(
            label="📄 Exportar como TXT",
            data=contenido_txt,
            file_name=f"conversacion_rrhh_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
        # Botón para exportar como .md
        contenido_md = generar_contenido_md()
        st.download_button(
            label="📝 Exportar como MD",
            data=contenido_md,
            file_name=f"conversacion_rrhh_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    else:
        st.info("💬 No hay conversación para exportar todavía")


# ==================== MAIN CONTENT ====================
st.title(f"👔 Asistente Virtual de RRHH - Hola, {usuario['nombre']}!")
st.markdown(f"""
Bienvenido/a al asistente de RRHH, {usuario['nombre']}. Estoy aquí para ayudarte con:
- **Políticas de la empresa** (vacaciones, teletrabajo, bajas...)
- **Tus días de vacaciones**
- **Solicitar vacaciones o reportar bajas médicas**
- **Consultar tus nóminas**
- **Beneficios para empleados**
""")


# Inicializar memoria conversacional (solo una vez)
if "memory" not in st.session_state:
    try:
        # Crear memoria conversacional simple (sin conteo de tokens)
        st.session_state.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
    except Exception as e:
        st.error(f"Error al inicializar la memoria: {e}")
        st.stop()

# Inicializar agente (solo una vez) con la memoria y contexto del usuario
if "agent" not in st.session_state:
    try:
        with st.spinner("Iniciando el sistema..."):
            st.session_state.agent = get_agent(
                memory=st.session_state.memory,
                user_context=usuario  # Pasar info del usuario al agente
            )
    except Exception as e:
        st.error(f"Error al iniciar el agente: {e}")
        st.stop()

# Mostrar mensajes del historial con avatares
for message in st.session_state.messages:
    avatar = st.session_state.user_avatar if message["role"] == "user" else st.session_state.assistant_avatar
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Input del usuario
if prompt := st.chat_input("¿En qué puedo ayudarte hoy?"):
    # Guardar y mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=st.session_state.user_avatar):
        st.markdown(prompt)

    # Generar respuesta
    with st.chat_message("assistant", avatar=st.session_state.assistant_avatar):
        try:
            with st.spinner("Pensando..."):
                # El agente ahora usa la memoria automáticamente
                response = st.session_state.agent.invoke({"input": prompt})
                output_text = response["output"]
                st.markdown(output_text)
                
                # Guardar respuesta en historial de Streamlit
                st.session_state.messages.append({"role": "assistant", "content": output_text})
                st.rerun()  # Forzar actualización del sidebar
                
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")
