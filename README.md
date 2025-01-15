# PDF Splitter, Renamer, and Uploader

The script automatically splits, renames, and uploads the PDF pages to a defined [Paperless-NGX](https://github.com/paperless-ngx/paperless-ngx) instance.

---

## Prerequisites
- Python 3.8 or higher
- Pip-installed dependencies:
  - `pypdf`
  - `requests`
  - `python-dotenv`

### Environment Variables
Use a `.env` file in the root of your project to configure the following variables:

```env
API_BASE_URL=https://your-paperless-ngx-instance.com/api/documents/
API_TOKEN=your_api_token
CONSUME_FOLDER=/path/to/input/folder
OUTPUT_FOLDER=/path/to/output/folder
```
