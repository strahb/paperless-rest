import os
from pypdf import PdfReader, PdfWriter
from datetime import datetime
import logging
import argparse
from dotenv import load_dotenv
import requests
from requests.exceptions import RequestException

# Load environment variables
load_dotenv()

def setup_logging(verbose):
    """Configure logging based on verbosity level."""
    if verbose:
        level = logging.DEBUG
        format = '%(asctime)s - %(levelname)s - %(message)s'
    else:
        level = logging.WARNING
        format = '%(message)s'
    
    # Remove any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format=format
    )

def validate_path(path):
    """Validate and create directory if it doesn't exist."""
    try:
        if not os.path.exists(path):
            os.makedirs(path)
            logging.info(f"Created directory: {path}")      
        return True
    except Exception as e:
        logging.error(f"Error creating directory {path}: {str(e)}")
        return False

def clean_output(path):
    """Ensure the output path is empty, so as to not cause any upload conflicts"""
    try:
        # Get all files in the directory
        files = [f.name for f in os.scandir(path) if f.is_file()]
        files_len = len(files)
        
        print(f"Removing {files_len} existing files.")
        
        for file in files:
            try:
                file_path = os.path.join(path, file)
                os.remove(file_path)
                logging.info(f"{file} removed successfully.")
            except Exception as e:
                logging.warning(
                    f"Error deleting {file}. The program will proceed, but it will attempt to handle the failed document. Error: {e}"
                )
                # Continue removing other files instead of returning early
                continue
    except Exception as outer_error:
        logging.error(f"Error accessing directory {path}: {outer_error}")

def split_pdf(pdf_path, output_base_dir):
    """Split PDF into individual pages."""
    output_dir = os.path.join(output_base_dir)
    if not validate_path(output_dir):
        return False

    try:
        # Verify PDF file exists
        if not os.path.exists(pdf_path):
            logging.error(f"PDF file not found: {pdf_path}")
            return False

        # Open and validate PDF
        pdf = PdfReader(pdf_path)
        if len(pdf.pages) == 0:
            logging.error(f"PDF file is empty: {pdf_path}")
            return False
        
        # Split pages
        for page_num in range(len(pdf.pages)):
            try:
                pdf_writer = PdfWriter()
                pdf_writer.add_page(pdf.pages[page_num])
                
                output_filename = f"temp_page_{page_num + 1}.pdf"
                output_path = os.path.join(output_dir, output_filename)
                
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
                logging.debug(f"Created page {page_num + 1}")
            
            except Exception as e:
                logging.error(f"Error processing page {page_num + 1}: {str(e)}")
                continue
        
        logging.info(f"Successfully split {pdf_path} into {len(pdf.pages)} pages")
        return True
        
    except Exception as e:
        logging.error(f"Error processing PDF {pdf_path}: {str(e)}")
        return False

def rename_files(output_dir):
    """Rename split PDF files with date and sequential numbering."""
    try:
        files = [f for f in os.listdir(output_dir) if f.endswith('.pdf')]
        if not files:
            logging.warning(f"No PDF files found in {output_dir}")
            return False

        creation_date = datetime.now().strftime("%d-%m-%y")
        
        for index, filename in enumerate(sorted(files), start=1):
            try:
                old_path = os.path.join(output_dir, filename)
                new_name = f"{index:02}_Xerox_Scan_{creation_date}.pdf"
                new_path = os.path.join(output_dir, new_name)
                
                os.rename(old_path, new_path)
                logging.debug(f"Renamed: {filename} -> {new_name}")
                
            except Exception as e:
                logging.error(f"Error renaming {filename}: {str(e)}")
                continue
                
        logging.info(f"Successfully renamed {len(files)} files")
        return True
        
    except Exception as e:
        logging.error(f"Error during renaming process: {str(e)}")
        return False

def test_api_connection():
    """Test API connectivity using credentials from environment variables."""
    try:
        if not api_url or not api_token:
            raise ValueError("API_BASE_URL and API_TOKEN must be set in environment variables")

        headers = {'Authorization': f'Token {api_token}'}
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            logging.info("API Connection successful!")
            return True
        else:
            logging.error(f"API Connection failed with status code: {response.status_code}")
            logging.error(f"API Response: {response.text}")
            return False

    except RequestException as e:
        logging.error(f"Network error while testing API: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Error testing API connection: {str(e)}")
        return False

def upload():
    """POST output files to the Paperless-NGX Instance following the env variables"""
    if test_api_connection():
        headers = {'Authorization': f'Token {os.getenv('API_TOKEN')}'}
        POST_endpoint = f"{os.getenv('API_BASE_URL')}post_document/"

        output_folder = os.getenv('OUTPUT_FOLDER')
        files = [f for f in os.listdir(output_folder) if os.path.isfile(os.path.join(output_folder, f))]
        files = (len(files))
        _ = 1
        print(f"\nThere are {files} files to be uploaded")      
    try:        
        """The POSTing segment of the code"""
        for file in os.listdir(output_folder):
            print(f"{_:02}/{files} Uploading {file}")
            _ += 1
            with open(f"{output_folder}/{file}", 'rb') as file_data:
                post = {'document': (file, file_data)}
                response = requests.post(POST_endpoint, headers=headers, files=post )
                response.raise_for_status()  # Raise an HTTPError for bad status codes
                logging.info(f"Successfully uploaded {file}. Response: {response.content}")
        return
    except RequestException as e:
        logging.error(f"Network error during file upload: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Error during file upload: {str(e)}")
        return False
  
        
def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='PDF Splitter and Renamer')
    parser.add_argument('-verbose', action='store_true', help='Enable detailed logging')
    parser.add_argument('-testAPI', action='store_true', help='Test API connectivity')
    parser.add_argument('-upload', action='store_true', help="Upload to Paperless-NGX instance") 
    args = parser.parse_args()
    
    # Global variable delcarationc
    global api_url
    api_url = os.getenv('API_BASE_URL')
    global api_token 
    api_token = os.getenv('API_TOKEN')
    
    # Configure logging based on verbose flag
    setup_logging(args.verbose)
    
    # If -testAPI flag is present, only test API and exit
    if args.testAPI:
        if test_api_connection():
            return
        else:
            exit(1)
    
    try:
        # Get paths from environment variables or prompt user
        consume_folder = os.getenv('CONSUME_FOLDER') or input("Enter the path to the consume folder: ").strip()
        output_base_dir = os.getenv('OUTPUT_FOLDER') or input("Enter the path for the output directory: ").strip()
        
        # Check for placeholder paths
        if "C:/path/to/" in consume_folder or "C:/path/to/" in output_base_dir:
            raise ValueError("Placeholder path detected in environment variables. Please update the consume and output folders.")
        
        if not all([validate_path(consume_folder), validate_path(output_base_dir)]):
            logging.error("Failed to validate directories")
            return
        
        # CLean output folder from any existing files
        if clean_output(output_base_dir):
            return

        # Process PDF files
        pdf_files = [f for f in os.listdir(consume_folder) if f.lower().endswith('.pdf')]
        if not pdf_files:
            logging.warning("No PDF files found in the consume folder")
            return
        
        for index, filename in enumerate(pdf_files, 1):
            print(f"\nProcessing file {index}/{len(pdf_files)}: {filename}")
            pdf_path = os.path.join(consume_folder, filename)
            
            if split_pdf(pdf_path, output_base_dir):
                output_dir = os.path.join(output_base_dir)
                rename_files(output_dir)
            else:
                logging.error(f"Failed to process {filename}")
        
        print(f"\nCompleted processing {len(pdf_files)} PDF files")
        
    except Exception as e:
        logging.error(f"Program error: {str(e)}")
        raise
    
    if args.upload:
        if upload():
            exit(1)

if __name__ == "__main__":
    main()
