import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =============================================================
# CONFIGURACIÓN INICIAL
# =============================================================

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("Dashboard de Mercado Gastronómico")

# Paleta de colores
st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #17324D;
    }
    div[data-testid="stMetric"] {
        background-color: #F0F5F9;
        border: 1px solid #D6E2EC;
        padding: 14px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.caption("Análisis de valoraciones, precios, servicios y competencia de restaurantes")

# =============================================================
# CARGA Y PREPARACIÓN
# =============================================================

# Este código es para cargar manualmente el archivo csv 
# una vez el programa iniciado
archivo = st.file_uploader(
    "Carga el dataset de restaurantes (CSV)",
    type=["csv"]
)

if archivo is None:
    st.info(
        "Carga el archivo CSV para calcular los indicadores "
        "y generar los gráficos del análisis."
    )
    st.stop()


# Carga y normalización de los datos

def cargar_datos(file_bytes):
    # Prueba codificaciones habituales de archivos CSV.
    df = None
    for encoding in ["utf-8", "utf-8-sig", "latin1"]:
        try:
            from io import BytesIO
            df = pd.read_csv(
                BytesIO(file_bytes),
                encoding=encoding,
                low_memory=False
            )
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        raise ValueError(
            "No fue posible interpretar la codificación del CSV."
        )

    # Normalizar nombres de columnas.
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

    # Corregir variantes frecuentes en los encabezados.
    aliases = {
        "Restaurant ID": "Restaurant ID",
        "Restaurant Name": "Restaurant Name",
        "Country Code": "Country Code",
        "Average cost for two": "Average cost for two",
        "Has Online delivery": "Has Online delivery",
        "Has Onlinne delivery": "Has Online delivery",
        "Aggregate rating": "Aggregate rating",
        "Price range": "Price range",
        "Rating text": "Rating text",
        "Rating color": "Rating color",
        "Locality Verbose": "Locality Verbose"
    }

    df = df.rename(columns=aliases)

    # Conversión de variables numéricas.
    numeric_cols = [
        "Restaurant ID",
        "Country Code",
        "Longitude",
        "Latitude",
        "Average cost for two",
        "Price range",
        "Aggregate rating",
        "Votes"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col], errors="coerce"
            )

    # Normalizar variables categóricas.
    categorical_cols = [
        "Restaurant Name", "City", "Country Code",
        "Address", "Locality", "Locality Verbose",
        "Cuisines", "Currency", "Has table booking",
        "Has Online delivery", "Is delivering now",
        "Switch to order menu", "Rating color", "Rating text"
    ]

    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()

    return df


try:
    df = cargar_datos(archivo.getvalue())
except Exception as error:
    st.error(f"Error al cargar el archivo: {error}")
    st.stop()

# Validar estructura mínima.
required_cols = [
    "Restaurant ID",
    "Aggregate rating",
    "Votes"
]

missing_required = [
    col for col in required_cols if col not in df.columns
]

if missing_required:
    st.error(
        "Faltan columnas necesarias para el análisis: "
        + ", ".join(missing_required)
    )
    st.stop()

# Muestra de los primeros 10 datos registrados
st.success(f"✅ Datos cargados: {len(df):,} registros")
st.dataframe(df.head(10))

# =============================================================
# FILTROS
# =============================================================

st.sidebar.header("Filtros de análisis")

filtered = df.copy()

if "Country Code" in filtered.columns:
    countries = sorted(
        filtered["Country Code"].dropna().unique().tolist(),
        key=str
    )
    selected_countries = st.sidebar.multiselect(
        "Código de país",
        countries,
        default=countries
    )
    filtered = filtered[
        filtered["Country Code"].isin(selected_countries)
    ]

if "City" in filtered.columns:
    cities = sorted(filtered["City"].dropna().unique().tolist())
    selected_cities = st.sidebar.multiselect(
        "Ciudad",
        cities,
        default=[]
    )
    if selected_cities:
        filtered = filtered[
            filtered["City"].isin(selected_cities)
        ]

if "Price range" in filtered.columns:
    price_values = filtered["Price range"].dropna()
    if not price_values.empty:
        min_price = int(price_values.min())
        max_price = int(price_values.max())

        price_filter = st.sidebar.slider(
            "Rango de precios",
            min_value=min_price,
            max_value=max_price,
            value=(min_price, max_price)
        )

        filtered = filtered[
            filtered["Price range"].between(
                price_filter[0], price_filter[1]
            )
        ]

if filtered.empty:
    st.warning("No hay registros para los filtros seleccionados.")
    st.stop()

# =============================================================
# KPIS CLAVE
# =============================================================

total = len(filtered)
unique_restaurants = (
    filtered["Restaurant ID"].nunique()
)

avg_rating = filtered["Aggregate rating"].mean()
avg_votes = filtered["Votes"].mean()

rating_valid = filtered["Aggregate rating"].dropna()
rating_coverage = (
    len(rating_valid) / total * 100 if total else 0
)

st.header("Indicadores clave")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Restaurantes Únicos", f"{unique_restaurants:,}")

col2.metric("Valoración Promedio", f"{avg_rating:.2f}/5" if pd.notna(avg_rating) else "Sin Datos")

col3.metric("Votos Promedio", f"{avg_votes:,.1f}" if pd.notna(avg_votes) else "Sin Datos")

col4.metric("Registros con Valoración", f"{rating_coverage:.1f}%")

st.caption(
    f"Registros analizados: {total:,}. "
    "Los indicadores corresponden a los filtros activos."
)

# =============================================================
# CONTEXTO
# =============================================================

# Paleta de colores
COLORS = {
    "primary": "#17324D",    # Azul oscuro
    "secondary": "#2878A5",  # Azul
    "positive": "#16A085",   # Turquesa
    "warning": "#E67E22",    # Naranja
    "negative": "#C0392B",   # Rojo
    "neutral": "#AAB7B8",    # Gris
    "background": "#F4F7FA"
}

PLOT_TEMPLATE = "plotly_white"

def estilo_grafico(fig, height=380):
    """Aplica un formato común a todos los gráficos."""
    fig.update_layout(
        template=PLOT_TEMPLATE,
        height=height,
        font=dict(
            family="Arial, sans-serif",
            size=12,
            color=COLORS["primary"]
        ),
        title_font=dict(size=17, color=COLORS["primary"]),
        margin=dict(l=20, r=20, t=65, b=30),
        legend_title_text="",
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        )
    )
    return fig


# Título, Descripción

st.header("1. Contexto: ¿Cómo es el mercado?")
st.markdown(
    "Explora la distribución de restaurantes, valoraciones, "
    "precios, ciudades y tipos de cocina."
)

col1, col2 = st.columns(2)

# ---------------------------------------------------------
# Gráfico 1: Distribución de valoraciones
# ---------------------------------------------------------
with col1:
    st.subheader("Distribución de valoraciones")

    ratings = filtered["Aggregate rating"].dropna()

    if not ratings.empty:
        fig = px.histogram(
            filtered.dropna(subset=["Aggregate rating"]),
            x="Aggregate rating",
            nbins=20,
            color_discrete_sequence=[COLORS["secondary"]],
            labels={
                "Aggregate rating": "Valoración",
                "Cantidad": "Cantidad de restaurantes"
            },
            title="Frecuencia de las valoraciones"
        )

        fig.update_traces(
            marker_line_color="white",
            marker_line_width=1,
            hovertemplate=(
                "Valoración: %{x}<br>"
                "Cantidad: %{y}<extra></extra>"
            )
        )

        fig.update_xaxes(range=[0, 5])
        st.plotly_chart(
            estilo_grafico(fig),
            use_container_width=True
        )
    else:
        st.info("No existen valoraciones disponibles.")

# ---------------------------------------------------------
# Gráfico 2: Distribución de rangos de precios
# ---------------------------------------------------------
with col2:
    st.subheader("Distribución de precios")

    if "Price range" in filtered.columns:
        price_data = filtered.dropna(subset=["Price range"])

        if not price_data.empty:
            price_counts = (
                price_data.groupby("Price range")
                .size()
                .reset_index(name="Restaurantes")
            )

            fig = px.bar(
                price_counts,
                x="Price range",
                y="Restaurantes",
                color="Restaurantes",
                color_continuous_scale=["#D6EAF8", COLORS["secondary"]],
                text="Restaurantes",
                title="Restaurantes por rango de precios",
                labels={
                    "Price range": "Rango de precios",
                    "Restaurantes": "Cantidad"
                }
            )

            fig.update_traces(textposition="outside")
            fig.update_layout(coloraxis_showscale=False)

            st.plotly_chart(
                estilo_grafico(fig),
                use_container_width=True
            )
        else:
            st.info("No existen datos de precios.")
    else:
        st.info("No se encontró la columna Price range.")

# ---------------------------------------------------------
# Gráfico 3: Ciudades con más restaurantes
# ---------------------------------------------------------
if "City" in filtered.columns:
    st.subheader("Principales ciudades por cantidad de restaurantes")

    top_cities = (
        filtered["City"]
        .dropna()
        .value_counts()
        .head(10)
        .sort_values()
        .rename_axis("Ciudad")
        .reset_index(name="Restaurantes")
    )

    if not top_cities.empty:
        fig = px.bar(
            top_cities,
            x="Restaurantes",
            y="Ciudad",
            orientation="h",
            text="Restaurantes",
            color="Restaurantes",
            color_continuous_scale=["#D6EAF8", COLORS["primary"]],
            title="Top 10 ciudades",
            labels={"Restaurantes": "Cantidad"}
        )

        fig.update_traces(textposition="outside")
        fig.update_layout(
            yaxis={"categoryorder": "array",
                   "categoryarray": top_cities["Ciudad"]}
        )
        fig.update_layout(coloraxis_showscale=False)

        st.plotly_chart(
            estilo_grafico(fig, height=450),
            use_container_width=True
        )

# ---------------------------------------------------------
# Gráfico 4: Tipos de cocina más frecuentes
# ---------------------------------------------------------
if "Cuisines" in filtered.columns:
    st.subheader("Tipos de cocina más frecuentes")

    cuisine_counts = (
        filtered["Cuisines"]
        .dropna()
        .str.split(",")
        .explode()
        .str.strip()
    )

    cuisine_counts = cuisine_counts[
        cuisine_counts.ne("")
    ]

    top_cuisines = (
        cuisine_counts.value_counts()
        .head(10)
        .sort_values()
        .rename_axis("Tipo de cocina")
        .reset_index(name="Apariciones")
    )

    if not top_cuisines.empty:
        fig = px.bar(
            top_cuisines,
            x="Apariciones",
            y="Tipo de cocina",
            orientation="h",
            text="Apariciones",
            color_discrete_sequence=[COLORS["positive"]],
            title="Top 10 tipos de cocina",
            labels={"Apariciones": "Frecuencia"}
        )

        fig.update_traces(textposition="outside")

        st.plotly_chart(
            estilo_grafico(fig, height=450),
            use_container_width=True
        )

# =============================================================
# CONFLICTO
# =============================================================

st.header(
    "2. Conflicto: ¿Qué factores se relacionan con el desempeño?"
)

st.markdown(
    "Identificar posibles asociaciones entre precios, reputación "
    "y disponibilidad de servicios. Las asociaciones no implican "
    "causalidad."
)

col1, col2 = st.columns(2)

# ---------------------------------------------------------
# Gráfico 1: Precio frente a valoración
# ---------------------------------------------------------
with col1:
    st.subheader("Costo para dos personas vs. valoración")

    price_col = "Average Cost for two"
    rating_col = "Aggregate rating"

    if price_col in filtered.columns:
        scatter_data = filtered[
            [price_col, rating_col]
        ].dropna()

        if not scatter_data.empty:
            fig = px.scatter(
                scatter_data,
                x=price_col,
                y=rating_col,
                opacity=0.55,
                color=rating_col,
                color_continuous_scale=[
                    COLORS["warning"],
                    "#F1C40F",
                    COLORS["positive"]
                ],
                hover_data={
                    price_col: ":,0f",
                    rating_col: ":.2f"
                },
                title="¿Los restaurantes más caros tienen mejor valoración?",
                labels={
                    price_col: "Costo para dos personas",
                    rating_col: "Valoración promedio"
                }
            )

            fig.update_yaxes(range=[0, 5])
            fig.update_layout(coloraxis_colorbar_title="Rating")

            st.plotly_chart(
                estilo_grafico(fig),
                use_container_width=True
            )
        else:
            st.info("No hay suficientes datos para comparar.")
    else:
        st.info("No existe la variable de costo.")

# ---------------------------------------------------------
# Gráfico 2: Votos frente a valoración
# ---------------------------------------------------------
with col2:
    st.subheader("Cantidad de votos vs. valoración")

    vote_col = "Votes"

    scatter_data = filtered[
        [vote_col, rating_col]
    ].dropna()

    if not scatter_data.empty:
        fig = px.scatter(
            scatter_data,
            x=vote_col,
            y=rating_col,
            opacity=0.55,
            color_discrete_sequence=[COLORS["secondary"]],
            hover_data={
                vote_col: ":,",
                rating_col: ":.2f"
            },
            title="Participación de usuarios y reputación",
            labels={
                vote_col: "Cantidad de votos",
                rating_col: "Valoración promedio"
            }
        )

        fig.update_yaxes(range=[0, 5])

        st.plotly_chart(
            estilo_grafico(fig),
            use_container_width=True
        )
    else:
        st.info("No hay datos suficientes de votos y valoraciones.")

# ---------------------------------------------------------
# Gráfico 3: Matriz de correlación
# ---------------------------------------------------------
st.subheader("Matriz de correlación")

numeric_data = filtered.select_dtypes(include="number").copy()

# Los identificadores no representan magnitudes de negocio.
numeric_data = numeric_data.drop(
    columns=["Restaurant ID", "Country Code"],
    errors="ignore"
)

if numeric_data.shape[1] >= 2:
    corr = numeric_data.corr(
        method="pearson",
        min_periods=3
    )

    fig = px.imshow(
        corr,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale=[
            COLORS["negative"],
            "#FFFFFF",
            COLORS["positive"]
        ],
        zmin=-1,
        zmax=1,
        origin="lower",
        title="Correlaciones entre variables numéricas",
        labels={
            "x": "Variable",
            "y": "Variable",
            "color": "Correlación"
        }
    )

    st.plotly_chart(
        estilo_grafico(fig, height=550),
        use_container_width=True
    )

    # Asociaciones con Aggregate rating.
    if rating_col in corr.columns:
        rating_corr = (
            corr[rating_col]
            .drop(labels=[rating_col], errors="ignore")
            .dropna()
        )

        if not rating_corr.empty:
            rating_corr = rating_corr.reindex(
                rating_corr.abs()
                .sort_values(ascending=True)
                .index
            )

            colors = [
                COLORS["positive"] if value >= 0
                else COLORS["negative"]
                for value in rating_corr.values
            ]

            fig = go.Figure(
                go.Bar(
                    x=rating_corr.values,
                    y=rating_corr.index,
                    orientation="h",
                    marker_color=colors,
                    text=[f"{v:.2f}" for v in rating_corr.values],
                    textposition="outside",
                    hovertemplate=(
                        "Variable: %{y}<br>"
                        "Correlación: %{x:.3f}<extra></extra>"
                    )
                )
            )

            fig.update_layout(
                title="Variables asociadas con la valoración",
                xaxis_title="Correlación de Pearson",
                yaxis_title="Variable",
                xaxis=dict(range=[-1.15, 1.15]),
                showlegend=False
            )

            st.plotly_chart(
                estilo_grafico(fig, height=400),
                use_container_width=True
            )
else:
    st.info("Se necesitan al menos dos variables numéricas.")

# ---------------------------------------------------------
# Gráfico 4: Servicios digitales y valoración
# ---------------------------------------------------------
st.subheader("Servicios digitales y valoración")

service_cols = [
    "Has table booking",
    "Has Online delivery",
    "Is delivering now"
]

available_services = [
    col for col in service_cols
    if col in filtered.columns
]

service_data = []

for col in available_services:
    temp = filtered[[col, rating_col]].dropna()

    if not temp.empty:
        grouped = temp.groupby(col)[rating_col].agg(
            ["mean", "count"]
        ).reset_index()

        for _, row in grouped.iterrows():
            service_data.append({
                "Servicio": col,
                "Disponibilidad": str(row[col]),
                "Valoración promedio": row["mean"],
                "Cantidad de restaurantes": int(row["count"])
            })

if service_data:
    service_df = pd.DataFrame(service_data)

    fig = px.bar(
        service_df,
        x="Servicio",
        y="Valoración promedio",
        color="Disponibilidad",
        barmode="group",
        text_auto=".2f",
        hover_data=["Cantidad de restaurantes"],
        title="Valoración promedio según disponibilidad de servicios",
        color_discrete_sequence=[
            COLORS["secondary"],
            COLORS["positive"],
            COLORS["warning"]
        ],
        labels={
            "Valoración promedio": "Valoración promedio (0–5)"
        }
    )

    fig.update_yaxes(range=[0, 5])

    st.plotly_chart(
        estilo_grafico(fig, height=450),
        use_container_width=True
    )

    st.caption(
        "Las diferencias observadas pueden depender del país, "
        "tipo de cocina, precio y tamaño de muestra."
    )
else:
    st.info("No hay datos suficientes para comparar los servicios.")

# =============================================================
# RESOLUCIÓN
# =============================================================
st.header("3. Resolución: ¿Qué decisiones tomar?")

# ---------------------------------------------------------
# Gráfico 1: Valoración por rango de precios
# ---------------------------------------------------------
st.subheader("Segmentos de precios con mejores valoraciones")

if (
    "Price range" in filtered.columns
    and rating_col in filtered.columns
):
    price_analysis = (
        filtered.dropna(subset=["Price range", rating_col])
        .groupby("Price range")
        .agg(
            Valoracion_promedio=(rating_col, "mean"),
            Cantidad=(rating_col, "count"),
            Mediana=(rating_col, "median")
        )
        .reset_index()
        .sort_values("Price range")
    )

    # Evitar recomendar segmentos con muestras muy pequeñas.
    MIN_SAMPLE = 5

    price_analysis["Segmento evaluable"] = (
        price_analysis["Cantidad"] >= MIN_SAMPLE
    )

    if not price_analysis.empty:
        fig = px.bar(
            price_analysis,
            x="Price range",
            y="Valoracion_promedio",
            text="Valoracion_promedio",
            color="Valoracion_promedio",
            color_continuous_scale=[
                COLORS["warning"],
                "#F1C40F",
                COLORS["positive"]
            ],
            hover_data=[
                "Cantidad",
                "Mediana",
                "Segmento evaluable"
            ],
            title="Valoración promedio por rango de precios",
            labels={
                "Price range": "Rango de precios",
                "Valoracion_promedio": "Valoración promedio",
                "Cantidad": "Restaurantes evaluados",
                "Mediana": "Valoración mediana"
            }
        )

        fig.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside"
        )
        fig.update_yaxes(range=[0, 5])
        fig.update_layout(coloraxis_showscale=False)

        st.plotly_chart(
            estilo_grafico(fig),
            use_container_width=True
        )

        eligible = price_analysis[
            price_analysis["Segmento evaluable"]
        ]

        if not eligible.empty:
            best = eligible.loc[
                eligible["Valoracion_promedio"].idxmax()
            ]

            st.success(
                f"Segmento a investigar: rango de precios "
                f"{best['Price range']}, con valoración promedio "
                f"{best['Valoracion_promedio']:.2f}/5 y "
                f"{int(best['Cantidad'])} restaurantes evaluados."
            )

            st.caption(
                "Una mejor valoración no demuestra mayor rentabilidad. "
                "Para evaluar la rentabilidad se necesitan datos de "
                "ventas, costos y márgenes."
            )
        else:
            st.warning(
                "Ningún segmento alcanza el mínimo de "
                f"{MIN_SAMPLE} restaurantes con valoración."
            )
    else:
        st.info("No existen registros suficientes por rango de precios.")
else:
    st.info("Faltan las columnas de precios o valoraciones.")

# ---------------------------------------------------------
# Gráfico 2: Oportunidades en servicios digitales
# ---------------------------------------------------------
st.subheader("Diferencias observadas entre servicios digitales")

if service_data:
    service_df = pd.DataFrame(service_data)

    # Calcular diferencia entre categorías dentro de cada servicio.
    service_gaps = (
        service_df.groupby("Servicio")
        .agg(
            Diferencia=(
                "Valoración promedio",
                lambda s: s.max() - s.min()
            ),
            Muestra_total=("Cantidad de restaurantes", "sum"),
            Categorias=("Disponibilidad", "nunique")
        )
        .reset_index()
    )

    service_gaps = service_gaps[
        service_gaps["Categorias"] >= 2
    ].sort_values("Diferencia", ascending=True)

    if not service_gaps.empty:
        fig = px.bar(
            service_gaps,
            x="Diferencia",
            y="Servicio",
            orientation="h",
            text="Diferencia",
            color="Diferencia",
            color_continuous_scale=[
                "#D6EAF8",
                COLORS["secondary"],
                COLORS["warning"]
            ],
            hover_data=[
                "Muestra_total",
                "Categorias"
            ],
            title="Brecha de valoración entre categorías de servicio",
            labels={
                "Diferencia": "Diferencia de valoración (puntos)",
                "Muestra_total": "Registros agrupados",
                "Categorias": "Categorías comparadas"
            }
        )

        fig.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside"
        )
        fig.update_layout(coloraxis_showscale=False)

        st.plotly_chart(
            estilo_grafico(fig, height=380),
            use_container_width=True
        )

        strongest = service_gaps.iloc[-1]

        st.info(
            f"Área para investigar: {strongest['Servicio']}. "
            f"La diferencia observada es de "
            f"{strongest['Diferencia']:.2f} puntos. "
            "No implica que el servicio cause esa diferencia."
        )

        st.caption(
            "La brecha representa la diferencia entre la categoría "
            "con mayor promedio y la de menor promedio. Deben "
            "examinarse los tamaños de muestra y las variables "
            "de confusión antes de tomar decisiones."
        )
    else:
        st.info(
            "Se requieren al menos dos categorías comparables "
            "por servicio."
        )
else:
    st.info("No hay resultados suficientes para evaluar servicios.")



# ---------------------------------------------------------
# Tabla de resultados para exportar
# ---------------------------------------------------------
st.subheader("Resumen para la toma de decisiones")

if "Price range" in filtered.columns:
    summary = (
        filtered.groupby("Price range")
        .agg(
            Restaurantes=("Restaurant ID", "nunique"),
            Valoracion_media=(rating_col, "mean"),
            Votos_medios=("Votes", "mean")
        )
        .reset_index()
    )

    st.dataframe(
        summary.round(2),
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Descargar resumen de segmentos",
        data=summary.to_csv(index=False).encode("utf-8-sig"),
        file_name="resumen_segmentos.csv",
        mime="text/csv"
    )
