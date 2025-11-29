import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# Load environment variables from .env file
load_dotenv()

def get_db_engine():
    """
    Creates and returns a SQLAlchemy engine configured from environment variables.
    """
    try:
        # Using pyodbc connection string
        connection_string = (
            f"mssql+pyodbc://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@"
            f"{os.getenv('DB_SERVER')}/{os.getenv('DB_DATABASE')}?"
            f"driver={os.getenv('DB_DRIVER').replace(' ', '+')}"
        )
        # For trusted connection (Windows Authentication)
        # if os.getenv('TRUSTED_CONNECTION') == 'yes':
        #     connection_string = (
        #         f"mssql+pyodbc://@{os.getenv('DB_SERVER')}/{os.getenv('DB_DATABASE')}?"
        #         f"driver={os.getenv('DB_DRIVER').replace(' ', '+')}&trusted_connection=yes"
        #     )
        
        engine = create_engine(connection_string)

        # Test connection
        connection = engine.connect()
        print("Database connection successful!")
        connection.close()
        
        return engine
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise

if __name__ == '__main__':
    # This block is for testing the connection directly
    get_db_engine()
