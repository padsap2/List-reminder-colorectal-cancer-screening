import pandas as pd
import pyodbc
import boto3
import os
import redshift_connector

    
def connect_to_redshift():
    try:
        conn = redshift_connector.connect(
            database='prod',
            host=os.getenv('REDSHIFT_HOST'),
            port=int(os.getenv('REDSHIFT_PORT', 5439)),
            user=os.getenv('REDSHIFT_USER'),
            password=os.getenv('REDSHIFT_PASSWORD'),
            ssl=True
        )
        return conn
    except Exception as e:
        print(f"Error connecting to Redshift: {e}")
        raise


def connect_to_as400():
    """
    Connect to AS400 using a DSN-less connection.
    Environment variables required:
        AS400_HOST, AS400_USER, AS400_PASSWORD
    Optional:
        AS400_PORT   (defaults to 446)
    """
    try:
        # Debug logging
        print("Attempting to connect to AS400...")
        print(f"AS400_HOST: {os.getenv('AS400_HOST')}")
        print(f"AS400_USER: {os.getenv('AS400_USER')}")
        print(f"AS400_PASSWORD: {'*' * len(os.getenv('AS400_PASSWORD', '')) if os.getenv('AS400_PASSWORD') else 'Not set'}")
        print(f"AS400_PORT: {os.getenv('AS400_PORT', '446')}")
        
        # Use DSN-less connection with exact driver name from odbcinst.ini
        conn_str = (
            "DRIVER={IBM i Access ODBC Driver};"  # Must match the name in odbcinst.ini
            f"SYSTEM={os.getenv('AS400_HOST')};"
            f"PORT={os.getenv('AS400_PORT', '446')};"  # Default to 446 if not specified
            f"UID={os.getenv('AS400_USER')};"
            f"PWD={os.getenv('AS400_PASSWORD')};"
            "Commit=0;"      # autocommit off (override in .cursor() if needed)
            "Naming=0;"      # 0 = SQL naming, 1 = system naming
            "Trace=0;"       # set to 1 for driver-level trace
        )
        print("Connection string (masked):", conn_str.replace(os.getenv('AS400_PASSWORD', ''), '****'))
        
        return pyodbc.connect(conn_str, autocommit=True)
    except Exception as e:
        print(f"Error connecting to AS400: {e}")
        raise

def fetch_data_from_redshift(query):
    conn = connect_to_redshift()
    if conn:
        try:
            df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            print(f"Error fetching data from Redshift: {e}")
            return None
    else:
        raise
    
def fetch_data_from_as400(query):
    conn = connect_to_as400()
    if conn:
        try:
            df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            print(f"Error fetching data from AS400: {e}")
            return None
    else:
        raise

def connect_to_s3():
    """
    Returns an S3 client using AWS credentials from environment variables
    """
    try:
        # Check if access key and secret key are provided in environment variables
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        region = os.getenv('AWS_REGION', 'us-east-1')  # Default to us-east-1 if not specified
        
        if access_key and secret_key:
            # Use explicit credentials from environment variables
            return boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
        else:
            # Final fallback to default credentials (Lambda role, ~/.aws/credentials, etc.)
            return boto3.client('s3')
            
    except Exception as e:
        print(f"Error creating S3 client: {e}")
        raise


def retrieve_file_from_s3(key):
    """
    Retrieve a file from S3 using the configured bucket
    """
    conn = connect_to_s3()
    if conn:
        try:
            response = conn.get_object(Bucket=os.getenv('S3_BUCKET'), Key=key)
            file_content = response['Body'].read().decode('utf-8')
            return file_content
        except Exception as e:
            print(f"Error retrieving file from S3: {e}")
            return None
    else:
        raise

def upload_file_to_s3(key, file_path):
    """
    Upload a file to S3 using the configured bucket
    """
    conn = connect_to_s3()
    if conn:
        try:
            with open(file_path, 'rb') as file:
                conn.upload_fileobj(file, Bucket=os.getenv('S3_BUCKET'), Key=key)
            print(f"File uploaded to S3: {key}")
        except Exception as e: 
            print(f"Error uploading file to S3: {e}")
            raise
    else:
        raise
    
    
if __name__ == "__main__":
    
    conn = connect_to_s3()
