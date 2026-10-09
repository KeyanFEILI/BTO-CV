#!/usr/bin/env python3
"""Create native editable DOCX from normalized candidate JSON. Python standard library only."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import sys
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
    if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]', value):
        raise ValueError(label + ' contains invalid XML control characters')
    return value.strip()

def strings(value, label):
    if not isinstance(value, list): raise ValueError(label + ' must be a list')
    result = [string(v, label) for v in value]
    for v in result:
        if re.match(r'^(?:[\u2022\u25aa\u25a0\u25cf\u25ab\uf0a7]|[-*]\s)', v):
            raise ValueError(label + ' must contain content only, without a typed bullet prefix')
    return result

LANGUAGE_LEVELS={'native':'Native','mother tongue':'Native','fluent':'Fluent','c1':'Fluent','c2':'Fluent',
                'b2':'Professional','professional working proficiency':'Professional',
                'full professional proficiency':'Professional','professional':'Professional',
                'basic':None,'a1':None,'a2':None,'b1':None,'intermediate':None,'beginner':None,
                'elementary':None,'limited proficiency':None}
LEVEL_PATTERN=r'\b(?:mother tongue|professional working proficiency|full professional proficiency|limited proficiency|professional|native|fluent|intermediate|beginner|elementary|basic|[ABC][12])\b'
# Canonical English names; common source-language spellings are explicit aliases.
LANGUAGE_NAMES={name.casefold():name for name in (
    'Afrikaans Albanian Amharic Arabic Armenian Azerbaijani Basque Belarusian Bengali Bosnian Bulgarian '
    'Burmese Catalan Cantonese Chinese Croatian Czech Danish Dutch English Estonian Finnish French '
    'Georgian German Greek Gujarati Hebrew Hindi Hungarian Icelandic Indonesian Irish Italian Japanese '
    'Kannada Kazakh Khmer Korean Kurdish Lao Latin Latvian Lithuanian Luxembourgish Macedonian Malay '
    'Malayalam Maltese Mandarin Marathi Mongolian Nepali Norwegian Pashto Persian Polish Portuguese '
    'Punjabi Romanian Russian Serbian Sinhala Slovak Slovenian Somali Spanish Swahili Swedish Tagalog '
    'Tamil Telugu Thai Turkish Ukrainian Urdu Uzbek Vietnamese Welsh Zulu').split()}
LANGUAGE_NAMES.update({'français':'French','francais':'French','deutsch':'German','español':'Spanish',
                       'espanol':'Spanish','italiano':'Italian','português':'Portuguese',
                       'portugues':'Portuguese','русский':'Russian','английский':'English',
                       'nederlands':'Dutch','中文':'Chinese','日本語':'Japanese','한국어':'Korean'})
EXAM_PATTERN=r'\b(?:IELTS|TOEFL|TOEIC|DELF|DALF|DILF|TCF|TEF|Cambridge|Goethe|TestDaF|telc|DELE|SIELE|CELI|CILS|HSK|JLPT|OET|PTE|Duolingo|Linguaskill|FCE|CAE|CPE|BULATS|certificat\w*|certified|exam\w*|test|diploma|score)\b'

def language_parts(value, review=None):
    """Separate explicit proficiency from supplied exams; never infer a level from a score."""
    boundary=re.search(r'\(|:|\s+[-\u2013\u2014]\s*|[-\u2013\u2014](?=(?:CEFR\s+)?'+LEVEL_PATTERN+r')',value,re.I)
    if boundary is None:
        boundary=re.search(r'\s+(?=(?:CEFR\s+)?'+LEVEL_PATTERN+r')',value,re.I)
    if boundary is None:
        boundary=re.search(r'\s+(?='+EXAM_PATTERN+r')',value,re.I)
    if boundary is None:
        if review is not None:review.append(value+' - omitted: no stated proficiency')
        return None,[]
    name=value[:boundary.start()].strip()
    if not name:raise ValueError('Language name missing: '+value)
    remainder=value[boundary.start():].strip(' :-\u2013\u2014')
    # Keep entire exam notes, including CEFR exam names, scores and dates.
    chunks=re.findall(r'\(([^()]*)\)|([^()]+)',remainder)
    if re.sub(r'\([^()]*\)|[^()]+','',remainder):
        if review is not None:review.append(value+' - omitted: unclear language parentheses')
        return None,[]
    proficiency=[];certifications=[]
    for group,plain in chunks:
        for chunk in re.split(r'\s*;\s*',group or plain):
            chunk=chunk.strip(' /,;:-')
            if not chunk:continue
            exam=re.search(EXAM_PATTERN,chunk,re.I)
            if exam:
                # "C1, IELTS 8.0" has an explicit level before the exam name.
                prefix=chunk[:exam.start()].strip(' /,;:-')
                if prefix and re.fullmatch(r'(?:CEFR\s+)?'+LEVEL_PATTERN,prefix,re.I):
                    proficiency.append(prefix);note=chunk[exam.start():].strip()
                else:note=chunk
                certifications.append(name+' - '+note)
            elif group and certifications and re.match(r'^(?:\d|score\b|passed\b|taken\b|planned\b|pending\b)',chunk,re.I):
                certifications[-1]+=' ('+chunk+')'
            else:proficiency.append(chunk)
    mapped=[];unknown=[]
    for part in proficiency:
        matches=list(re.finditer(LEVEL_PATTERN,part,re.I))
        mapped.extend(LANGUAGE_LEVELS[m.group().lower()] for m in matches)
        if any(m.group().lower() in ('native','mother tongue') for m in matches):
            if not re.fullmatch(r'(?:native(?: speaker)?|mother tongue)',part,re.I):
                unknown.append('native status is not explicitly stated')
        residue=re.sub(LEVEL_PATTERN,'',part,flags=re.I)
        residue=re.sub(r'\b(?:CEFR|level|proficiency|proficient)\b','',residue,flags=re.I).strip(' /,;:-')
        if re.fullmatch(r'native speaker',part,re.I):residue=''
        if residue:unknown.append(residue)
    canonical=LANGUAGE_NAMES.get(name.casefold())
    reason=None
    if not canonical:reason='language name requires English-name review'
    elif len(set(mapped))>1:reason='conflicting proficiency evidence'
    elif unknown:reason='ambiguous proficiency description'
    elif not mapped:reason='no stated proficiency; exams alone do not establish a level'
    elif mapped[0] is None:reason='below Professional working proficiency'
    if reason:
        if review is not None:review.append(value+' - omitted: '+reason)
        return None,certifications
    return canonical+' ('+mapped[0]+')',certifications

def language_label(value):
    return language_parts(value)[0]

def validate_lists(prototypes, parts):
    """Fail before writing if any list slot has lost its native square numbering."""
    numbering=minidom.parseString(parts['word/numbering.xml'])
    nums={n.getAttributeNS(W,'numId'):n for n in children(numbering.documentElement,'num')}
    abstracts={n.getAttributeNS(W,'abstractNumId'):n for n in children(numbering.documentElement,'abstractNum')}
    for slot in ['experience_bullet','education_bullet','skill_bullet','certification_bullet','language_bullet']:
        try:
            p=prototypes['{{'+slot+'}}']
            numpr=children(children(p,'pPr')[0],'numPr')[0]
            identifier=children(numpr,'numId')[0].getAttributeNS(W,'val')
            level=children(numpr,'ilvl')[0].getAttributeNS(W,'val')
            num=nums[identifier]
            abstract=abstracts[children(num,'abstractNumId')[0].getAttributeNS(W,'val')]
            # Overrides can replace the inherited glyph or turn the list into numbers.
            overrides=[n for n in children(num,'lvlOverride') if n.getAttributeNS(W,'ilvl')==level]
            levels=children(overrides[0],'lvl') if overrides else []
            if not levels:levels=[n for n in children(abstract,'lvl') if n.getAttributeNS(W,'ilvl')==level]
            lvl=levels[0]
            fonts=children(children(lvl,'rPr')[0],'rFonts')[0]
            valid=(children(lvl,'numFmt')[0].getAttributeNS(W,'val')=='bullet' and
                   children(lvl,'lvlText')[0].getAttributeNS(W,'val')=='\uf0a7' and
                   fonts.getAttributeNS(W,'ascii')=='Wingdings' and
                   fonts.getAttributeNS(W,'hAnsi')=='Wingdings')
            if not valid:raise ValueError()
        except (IndexError,KeyError,ValueError):
            raise ValueError('Template native square list invalid: '+slot) from None

def normalize(data):
    if not isinstance(data, dict): raise ValueError('Candidate data must be an object')
    allowed={'initials','experience','education','skills','certifications','languages','language_review'}
    unknown=set(data)-allowed
    if unknown: raise ValueError('Unmapped fields: '+', '.join(sorted(unknown)))
    result={'initials':string(data.get('initials'),'initials')}
    for key in ['education','certifications','languages']:
        result[key]=strings(data.get(key,[]),key)
    languages=[];evidence={};review=strings(data.get('language_review',[]),'language_review')
    for value in result['languages']:
        label,certifications=language_parts(value,review)
        if label:languages.append(label)
        for spelling,name in LANGUAGE_NAMES.items():
            if re.match(re.escape(spelling)+r'(?=$|[\s(:\-\u2013\u2014])',value,re.I):
                evidence.setdefault(name,[]).append(label)
                break
        for certificate in certifications:
            if certificate.casefold() not in {v.casefold() for v in result['certifications']}:
                result['certifications'].append(certificate)
    result['languages']=languages
    # Multiple entries for the same language must not conceal conflicting levels.
    for name,values in evidence.items():
        entries=set(values)
        if len(entries)>1:
            languages[:]=[label for label in languages if not label.startswith(name+' (')]
            review.append(name+' - omitted: conflicting proficiency evidence across entries')
    result['languages']=list(dict.fromkeys(languages))
    if review:result['language_review']=list(dict.fromkeys(review))
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
    if not any(result.get(k) for k in allowed-{'initials'}): raise ValueError('No CV content supplied')
    return result

def build(data, output, template=None):
    data=normalize(data)
    template=Path(template) if template else Path(__file__).resolve().parents[1]/'assets'/'BTO_CV_Template.docx'
    output=Path(output)
    if output.suffix.lower()!='.docx': raise ValueError('Output must end in .docx')
    if output.resolve()==template.resolve(): raise ValueError('Never overwrite the master template')
    if output.exists(): raise FileExistsError('Output already exists; choose a new filename')
    with zipfile.ZipFile(template) as z: parts={f:z.read(f) for f in z.namelist()}
    doc=minidom.parseString(parts['word/document.xml'])
    body=doc.getElementsByTagNameNS(W,'body')[0]
    paras=children(body,'p');sect=children(body,'sectPr')[0].cloneNode(True)
    prototypes={text(p):p for p in paras}
    required=['layout_rr_afr_v2','gap','initial_gap','initials','dates','role','employer','responsibilities','experience_bullet','education_bullet','skill_category','skill_bullet','certification_bullet','language_bullet']
    for slot in required:
        if '{{'+slot+'}}' not in prototypes:
            raise ValueError('Template slot missing: '+slot+'. Template and generator are incompatible; use the master bundled with this installed generator (omit --template).')
    for heading in HEADINGS:
        if heading not in prototypes: raise ValueError('Template heading missing: '+heading)
    validate_lists(prototypes,parts)
    banner=paras[0].cloneNode(True)
    if not banner.getElementsByTagNameNS(W,'drawing'): raise ValueError('Template banner missing')
    for node in list(body.childNodes): body.removeChild(node)
    body.appendChild(banner)
    def emit(key,value=None):
        p=prototypes[key].cloneNode(True)
        if value is not None:
            runs=children(p,'r');rp=children(runs[0],'rPr') if runs else []
            rp=rp[0].cloneNode(True) if rp else None
            tails=[r.cloneNode(True) for r in runs if r.getElementsByTagNameNS(W,'br') and not r.getElementsByTagNameNS(W,'t')]
            for c in list(p.childNodes):
                if c.nodeType!=c.ELEMENT_NODE or c.localName!='pPr':p.removeChild(c)
            r=doc.createElementNS(W,'w:r')
            if rp:r.appendChild(rp)
            # Keep plain text editable; XML serializer escapes ampersands and angle brackets.
            for i,line in enumerate(value.replace('\r\n','\n').split('\n')):
                if i:r.appendChild(doc.createElementNS(W,'w:br'))
                t=doc.createElementNS(W,'w:t');t.setAttribute('xml:space','preserve');t.appendChild(doc.createTextNode(line));r.appendChild(t)
            if value:
                p.appendChild(r)
                for tail in tails:p.appendChild(tail)
        body.appendChild(p)
    def slot(name,value):emit('{{'+name+'}}',value)
    def gap(count):
        for _ in range(count):slot('gap','')
    slot('initials',data['initials'])
    slot('initial_gap','')
    previous=None
    def heading(name):
        nonlocal previous
        if previous:gap(2)
        emit(name);previous=name
    if data['experience']:
        heading(HEADINGS[0])
        for i,job in enumerate(data['experience']):
            if i:gap(1)
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
    parser.add_argument('--template',type=Path,help='Explicit approved DOCX master')
    args=parser.parse_args()
    try:data=build(json.loads(args.input.read_text(encoding='utf-8-sig')),args.output,args.template)
    except (ValueError,KeyError,OSError,zipfile.BadZipFile) as error:parser.exit(1,str(error)+'\n')
    print('Created '+str(args.output))
    for note in data.get('language_review',[]):print('Language review: '+note,file=sys.stderr)

if __name__=='__main__': main()
