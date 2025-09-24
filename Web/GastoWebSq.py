import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Nombre de la base de datos
DB_FILE = 'expenses.db'

# Inicializar base de datos
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Cargar todos los gastos (sin filtros)
def load_all_expenses():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM expenses", conn)
    conn.close()
    return df

# Guardar un nuevo gasto
def save_expense(product, category, amount, date):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenses (product, category, amount, date)
        VALUES (?, ?, ?, ?)
    ''', (product, category, amount, date))
    conn.commit()
    conn.close()

# Filtrar gastos por fechas y categoría
def filter_expenses(start_date, end_date, category=None):
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT * FROM expenses WHERE date BETWEEN ? AND ?"
    params = [start_date, end_date]
    if category and category != "Todas":
        query += " AND category = ?"
        params.append(category)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# Agrupar gastos por periodo (semanal, mensual, anual)
def group_by_period(df, period='Mensual'):
    df['date'] = pd.to_datetime(df['date'])
    if period == 'Semanal':
        df['period'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time)
    elif period == 'Mensual':
        df['period'] = df['date'].dt.to_period('M').apply(lambda r: r.start_time)
    elif period == 'Anual':
        df['period'] = df['date'].dt.to_period('Y').apply(lambda r: r.start_time)
    else:
        df['period'] = df['date']  # Diario

    grouped = df.groupby(['period', 'category'])['amount'].sum().unstack(fill_value=0)
    return grouped

# Inicializar DB
init_db()

# Cargar todos los gastos una vez (para gráfica global)
all_expenses_df = load_all_expenses()

# Categorías predefinidas
CATEGORIES = ["Consumo diario", "Ocio", "Transporte", "Salud", "Educación"]

# Título
st.title("📊 GASTOCONTROLLER5000")

# Formulario para agregar gasto
st.header("➕ Agregar Nuevo Gasto")
with st.form("Formulario de Gasto"):
    col1, col2 = st.columns(2)
    with col1:
        product = st.text_input("Producto", placeholder="Ej. Café, Gasolina...")
    with col2:
        category = st.selectbox("Categoría", options=CATEGORIES)

    col3, col4 = st.columns(2)
    with col3:
        amount = st.number_input("Monto", min_value=0.0, step=0.01, format="%.2f")
    with col4:
        date = st.date_input("Fecha", value=datetime.today())

    submitted = st.form_submit_button("💾 Guardar")
    if submitted:
        if product and amount > 0:
            save_expense(product, category, amount, str(date))
            # Recargar datos globales después de guardar
            all_expenses_df = load_all_expenses()
            st.success("✅ Gasto guardado!")
        else:
            st.warning("⚠️ Por favor, complete el producto y el monto.")

st.markdown("---")

# 🥧 Gráfica de pastel: TOTAL DE TODOS LOS TIEMPOS (sin filtros)
st.subheader("🥧 Distribución Total de Gastos por Categoría")
if not all_expenses_df.empty:
    category_totals = all_expenses_df.groupby('category')['amount'].sum()
    fig_pie, ax_pie = plt.subplots(figsize=(6, 6))
    ax_pie.pie(category_totals, labels=category_totals.index, autopct='%1.1f%%', startangle=140)
    ax_pie.set_title("Distribución Global (Todo el historial)")
    ax_pie.axis('equal')
    st.pyplot(fig_pie)
else:
    st.info("No hay datos históricos para mostrar.")

st.markdown("---")

# 🔍 Filtros y análisis temporal (solo aquí usamos filtros)
st.header("🔍 Análisis Temporal (por fechas)")

# Fechas por defecto: último mes
today = datetime.today()
default_start = (today - timedelta(days=30)).date()

col1, col2, col3 = st.columns(3)
with col1:
    start_date = st.date_input("Fecha de inicio", value=default_start)
with col2:
    end_date = st.date_input("Fecha de fin", value=today.date())
with col3:
    selected_category = st.selectbox("Filtro de categoría", options=["Todas"] + CATEGORIES)

# Botón para aplicar filtro
if st.button("📊 Actualizar Gráficos Temporales"):
    filtered_df = filter_expenses(str(start_date), str(end_date), selected_category if selected_category != "Todas" else None)
else:
    # Por defecto: último mes, todas las categorías
    filtered_df = filter_expenses(str(default_start), str(today.date()), None)

# Selector de periodo
period = st.radio("📈 Agrupar por periodo:", ["Semanal", "Mensual", "Anual"], horizontal=True)

# Gráfico de barras temporal
st.subheader("📉 Gastos a lo largo del tiempo (Gráfico de Barras)")
if not filtered_df.empty:
    grouped_df = group_by_period(filtered_df, period)
    fig_bar, ax_bar = plt.subplots(figsize=(10, 5))
    grouped_df.plot(kind='bar', stacked=True, ax=ax_bar)
    ax_bar.set_title(f"Gastos por {period} (Filtrado)")
    ax_bar.set_ylabel("Monto (Q)")
    ax_bar.legend(title="Categoría")
    plt.xticks(rotation=45)
    st.pyplot(fig_bar)
else:
    st.info("No hay datos para mostrar con los filtros seleccionados.")

# Tabla y métricas del análisis temporal
st.header("📋 Gastos Filtrados (Análisis Temporal)")
if not filtered_df.empty:
    st.dataframe(filtered_df[['product', 'category', 'amount', 'date']].reset_index(drop=True))
    total = filtered_df['amount'].sum()
    avg = filtered_df['amount'].mean()
    st.metric("💰 Total Gastos (Filtrado)", f"Q{total:,.2f}")
    st.metric("📈 Promedio por Gasto", f"Q{avg:,.2f}")
else:
    st.write("No hay gastos que coincidan con los filtros seleccionados.")