import os
import logging
import argparse
from datetime import datetime

from dotenv import load_dotenv
import requests
from requests.exceptions import RequestException
from pypdf import PdfReader, PdfWriter

# Load environment variables
load_dotenv()

def setup_logging(verbose):
    if verbose:
        level = logging.DEBUG
        format = '%(asctime)s - %(levelname)s - %(message)s'
    else:
        level = logging.WARNING
        format = '%(message)s'
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=level, format=format)

def validate_path(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
            logging.info(f"Created directory: {path}")
        return True
    except Exception as e:
        logging.error(f"Error creating directory {path}: {str(e)}")
        return False

def clean_output(path):
    try:
        files = [f.name for f in os.scandir(path) if f.is_file()]
        files_len = len(files)
        if files_len != 0:
            print(f"Removing existing output files. ({files_len} to be removed)")
            for file in files:
                try:
                    os.remove(os.path.join(path, file))
                    logging.info(f"{file} removed successfully.")
                except Exception as e:
                    logging.warning(f"Error deleting {file}: {e}")
    except Exception as outer_error:
        logging.error(f"Error accessing directory {path}: {outer_error}")

def split_pdf(pdf_path, output_folder):
    output_dir = os.path.join(output_folder)
    if not validate_path(output_dir):
        return False
    try:
        if not os.path.exists(pdf_path):
            logging.error(f"PDF file not found: {pdf_path}")
            return False
        pdf = PdfReader(pdf_path)
        if len(pdf.pages) == 0:
            logging.error(f"PDF file is empty: {pdf_path}")
            return False
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
        logging.info(f"Successfully split {pdf_path} into {len(pdf.pages)} pages")
        return True
    except Exception as e:
        logging.error(f"Error processing PDF {pdf_path}: {str(e)}")
        return False

def rename_files(output_dir, start_index=1):
    try:
        files = [f for f in os.listdir(output_dir) if f.endswith('.pdf')]
        if not files:
            logging.warning(f"No PDF files found in {output_dir}")
            return False, start_index
        creation_date = datetime.now().strftime("%d-%m-%y %Hh%Mm")
        for filename in sorted(files):
            try:
                old_path = os.path.join(output_dir, filename)
                new_name = f"{start_index:02}_Xerox_Scan_{creation_date}.pdf"
                new_path = os.path.join(output_dir, new_name)
                os.rename(old_path, new_path)
                logging.debug(f"Renamed: {filename} -> {new_name}")
                start_index += 1
            except Exception as e:
                logging.error(f"Error renaming {filename}: {str(e)}")
        logging.info(f"Successfully renamed {len(files)} files")
        return True, start_index
    except Exception as e:
        logging.error(f"Error during renaming process: {str(e)}")
        return False, start_index

def test_api_connection():
    try:
        if not api_url or not api_token:
            raise ValueError("API_BASE_URL and API_TOKEN must be set in environment variables")
        headers = {'Authorization': f"Token {api_token}"}
        response = requests.get(api_url, headers=headers, verify=pubkey)
        if response.status_code == 200:
            print("API Connection successful!")
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
    if test_api_connection():
        headers = {'Authorization': f"Token {os.getenv('API_TOKEN')}"}
        POST_endpoint = f"{os.getenv('API_BASE_URL')}post_document/"
        files = [f for f in os.listdir(output_folder) if os.path.isfile(os.path.join(output_folder, f))]
        total = len(files)
        print(f"\nThere are {total} files to be uploaded")
        try:
            for i, file in enumerate(files, 1):
                if os.path.isfile(os.path.join(output_folder, file)):
                    print(f"{i:02}/{total:02} Uploading {file}")
                    with open(os.path.join(output_folder, file), 'rb') as file_data:
                        post = {'document': (file, file_data)}
                        response = requests.post(POST_endpoint, headers=headers, files=post, verify=pubkey)
                        response.raise_for_status()
                        logging.info(f"Successfully uploaded {file}. Response: {response.content}")
            return True
        except RequestException as e:
            logging.error(f"Network error during file upload: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Error during file upload: {str(e)}")
            return False
            
def clean_consume():
    content = os.listdir(consume_folder)

    while len(content) > 1:
        print("\nFiles in consume folder:")
        for n in range(len(content)):
            fullpath = os.path.join(consume_folder, content[n])
            try:
                created_time = datetime.fromtimestamp(os.path.getctime(fullpath))
            except Exception as e:
                created_time = f"Error: {e}"
            print(f"[{n+1}] {content[n]}        Created: {created_time}")

        try:
            index = int(input("Select which file to delete (0 to skip deleting): "))
        except ValueError:
            print("Invalid input, please enter a number.")
            continue

        if index == 0:
            print("Skipping...")
            return True

        # Validate index within allowed range
        while index < 1 or index > len(content):
            try:
                index = int(input("Invalid index, please select a valid one (0 to skip): "))
            except ValueError:
                print("Invalid input, skipping...")
                return True

        fullpath = os.path.join(consume_folder, content[index - 1])
        try:
            os.remove(fullpath)
            print(f"Deleted {content[index - 1]}")
        except FileNotFoundError:
            print("File not found, it may have been moved or deleted already.")
        except PermissionError:
            print("Permission denied: Could not delete the file.")
        except Exception as e:
            print(f"Unexpected error: {e}")

        content = os.listdir(consume_folder)

def main():
    parser = argparse.ArgumentParser(description='PDF Splitter and Renamer')
    parser.add_argument('-verbose', action='store_true', help='Enable detailed logging')
    parser.add_argument('-testAPI', action='store_true', help='Test API connectivity')
    parser.add_argument('-upload', action='store_true', help="Upload to Paperless-NGX instance")
    parser.add_argument('-archive', action='store_true', help="Archive processed files")
    args = parser.parse_args()

    global script_dir
    global consume_folder
    global output_folder
    global archive_folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    consume_folder = os.path.join(script_dir, os.getenv('CONSUME_FOLDER')) or input("Enter the path to the consume_folder folder: ").strip()
    output_folder = os.path.join(script_dir, os.getenv('OUTPUT_FOLDER')) or input("Enter the path for the output directory: ").strip()
    archive_folder = os.path.join(script_dir, "Archive") or input("Enter the path for the archive directory: ").strip()

    global api_url
    api_url = os.getenv('API_BASE_URL')
    global api_token
    api_token = os.getenv('API_TOKEN')
    global pubkey
    pubkey = os.path.join(script_dir, os.getenv('PUBKEY')) or input("Enter the path for the TLS CA certificate (.pem file): ").strip()

    setup_logging(args.verbose)

    if args.testAPI:
        if test_api_connection():
            return
        else:
            exit(1)

    try:
        if "C:/path/to/" in consume_folder or "C:/path/to/" in output_folder:
            raise ValueError("Placeholder path detected in environment variables.")
        if not all([validate_path(consume_folder), validate_path(output_folder)]):
            logging.error("Failed to validate directories")
            return
        clean_output(output_folder)

        if len(os.listdir(consume_folder)) > 1 :
            clean_consume()
        
        pdf_files = [f for f in os.listdir(consume_folder) if f.lower().endswith('.pdf')]
        if not pdf_files:
            logging.warning("No PDF files found in the consume_folder folder")
            return

        rename_counter = 1
        for index, filename in enumerate(pdf_files, 1):
            print(f"\nProcessing file {index}/{len(pdf_files)}: {filename}")
            pdf_path = os.path.join(consume_folder, filename)
            if split_pdf(pdf_path, output_folder):
                success, rename_counter = rename_files(output_folder, rename_counter)
                if not success:
                    logging.error(f"Failed to rename files for {filename}")
            else:
                logging.error(f"Failed to process {filename}")

        print(f"\nCompleted processing {len(pdf_files)} PDF files")

    except Exception as e:
        logging.error(f"Program error: {str(e)}")
        raise

    if args.upload:
        if upload():
            print(f"{len(pdf_files):02} files processed and uploaded")
            os.startfile(output_folder)
        else:
            exit(1)

    if args.archive:
        for filename in os.listdir(consume_folder):
            os.rename(os.path.join(consume_folder, filename), os.path.join(archive_folder, filename))


if __name__ == "__main__":
    main()