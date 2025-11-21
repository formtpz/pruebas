import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime
import pytz
from urllib.parse import urlparse


def Correcciones(usuario, puesto):

    # ----- Conexión a la BD ----- #
    uri = st.secrets.db_credentials.URI
    result = urlparse(uri)
    hostname = result.hostname
    database = result.path[1:]
    username = result.username
    pwd = result.password
    port_id = result.port

    con = psycopg2.connect(
        host=hostname,
        dbname=database,
        user=username,
        password=pwd,
        port=port_id
    )

    st.title("Corrección de Reportes")

    st.write(
        """
        Aquí puedes visualizar tus reportes, filtrar por fecha y solicitar correcciones
        o eliminaciones si encuentras errores.
        """
    )

    # ----- Filtro de fechas ----- #
    st.subheader("Filtrar reportes por fecha")

    col1, col2 = st.columns(2)

    with col1:
        fecha_inicio = st.date_input("Fecha inicio")
    with col2:
        fecha_fin = st.date_input("Fecha fin")

    if fecha_inicio > fecha_fin:
        st.error("La fecha de inicio no puede ser mayor que la fecha final.")
        return

    # ----- Obtener nombre del usuario ----- #
    df_nombre = pd.read_sql(f"SELECT nombre FROM usuarios WHERE usuario = '{usuario}'", con)
    nombre = df_nombre.loc[0, "nombre"]

    # ----- Consultar reportes del usuario ----- #
    query = f"""
        SELECT id AS ID Reporte, marca, usuario, nombre, fecha, unidad_asignacion, tipo, produccion, aprobados, rechazados, horas, uit, hito, lote, area, efes, informales, paquete, observaciones, zona, tipo_calidad, operador_cc, tipo_de_errores, conteo_de_errores
        FROM registro
        WHERE usuario = '{usuario}'
          AND fecha BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
        ORDER BY fecha DESC;
    """

    df = pd.read_sql(query, con)

    st.subheader("Reportes encontrados")
    st.dataframe(df, use_container_width=True)

    if df.empty:
        st.info("No tienes reportes en el rango seleccionado.")
        return

    # ----- Seleccionar ID para corregir o eliminar ----- #
    st.subheader("Solicitar corrección o eliminación")

    id_reporte = st.selectbox(
        "Selecciona el ID del reporte",
        df["id"].tolist()
    )

    tipo_correccion = st.radio(
        "Tipo de corrección:",
        ("Modificar valor", "Eliminar reporte")
    )

    nuevo_valor = None

    if tipo_correccion == "Modificar valor":
        columna = st.selectbox(
            "Selecciona la columna que deseas corregir",
            ["fecha", "proceso", "produccion", "horas", "estado", "observaciones"]
        )

        nuevo_valor = st.text_input("Ingresa el nuevo valor")

    # ----- Enviar solicitud ----- #
    if st.button("Enviar Solicitud"):

        cursor = con.cursor()

        marca = datetime.now(pytz.timezone("America/Guatemala")).strftime("%Y-%m-%d %H:%M:%S")

        if tipo_correccion == "Modificar valor":
            descripcion = f"Modificar columna '{columna}' por '{nuevo_valor}'"

        else:
            descripcion = "Solicitud de eliminación del reporte"

        insert_query = f"""
            INSERT INTO correcciones (usuario, nombre, tipo_correccion, id_asociado, fecha, estado)
            VALUES (%s, %s, %s, %s, %s, %s);
        """

        cursor.execute(insert_query, (
            usuario,
            nombre,
            descripcion,
            id_reporte,
            marca,
            "Pendiente"
        ))

        con.commit()

        st.success("Solicitud registrada correctamente 🎉")

        if tipo_correccion == "Modificar valor":
            st.info(f"Corrección solicitada: cambiar **{columna}** → **{nuevo_valor}**")
        else:
            st.info("Solicitud de eliminación registrada.")
