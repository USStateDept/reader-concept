from .docx import *
from .html import *
from .memo import *

"""
API-like Modules to ingest various document types, called by pipeline.py

The ingest formats (obviously) vary, but the output is a defined structure

##
## FileType intake:
##

docx.py
 |-> Docx

These generate an object property, .data that is a BeautifulSoup4 object with the
'body' as the top level container

##
## DataType parsers:
##

memo.py
 |-> MemoHandler

these ingest a .data property and the .parse() method parses the document and
generates .output dictionary that includes

{
 "header": {...}, # not required
 "footer": {...}, # not required
 "html": "string",
 "full_text": "string",
 "file_name": "string"
}

header fields:
# any can be 'unknown' if not determined or specified

 'from_auth': 'string',
 'doc_date': 'string', # format: December 26, 2012
 'from_bur': 'string',
 'addressee': 'string',
 'classification': 'string',
 'title': 'string'
 'category': 'string'

footer fields:
# any string field can be 'unknown' if not determined or specified

 'has_attachments': bit,
 'attach_urls': list or None,
 'approved_bur': 'string',
 'approved_name': 'string',
 'draft_bur': 'string',
 'draft_name': 'string',
 'draft_ext': 'string',
 'draft_phone': 'string',
 'clear_blob': list (can be empty)

"""