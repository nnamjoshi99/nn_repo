import pandas as pd
import streamlit as st
import sqlalchemy as sal
from sqlalchemy import create_engine
#import xlsxwriter
#import datetime

# Function to get user inputs
def get_credentials():
    st.title("Database Connection")
    user = st.text_input("Enter your Username")
    password = st.text_input("Enter your Password", type="password")
    host = st.text_input("Enter your Host")
    port = st.text_input("Enter Port number")
    database = st.text_input("Enter your Database Name")
    
    if st.button("Connect"):
        if user and password and host and port and database:
            st.session_state['credentials'] = (user, password, host, port, database)
        else:
            st.error("Please fill in all fields")

# Function to connect to the database and fetch data
def connect_db (user, password, host, port, database):
    try:
        engine = sal.create_engine(f'mssql+pyodbc://{user}:{password}@{host}:{port}/{database}?driver=ODBC Driver 17 for SQL Server&Encrypt=no')
        return engine
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# Main function
def main():
    if 'credentials' not in st.session_state:
        get_credentials()
    
    if 'credentials' in st.session_state:
        
        user, password, host, port, database = st.session_state['credentials']
        engine = connect_db(user, password, host, port, database)
        
        if engine is not None:
            
            query = """SELECT DB_NAME() AS "Database Name", sum(CAST( (size * 8.0/1024) AS DECIMAL(15,2) )) AS [Size] FROM sys.database_files"""
            dbsize = pd.read_sql(query, engine)
            st.write("Size of the database is: ")
            st.dataframe(dbsize)

if __name__ == "__main__":
    main() 
