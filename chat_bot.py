
import streamlit as st
import pandas as pd
import os
from langchain.agents import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain.sql_database import SQLDatabase
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.callbacks import StreamlitCallbackHandler
import sqlite3
from dotenv import load_dotenv
import openai

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Set page config
st.set_page_config(page_title="Data QA Assistant", layout="wide")

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'db_path' not in st.session_state:
    st.session_state.db_path = "temp_database.db"

def create_temp_db(df):
    """Create a temporary SQLite database from the DataFrame"""
    conn = sqlite3.connect(st.session_state.db_path)
    df.to_sql('data_table', conn, if_exists='replace', index=False)
    conn.close()

def load_data(file):
    """Load data from uploaded file"""
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    elif file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file)
    else:
        st.error("Unsupported file format")
        return None
    return df

def main():
    st.title("📊 Data QA Assistant")
    
    # Sidebar for OpenAI API key
    with st.sidebar:
        st.markdown("### Instructions")
        st.markdown("""
        1. Upload a CSV or Excel file
        2. Ask questions about your data in natural language
        3. Click 'Submit' to get your answer
        """)

    # File upload
    uploaded_file = st.file_uploader("Upload your data file (CSV or Excel)", type=['csv', 'xlsx', 'xls'])

    if uploaded_file is not None:
        with st.spinner("Loading data..."):
            st.session_state.df = load_data(uploaded_file)
            
        if st.session_state.df is not None:
            st.success("Data loaded successfully!")
            st.write("Preview of your data:")
            st.dataframe(st.session_state.df.head())
            
            # Create SQLite database
            create_temp_db(st.session_state.df)
            
            # Initialize LangChain components
            if OPENAI_API_KEY:
                try:
                    # Create database connection
                    db = SQLDatabase.from_uri(f"sqlite:///{st.session_state.db_path}")
                    
                    # Initialize OpenAI LLM
                    llm = ChatOpenAI(
                        temperature=0,
                        model_name="gpt-3.5-turbo",
                        openai_api_key=OPENAI_API_KEY
                    )
                    
                    # Create SQL toolkit and agent
                    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
                    
                    agent_executor = create_sql_agent(
                        llm=llm,
                        toolkit=toolkit,
                        verbose=True,
                        agent_type=AgentType.OPENAI_FUNCTIONS,
                    )
                    
                    # Question input with submit button
                    st.markdown("### Ask questions about your data")
                    with st.form(key='question_form'):
                        user_question = st.text_input("Enter your question:")
                        submit_button = st.form_submit_button(label='Submit')
                        
                        if submit_button and user_question:
                            with st.spinner("Analyzing..."):
                                # Create Streamlit container for callback
                                response_container = st.container()
                                
                                with response_container:
                                    # Execute agent with Streamlit callback
                                    response = agent_executor.run(user_question)
                                    st.write("Answer:", response)
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
            else:
                st.warning("Please check your OpenAI API key configuration.")

    # Cleanup database when session ends
    if st.session_state.db_path and os.path.exists(st.session_state.db_path):
        try:
            os.remove(st.session_state.db_path)
        except:
            pass

if __name__ == "__main__":
    main()