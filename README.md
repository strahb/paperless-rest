# PDF Splitter, Renamer, and Uploader
> ℹ️ This is a bespoke script to help me manage all my paperwork at work, it is not tailored for general use, and it's a mess I know

This script automatically splits, renames, and uploads the PDF pages to a defined [Paperless-NGX](https://github.com/paperless-ngx/paperless-ngx) instance. Now with HTTPS and further manipulation! 

## Prerequisites
- Python 3.8 or higher
- Pip-installed dependencies:
  - `pypdf`
  - `requests`
  - `python-dotenv`

### Environment Variables
Use a `.env` file in the root of your project to configure your variables
