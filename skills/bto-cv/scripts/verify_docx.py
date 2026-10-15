#!/usr/bin/env python3
"""Verify a generated CV against its normalized input and the paired Word master.

This checks content preservation and Word structure, not factual source accuracy
or visual pagination. Python standard library only; no extra document generation.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import zipfile
from xml.dom import minidom

spec=importlib.util.spec_from_file_location('bto_builder',Path(__file__).with_name('build_docx.py'))
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
W=builder.W

def expected_content(data):
    """Expected non-empty paragraphs and their list status in candidate order."""
    content=[(data['initials'],False)]
    if data['experience']:
        content.append(('WORK EXPERIENCE',False))
        for job in data['experience']:
            content.extend((job[k],False) for k in ('dates','role','employer') if job[k])
            if job['bullets']:
                content.append(('Main responsibilities:',False))
                content.extend((v,True) for v in job['bullets'])
    for key,title in [('education','EDUCATION'),('skills','IT SKILLS'),
                      ('certifications','CERTIFICATIONS AND TRAINING'),('languages','LANGUAGES')]:
        if not data[key]:continue
        content.append((title,False))
        if key=='skills':
            for group in data[key]:
                if group['category']:content.append((group['category'],False))
                content.extend((v,True) for v in group['bullets'])
        else:content.extend((v,True) for v in data[key])
    return [(v.replace('\r\n','\n').replace('\n',''),is_list) for v,is_list in content]

def verify(data,output,template=None):
    data=builder.normalize(data)
    template=Path(template) if template else Path(__file__).resolve().parents[1]/'assets/BTO_CV_Template.docx'
    with zipfile.ZipFile(template) as source,zipfile.ZipFile(output) as result:
        if set(source.namelist())!=set(result.namelist()):raise ValueError('DOCX package members differ from the master')
        parts={name:result.read(name) for name in result.namelist()}
        for name in source.namelist():
            if name!='word/document.xml' and source.read(name)!=parts[name]:
                raise ValueError('Unexpected change to master package part: '+name)
        master=minidom.parseString(source.read('word/document.xml'))
    doc=minidom.parseString(parts['word/document.xml'])
    body=doc.getElementsByTagNameNS(W,'body')[0]
    paras=builder.children(body,'p')
    actual=[]
    for p in paras:
        value=builder.text(p)
        if value:actual.append((value,bool(p.getElementsByTagNameNS(W,'numPr'))))
    expected=expected_content(data)
    if actual!=expected:raise ValueError('Document paragraphs or native list assignments differ from normalized input')
    if doc.getElementsByTagNameNS(W,'sectPr')[0].toxml()!=master.getElementsByTagNameNS(W,'sectPr')[0].toxml():
        raise ValueError('Page settings differ from the master')
    banner=builder.children(master.getElementsByTagNameNS(W,'body')[0],'p')[0]
    if not paras or paras[0].toxml()!=banner.toxml() or len(doc.getElementsByTagNameNS(W,'drawing'))!=1:
        raise ValueError('Banner differs from the master')
    lists={}
    for p in paras:
        if builder.text(p)=='Main responsibilities:':
            spacing=p.getElementsByTagNameNS(W,'spacing')
            if (len(spacing)!=1 or spacing[0].getAttributeNS(W,'line')!='360'
                    or spacing[0].getAttributeNS(W,'lineRule')!='auto'
                    or any(spacing[0].getAttributeNS(W,key) not in ('','0') for key in ('before','after'))):
                raise ValueError('Main responsibilities label must use 1.5-line spacing with zero paragraph spacing')
        if p.getElementsByTagNameNS(W,'numPr'):
            lists['{{bullet_'+str(len(lists))+'}}']=p
            if not p.getElementsByTagNameNS(W,'keepLines'):raise ValueError('List paragraph may split across pages')
    builder.validate_lists(lists,parts,[key[2:-2] for key in lists])
    return {'paragraphs':len(expected),'roles':len(data['experience']),'skill_groups':len(data['skills'])}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('document',type=Path)
    parser.add_argument('--template',type=Path)
    args=parser.parse_args()
    try:result=verify(json.loads(args.input.read_text(encoding='utf-8-sig')),args.document,args.template)
    except (ValueError,KeyError,IndexError,OSError,zipfile.BadZipFile) as error:parser.exit(1,str(error)+'\n')
    print(f"Verified {result['roles']} roles, {result['skill_groups']} skill groups and {result['paragraphs']} content paragraphs; visual and source review still required")

if __name__=='__main__':main()
