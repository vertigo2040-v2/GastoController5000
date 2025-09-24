import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
#streamlit run GastoWebSq.py 
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

# Cargar todos los gastos
def load_expenses():
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

# Cargar datos en session_state
if 'expenses_df' not in st.session_state: #comprobar si existe la 
    st.session_state.expenses_df = load_expenses()

# Categorías predefinidas
CATEGORIES = ["Consumo diario", "Ocio", "Transporte", "Salud", "Educación"]

# Título
st.title("📊 GASTOCONTROLLER5000")

# Formulario para agregar gasto
st.header("➕ Ingresar un nuevo gasto")
with st.form("expense_form"):
    col1, col2 = st.columns(2)
    with col1:
        product = st.text_input("Product", placeholder="Ej. Café, Gasolina...")
    with col2:
        category = st.selectbox("Categoria", options=CATEGORIES)

    col3, col4 = st.columns(2)
    with col3:
        amount = st.number_input("Valor(Q)", min_value=0.0, step=0.01, format="%.2f")
    with col4:
        date = st.date_input("Fecha", value=datetime.today())

    submitted = st.form_submit_button("💾 Guardar gasto")
    if submitted:
        if product and amount > 0:
            save_expense(product, category, amount, str(date))
            st.session_state.expenses_df = load_expenses()  # Recargar
            st.success("✅ Gasto guardado!")
        else:
            st.warning("⚠️ Por favor, complete el producto y el monto.")

st.markdown("---")

# Filtros de consulta
st.header("🔍 Filtrar y Analizar")

# Fechas por defecto: último mes
today = datetime.today()
default_start = (today - timedelta(days=30)).date()

col1, col2, col3 = st.columns(3)
with col1:
    start_date = st.date_input("Start Date", value=default_start)
with col2:
    end_date = st.date_input("End Date", value=today.date())
with col3:
    selected_category = st.selectbox("Category Filter", options=["Todas"] + CATEGORIES)

# Botón para aplicar filtro
if st.button("📊 Update Charts"):
    filtered_df = filter_expenses(str(start_date), str(end_date), selected_category if selected_category != "Todas" else None)
else:
    # Por defecto: último mes, todas las categorías
    filtered_df = filter_expenses(str(default_start), str(today.date()), None)

# Selector de periodo
period = st.radio("📈 Group by period:", ["Semanal", "Mensual", "Anual"], horizontal=True)

# Gráficos
st.subheader("📉 Expenses Over Time (Bar Chart)")
if not filtered_df.empty:
    grouped_df = group_by_period(filtered_df, period)
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    grouped_df.plot(kind='bar', stacked=True, ax=ax1)
    ax1.set_title(f"Expenses by {period}")
    ax1.set_ylabel("Amount ($)")
    ax1.legend(title="Category")
    plt.xticks(rotation=45)
    st.pyplot(fig1)
else:
    st.info("No data to display for selected filters.")

st.subheader("🥧 Expense Distribution by Category (Pie Chart)")
if not filtered_df.empty:
    category_totals = filtered_df.groupby('category')['amount'].sum()
    fig2, ax2 = plt.subplots(figsize=(6, 6))
    ax2.pie(category_totals, labels=category_totals.index, autopct='%1.1f%%', startangle=140)
    ax2.set_title("Category Distribution")
    ax2.axis('equal')
    st.pyplot(fig2)
else:
    st.info("No category data to display.")

st.markdown("---")

# Tabla de datos filtrados
st.header("📋 Filtered Expenses")
if not filtered_df.empty:
    st.dataframe(filtered_df[['product', 'category', 'amount', 'date']].reset_index(drop=True))
else:
    st.write("No expenses match the selected filters.")

# Estadísticas rápidas
if not filtered_df.empty:
    total = filtered_df['amount'].sum()
    avg = filtered_df['amount'].mean()
    st.metric("💰 Total Expenses", f"${total:,.2f}")
    st.metric("📈 Average per Expense", f"${avg:,.2f}")