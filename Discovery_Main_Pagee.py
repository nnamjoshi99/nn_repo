import pandas as pd
import sqlalchemy as sal
from sqlalchemy import create_engine
import streamlit as st
import networkx as nx
from pyvis.network import Network
import plotly.express as px
from streamlit_navigation_bar import st_navbar
import xlsxwriter
import sqlserverconnection as conn
import sqlserver as ss


# Main function
def main():

    # st.set_page_config(page_title="[Database Data Discovery]",layout='wide')

    # Setting up Background
    page_bg_img = f"""
        <style>
        [data-testid="stAppViewContainer"] > .main {{
        background-image: linear-gradient(to right, #CAE9F6, #44B3E0);
        background-size: cover;
        background-position: center center;
        background-repeat: no-repeat;
        background-attachment: local;
        }}
        [data-testid="stHeader"] {{
        background: rgba(0,0,0,0);
        }}
        </style>
        """

    # CSS for rendering Dataframes
    css = """
     <style>
     .dataframe-container {
        height: 300px;  /* Adjust the height as needed */
        overflow-y: scroll;
        position: relative;
        background-color: #DBF0F9;
      }

     .dataframe-container thead th {
        position: sticky;
        top: 0;
        z-index: 1;
     }

     table {
        font-family: Arial, sans-serif;  /* Font family */
        font-size: 14px;  /* Font size */
        border-collapse: collapse;
        width: 100%;
           }

     th, td {
        border: 1px solid #000000;
        text-align: left;
        padding: 8px;
           }

     th {
        background-color: #1F52B7;
        color: white;
        }

     td {
        color: black;
        }
     </style>
     """

    # Custom CSS to set the width of the database selectbox
    selectbox_css = """
    <style>
    div[data-baseweb="select"] > div {
        width: 300px;  /* Adjust the width as needed */
    }
    </style>
    """
    pages = ["Summary", "Database", "Table-View", "User Info", "FK and Lineage"]

    styles = {
        "nav": {
            "background-color": "#F8DFA2",
        },
        "div": {
            "max-width": "40rem",
        },
        "span": {
            "border-radius": "0.5rem",
            "color": "#143576",
            "margin": "0 0.145rem",
            "padding": "0.4375rem 0.625rem",
        },
        "active": {
            "background-color": "#DBF0F9",
        },
        "hover": {
            "background-color": "rgba(255, 255, 255, 0.35)",
        },
    }

    # Function to calculate the width of the column
    def calculate_width(series):
        return max(series.astype(str).map(len).max(), len(series.name)) + 2

    page = st_navbar(pages, styles=styles)

    # Render Page Background in the Streamlit app
    st.markdown(page_bg_img, unsafe_allow_html=True)

    # Dataframe rendering using CSS in the Streamlit app
    st.markdown(css, unsafe_allow_html=True)

    if "credentials" not in st.session_state:
        conn.get_credentials()

    if "credentials" in st.session_state:
        user, password, host, port, database = st.session_state["credentials"]
        engine = conn.connect_db(user, password, host, port, database)

        if engine is not None:

            # st.subheader("Database Data Discovery", divider="blue")
            st.sidebar.title(":blue[Database Data Discovery]")

            # Get object stats for selected database
            query = ss.dbsize
            dbsize = pd.read_sql(query, engine)

            query = ss.Objcount
            Objcount = pd.read_sql(query, engine)

            query = ss.indexdf
            indexdf = pd.read_sql(query, engine)

            query = ss.tblSize
            tblSize = pd.read_sql(query, engine)

            query = ss.tblComplexity
            tblComplexity = pd.read_sql(query, engine)

            query = ss.viewComplexity
            viewComplexity = pd.read_sql(query, engine)

            query = ss.complexityDF
            complexityDF = pd.read_sql(query, engine)

            query = ss.tblComplexitydf
            tblComplexitydf = pd.read_sql(query, engine)

            query = ss.bigTblDF
            bigTblDF = pd.read_sql(query, engine)

            query = ss.objCountdf
            objCountdf = pd.read_sql(query, engine)

            query = ss.colDTdf
            colDTdf = pd.read_sql(query, engine)

            query = ss.indInfodf
            indInfodf = pd.read_sql(query, engine)

            query = ss.schemadf
            schemadf = pd.read_sql(query, engine)

            query = ss.users
            users = pd.read_sql(query, engine)

            query = ss.userRoledf
            userRoledf = pd.read_sql(query, engine)

            query = ss.userDtlDF
            userDtlDF = pd.read_sql(query, engine)

            query = ss.usergraphdf
            usergraphdf = pd.read_sql(query, engine)

            query = ss.userLoginDF
            userLoginDF = pd.read_sql(query, engine)

            query = ss.foreignkeydf
            foreignkeydf = pd.read_sql(query, engine)

            query = ss.lineageDF
            lineageDF = pd.read_sql(query, engine)

        # List of DataFrames and corresponding sheet names
        dataframes = [
            dbsize,
            Objcount,
            indexdf,
            tblSize,
            tblComplexity,
            viewComplexity,
            complexityDF,
            tblComplexitydf,
            bigTblDF,
            objCountdf,
            schemadf,
            colDTdf,
            indInfodf,
            users,
            userDtlDF,
            userRoledf,
            userLoginDF,
            usergraphdf,
            foreignkeydf,
            lineageDF,
        ]
        sheet_names = [
            "DB_Size",
            "Object_Count",
            "Index_Count",
            "Table_Size",
            "Sch_Tbl_Complex",
            "View_Complexity",
            "Complexity",
            "Tbl_Complex_count",
            "Top_Big_Tbls",
            "DB_Obj_count",
            "DB_Schemas",
            "Column_Datatype",
            "Index_dtl",
            "User_Info",
            "User_Details",
            "User_Role",
            "User_LoginInfo",
            "User_pie",
            "Foreignkey_Details",
            "Lineage_Details",
        ]

        out_path = r"D:\vs_code_folder\.vscode\Discovery\db_output.xlsx"

        # Writing data frame to excel file ,mode='a',if_sheet_exists='replace'
        # Write to Excel with formatting
        with pd.ExcelWriter(out_path, engine="xlsxwriter") as writer:
            for df, sheet_name in zip(dataframes, sheet_names):
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                worksheet = writer.sheets[sheet_name]
                workbook = writer.book

                # Define formats
                header_format = workbook.add_format(
                    {
                        "bold": True,
                        "text_wrap": True,
                        "valign": "top",
                        "fg_color": "#D7E4BC",
                        "border": 1,
                    }
                )
                cell_format = workbook.add_format({"border": 1})

                # Apply header format and set column width
                for col_num, value in enumerate(df.columns.values):
                    column_len = calculate_width(df.iloc[:, col_num])
                    worksheet.set_column(col_num, col_num, column_len)
                    worksheet.write(0, col_num, value, header_format)

                # Apply cell format
                for row_num in range(1, len(df) + 1):
                    for col_num in range(len(df.columns)):
                        worksheet.write(
                            row_num, col_num, df.iloc[row_num - 1, col_num], cell_format
                        )

        st.sidebar.subheader(f"Stats for Database: :blue[{database}]")

        if page == "Summary":

            # st.subheader(f"Stats for Database: :blue[{selected_db}]", divider="blue")

            # Create two columns
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(":blue[Size of the Database]", divider="blue")
                st.markdown(
                    '<div id="table-container" style="width: fit-content; overflow-y: auto; background-color:#DBF0F9">'
                    + dbsize.to_html(index=False)
                    + "</div>",
                    unsafe_allow_html=True,
                )

            with col2:
                st.subheader(":blue[Database Schema Details]", divider="blue")
                st.markdown(
                    '<div id="table-container" style="width: fit-content; overflow-y: auto; background-color:#DBF0F9">'
                    + schemadf.to_html(index=False)
                    + "</div>",
                    unsafe_allow_html=True,
                )

            # Create two columns
            col3, col4 = st.columns(2)
            with col3:

                # Bar Chart Table Complexity
                st.subheader(":blue[Table Complexity]", divider="blue")
                st.bar_chart(data=tblComplexitydf, x="Complexity Level", y="Count")

                # Create the pie chart
                st.subheader(":blue[Object Complexity %]", divider="blue")
                fig = px.pie(objCountdf, values="Count", names="Category")
                # Update layout dimensions
                fig.update_layout(
                    width=400, height=300, margin=dict(l=20, r=20, t=20, b=20)
                )  # Width, Height in pixels
                # Display the chart in Streamlit
                st.plotly_chart(fig)

                # Bar Chart Users
                st.subheader(":blue[User Info]", divider="blue")
                st.bar_chart(data=usergraphdf, x="User Type", y="Count")

            with col4:

                # Bar Chart Types of Indexes
                st.subheader(":blue[Types of Indexes]", divider="blue")
                st.bar_chart(data=indexdf, x="Index Type", y="Count")

                # Bar Chart Object Count
                st.subheader(":blue[DB Object Count]", divider="blue")
                st.bar_chart(data=Objcount, x="ObjDescription", y="ObjCount")

            # Data Lineage Graph
            st.subheader(":blue[Data Lineage Graph]", divider="blue")

            # Create a directed graph
            G = nx.DiGraph()

            # Add nodes and edges to the graph
            for _, row in lineageDF.iterrows():
                if pd.notna(row["referenced_table_name"]):
                    G.add_edge(
                        row["table_name"],
                        row["referenced_table_name"],
                        label=row["foreign_key_name"],
                    )

            # Create a PyVis network
            net = Network(notebook=True, height="750px", width="100%", directed=True)

            # Add nodes and edges from the NetworkX graph
            net.from_nx(G)

            # Save and display the network
            net.save_graph("lineage_graph.html")
            st.components.v1.html(open("lineage_graph.html", "r").read(), height=750)

        elif page == "Database":
            # st.subheader(f"Stats for Database: :blue[{selected_db}]")

            st.subheader(":blue[Size of the Database]", divider="blue")
            # st.markdown(dbsize.to_html(index=False), unsafe_allow_html=True)
            st.markdown(
                '<div id="table-container" style="width: fit-content; overflow-y: auto; background-color:#DBF0F9">'
                + dbsize.to_html(index=False)
                + "</div>",
                unsafe_allow_html=True,
            )

            st.subheader(
                ":blue[Count of various objects in the Database]", divider="blue"
            )
            st.markdown(
                '<div class="dataframe-container">'
                + Objcount.to_html(index=False)
                + "</div>",
                unsafe_allow_html=True,
            )

            st.subheader(":blue[Complexity Metrics at Database level]", divider="blue")
            st.markdown(
                '<div class="dataframe-container">'
                + complexityDF.to_html(index=False)
                + "</div>",
                unsafe_allow_html=True,
            )

            st.subheader(
                ":blue[Column Data Type Info at Database level]", divider="blue"
            )
            st.markdown(
                '<div class="dataframe-container">'
                + colDTdf.to_html(index=False)
                + "</div>",
                unsafe_allow_html=True,
            )

            st.subheader(":blue[Index Details at Database level]", divider="blue")
            st.markdown(
                '<div class="dataframe-container">'
                + indInfodf.to_html(index=False)
                + "</div>",
                unsafe_allow_html=True,
            )

            st.subheader(":blue[Index Information]", divider="blue")
            st.markdown(
                '<div id="table-container" style="width: fit-content; overflow-y: auto; background-color:#DBF0F9">'
                + indexdf.to_html(index=False)
                + "</div>",
                unsafe_allow_html=True,
            )

            st.subheader(":blue[Top 7 Big Tables by Size]", divider="blue")
            st.markdown(
                '<div class="dataframe-container">'
                + bigTblDF.to_html(index=False)
                + "</div>",
                unsafe_allow_html=True,
            )

            st.subheader(":blue[Schema wise Table Row count and Size]", divider="blue")
            st.markdown(
                '<div class="dataframe-container">'
                + tblSize.to_html(index=False)
                + "</div>",
                unsafe_allow_html=True,
            )

        elif page == "Table-View":
            st.subheader(":blue[Table Complexity Count]", divider="blue")
            st.markdown(
                '<div class="dataframe-container">'
                + tblComplexity.to_html(index=False)
                + "</div>",
                unsafe_allow_html=True,
            )

            st.subheader(":blue[View Complexity Count]", divider="blue")
            st.markdown(
                '<div class="dataframe-container">'
                + viewComplexity.to_html(index=False)
                + "</div>",
                unsafe_allow_html=True,
            )

        elif page == "User Info":
            st.subheader(":blue[Database User Info]", divider="blue")
            st.markdown(
                '<div id="table-container" style="width: fit-content; overflow-y: auto; background-color:#DBF0F9">'
                + users.to_html(index=False)
                + "</div>",
                unsafe_allow_html=True,
            )

            st.subheader(":blue[Database User Details]", divider="blue")
            st.markdown(
                '<div id="table-container" style="max-height: 300px; width: fit-content; overflow-y: scroll; background-color:#DBF0F9">'
                + userDtlDF.to_html(index=False)
                + "</div>",
                unsafe_allow_html=True,
            )

            st.subheader(":blue[User Role Mapping]", divider="blue")
            st.markdown(
                '<div class="dataframe-container">'
                + userRoledf.to_html(index=False)
                + "</div>",
                unsafe_allow_html=True,
            )

            st.subheader(":blue[Database User Info]", divider="blue")
            st.markdown(
                '<div class="dataframe-container">'
                + userLoginDF.to_html(index=False)
                + "</div>",
                unsafe_allow_html=True,
            )

        elif page == "FK and Lineage":
            st.subheader(":blue[Schema wise Foreign Key Info]", divider="blue")
            st.markdown(
                '<div class="dataframe-container">'
                + foreignkeydf.to_html(index=False)
                + "</div>",
                unsafe_allow_html=True,
            )

            st.subheader(":blue[Table Lineage Details]", divider="blue")
            st.markdown(
                '<div class="dataframe-container">'
                + lineageDF.to_html(index=False)
                + "</div>",
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
