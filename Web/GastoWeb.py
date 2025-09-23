import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
#Para iniciar le parte web
#streamlit run GastoWeb.py 
CSV_FILE = 'expenses.csv'

# Función para cargar gastos
def load_expenses():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        return df
    else:
        return pd.DataFrame(columns=['Product', 'Category', 'Amount', 'Date'])

# Función para guardar gastos
def save_expenses(df):
    df.to_csv(CSV_FILE, index=False)

# Función para actualizar gráfico
def update_pie_chart(df):
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    category_expenses = df.dropna(subset=['Amount']).groupby('Category')['Amount'].sum()

    fig, ax = plt.subplots(figsize=(6, 6))
    if not category_expenses.empty:
        ax.pie(category_expenses, labels=category_expenses.index, autopct='%1.1f%%', startangle=140)
        ax.set_title("Expense Distribution by Category")
        ax.axis('equal')
    else:
        ax.text(0, 0, "No expense data available", horizontalalignment='center', verticalalignment='center')
        ax.set_title("Expense Distribution by Category")
    st.pyplot(fig)

# Cargar datos iniciales
if 'expenses_df' not in st.session_state:
    st.session_state.expenses_df = load_expenses()

# Título de la app
st.title("📊 Expense Tracker Web App")

# Formulario para agregar gasto
st.header("➕ Add New Expense")

CATEGORIES = ["Consumo diario", "Ocio", "Transporte", "Salud", "Educación"]

with st.form("expense_form"):
    product = st.text_input("Product")
    category = st.selectbox("Category", options=CATEGORIES)
    amount = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f")
    date = st.date_input("Date")

    submitted = st.form_submit_button("Add Expense")

    if submitted:
        if product and amount > 0:
            new_expense = pd.DataFrame([{
                'Product': product,
                'Category': category,
                'Amount': amount,
                'Date': str(date)
            }])
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, new_expense], ignore_index=True)
            save_expenses(st.session_state.expenses_df)
            st.success("✅ Expense added successfully!")
        else:
            st.error("❌ Please fill in all fields correctly.")

# Mostrar gráfico actualizado
st.header("📈 Expense Distribution")
update_pie_chart(st.session_state.expenses_df)

# Mostrar tabla de datos (opcional)
st.header("📋 All Expenses")
st.dataframe(st.session_state.expenses_df)