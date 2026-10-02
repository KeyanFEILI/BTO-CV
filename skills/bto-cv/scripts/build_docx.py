#!/usr/bin/env python3
"""Create native editable DOCX from normalized candidate JSON. Python standard library only."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import zipfile
from xml.dom import minidom

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
HEADINGS = ['WORK EXPERIENCE', 'EDUCATION', 'IT SKILLS', 'CERTIFICATIONS AND TRAINING', 'LANGUAGES']

def text(node):
    return ''.join(c.data for t in node.getElementsByTagNameNS(W, 't') for c in t.childNodes if c.nodeType == c.TEXT_NODE)

def children(node, local):
    return [c for c in node.childNodes if c.nodeType == c.ELEMENT_NODE and c.namespaceURI == W and c.localName == local]

def string(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + ' must be a non-empty string')
    if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', value):
        raise ValueError(label + ' contains invalid XML control characters')
    return value.strip()

def strings(value, label):
    if not isinstance(value, list): raise ValueError(label + ' must be a list')
    return [string(v, label) for v in value]

def normalize(data):
    if not isinstance(data, dict): raise ValueError('Candidate data must be an object')
    allowed={'initials','experience','education','skills','certifications','languages'}
    unknown=set(data)-allowed
    if unknown: raise ValueError('Unmapped fields: '+', '.join(sorted(unknown)))
    result={'initials':string(data.get('initials'),'initials')}
    for key in ['education','certifications','languages']:
        result[key]=strings(data.get(key,[]),key)
    for key,fields in [('experience',{'dates','role','employer','bullets'}),('skills',{'category','bullets'})]:
        items=data.get(key,[])
        if not isinstance(items,list): raise ValueError(key+' must be a list')
        result[key]=[]
        for item in items:
            if not isinstance(item,dict) or set(item)-fields: raise ValueError('Invalid fields in '+key)
            record={'bullets':strings(item.get('bullets',[]),key+'.bullets')}
            for field in fields-{'bullets'}:
                value=item.get(field,'')
                if not isinstance(value,str): raise ValueError(field+' must be a string')
                record[field]=string(value,field) if value.strip() else ''
            if not any(record.values()): raise ValueError('Empty '+key+' entry')
            result[key].append(record)
    if not any(result[k] for k in allowed-{'initials'}): raise ValueError('No CV content supplied')
    return result

def build(data, output, layout='mm', template=None):
    data=normalize(data)
    template=Path(template) if template else Path(__file__).resolve().parents[1]/'assets'/('BTO_CV_Template_DP.docx' if layout=='dp' else 'BTO_CV_Template.docx')
    output=Path(output)
    if output.suffix.lower()!='.docx': raise ValueError('Output must end in .docx')
    if output.resolve()==template.resolve(): raise ValueError('Never overwrite the master template')
    if output.exists(): raise FileExistsError('Output already exists; choose a new filename')
    with zipfile.ZipFile(template) as z: parts={f:z.read(f) for f in z.namelist()}
    doc=minidom.parseString(parts['word/document.xml'])
    body=doc.getElementsByTagNameNS(W,'body')[0]
    paras=children(body,'p');sect=children(body,'sectPr')[0].cloneNode(True)
    prototypes={text(p):p for p in paras}
    required=['initials','gap','dates','role','employer','responsibilities','experience_bullet','education_bullet','skill_category','skill_bullet','certification_bullet','language_bullet']
    for slot in required:
        if '{{'+slot+'}}' not in prototypes: raise ValueError('Template slot missing: '+slot)
    for heading in HEADINGS:
        if heading not in prototypes: raise ValueError('Template heading missing: '+heading)
    banner=paras[0].cloneNode(True)
    if not banner.getElementsByTagNameNS(W,'drawing'): raise ValueError('Template banner missing')
    for node in list(body.childNodes): body.removeChild(node)
    body.appendChild(banner)
    def emit(key,value=None):
        p=prototypes[key].cloneNode(True)
        if value is not None:
            runs=children(p,'r');rp=children(runs[0],'rPr') if runs else []
            rp=rp[0].cloneNode(True) if rp else None
            for c in list(p.childNodes):
                if c.nodeType!=c.ELEMENT_NODE or c.localName!='pPr':p.removeChild(c)
            r=doc.createElementNS(W,'w:r')
            if rp:r.appendChild(rp)
            # Keep plain text editable; XML serializer escapes ampersands and angle brackets.
            for i,line in enumerate(value.replace('\r\n','\n').split('\n')):
                if i:r.appendChild(doc.createElementNS(W,'w:br'))
                t=doc.createElementNS(W,'w:t');t.setAttribute('xml:space','preserve');t.appendChild(doc.createTextNode(line));r.appendChild(t)
            p.appendChild(r)
        body.appendChild(p)
    def slot(name,value):emit('{{'+name+'}}',value)
    def gap(count=1):
        for _ in range(count):slot('gap','')
    slot('initials',data['initials']);gap()
    section_count=0
    def heading(name):
        nonlocal section_count
        if section_count:gap(2)
        emit(name);section_count+=1
    if data['experience']:
        heading(HEADINGS[0])
        if layout=='dp':gap()
        for i,job in enumerate(data['experience']):
            if i:gap()
            for key in ['dates','role','employer']:
                if job[key]:slot(key,job[key])
            if job['bullets']:
                slot('responsibilities','Main responsibilities:')
                for b in job['bullets']:slot('experience_bullet',b)
    if data['education']:
        heading(HEADINGS[1])
        for b in data['education']:slot('education_bullet',b)
    if data['skills']:
        heading(HEADINGS[2])
        for group in data['skills']:
            if group['category']:slot('skill_category',group['category'])
            for b in group['bullets']:slot('skill_bullet',b)
    for key,title,role in [('certifications',HEADINGS[3],'certification_bullet'),('languages',HEADINGS[4],'language_bullet')]:
        if data[key]:
            heading(title)
            for b in data[key]:slot(role,b)
    body.appendChild(sect)
    parts['word/document.xml']=doc.toxml(encoding='UTF-8')
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for name,content in parts.items():z.writestr(name,content)
    return data

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path,help='Normalized UTF-8 candidate JSON')
    parser.add_argument('output',type=Path,help='New .docx output file')
    parser.add_argument('--layout',choices=['mm','dp'],default='mm')
    parser.add_argument('--template',type=Path,help='Explicit approved DOCX master')
    args=parser.parse_args()
    try:build(json.loads(args.input.read_text(encoding='utf-8-sig')),args.output,args.layout,args.template)
    except (ValueError,KeyError,OSError,zipfile.BadZipFile) as error:parser.exit(1,str(error)+'\n')
    print('Created '+str(args.output))

if __name__=='__main__': main()
