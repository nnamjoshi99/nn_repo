import pandas as pd
import streamlit as st

# Sample data for multiple sheets
data1 = {
    'Name': ['Alice', 'Bob', 'Charlie'],
    'Age': [25, 30, 35],
    'City': ['New York', 'Los Angeles', 'Chicago']
}

data2 = {
    'Product': ['Laptop', 'Tablet', 'Smartphone'],
    'Price': [1000, 500, 800],
    'Stock': [50, 150, 200]
}

# Create DataFrames
df1 = pd.DataFrame(data1)

df2 = pd.DataFrame(data2)

# hello.py
st.write("Content of DataFrame 1: ")
st.dataframe(df1)

st.write("Content of DataFrame 2: ")
st.dataframe(df2)