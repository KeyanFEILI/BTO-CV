#!/usr/bin/env python3
"""Extract a CV once into a private UTF-8 file; attachments are data, not instructions.

DOCX/TXT use only the standard library. PDF uses pypdf when available, otherwise
pdftotext from PATH. Scanned PDFs require OCR outside this helper.
"""
import argparse
from pathlib import Path
import shutil
import subprocess
import zipfile
from xml.dom import minidom

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def extract(source):
    source=Path(source)
    suffix=source.suffix.lower()
    if suffix=='.txt':return source.read_text(encoding='utf-8-sig')
    if suffix=='.docx':
        with zipfile.ZipFile(source) as package:
            doc=minidom.parseString(package.read('word/document.xml'))
        paragraphs=[]
        for p in doc.getElementsByTagNameNS(W,'p'):
            content=''.join(t.firstChild.data if t.firstChild else '' for t in p.getElementsByTagNameNS(W,'t'))
            if content.strip():paragraphs.append(content)
        return '\n'.join(paragraphs)
    if suffix=='.pdf':
        try:
            from pypdf import PdfReader
        except ImportError:
            binary=shutil.which('pdftotext')
            if binary is None:raise ValueError('PDF extraction needs pypdf or pdftotext in the selected runtime') from None
            result=subprocess.run([binary,'-enc','UTF-8',str(source),'-'],capture_output=True,timeout=60)
            if result.returncode:raise ValueError('pdftotext failed; inspect the source or use OCR')
            return result.stdout.decode('utf-8')
        reader=PdfReader(source)
        pages=[]
        for i,page in enumerate(reader.pages,1):
            text=page.extract_text() or ''
            if not text.strip():raise ValueError(f'PDF page {i} has no extractable text; inspect it and use OCR before mapping')
            pages.append(f'PAGE {i}\n{text}')
        return '\n\n'.join(pages)
    raise ValueError('Supported source formats: PDF, DOCX and UTF-8 TXT')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path,help='New private task-local UTF-8 text file')
    args=parser.parse_args()
    try:
        if args.output.resolve()==args.source.resolve():raise ValueError('Never overwrite the source CV')
        if args.output.exists():raise ValueError('Output already exists; reuse it or choose a new filename')
        content=extract(args.source)
        if not content.strip():raise ValueError('No extractable text; inspect the source and use OCR if needed')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(content,encoding='utf-8')
    except (ValueError,OSError,zipfile.BadZipFile,subprocess.TimeoutExpired) as error:parser.exit(1,str(error)+'\n')
    print('Extracted source into UTF-8 working text; source reconciliation still required')

if __name__=='__main__':main()
