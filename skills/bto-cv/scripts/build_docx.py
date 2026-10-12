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

LANGUAGE_LEVELS={
    'native':'Native','mother tongue':'Native','bilingual':'Native','bilingue':'Native',
    'langue maternelle':'Native','fluent':'Fluent','courant':'Fluent','usage courant':'Fluent',
    'c1':'Fluent','c2':'Fluent','b2':'Professional','basic':'Professional',
    'a1':'Professional','a2':'Professional','b1':'Professional','professional':'Professional',
    'full professional':'Professional','intermediate':'Professional','notions':'Professional',
    'bonnes notions':'Professional','très bonnes notions':'Professional',
}
LEVEL_PATTERN=r'\b(?:'+ '|'.join(re.escape(k) for k in sorted(LANGUAGE_LEVELS,key=len,reverse=True))+r')\b'
EXAM_PATTERN=r'\b(?:IELTS|TOEFL|TOEIC|DELF|DALF|DILF|TCF|TEF|Cambridge|Goethe|TestDaF|telc|DELE|SIELE|CELI|CILS|HSK|JLPT|OET|PTE|Duolingo|Linguaskill|FCE|CAE|CPE|BULATS|certificat\w*|certified|exam\w*|test|diploma|score)\b'

def language_parts(value):
    """Separate explicit proficiency from supplied exams; never infer a level from a score."""
    boundary=re.search(r'\(|:|\s+[-\u2013\u2014]\s*|[-\u2013\u2014](?=(?:CEFR\s+)?'+LEVEL_PATTERN+r')',value,re.I)
    if boundary is None:
        boundary=re.search(r'\s+(?=(?:CEFR\s+)?'+LEVEL_PATTERN+r')',value,re.I)
    if boundary is None:
        boundary=re.search(r'\s+(?='+EXAM_PATTERN+r')',value,re.I)
    if boundary is None:return value,[]
    name=value[:boundary.start()].strip()
    if not name:raise ValueError('Language name missing: '+value)
    remainder=value[boundary.start():].strip(' :-\u2013\u2014')
    # Keep entire exam notes, including CEFR exam names, scores and dates.
    chunks=re.findall(r'\(([^()]*)\)|([^()]+)',remainder)
    if re.sub(r'\([^()]*\)|[^()]+','',remainder):
        raise ValueError('Unclear language parentheses; separate proficiency and certifications: '+value)
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
    has_level=any(re.search(LEVEL_PATTERN,part,re.I) for part in proficiency)
    for part in proficiency:
        matches=list(re.finditer(LEVEL_PATTERN,part,re.I))
        mapped.extend(LANGUAGE_LEVELS[m.group().lower()] for m in matches)
        residue=re.sub(LEVEL_PATTERN,'',part,flags=re.I)
        # Only remove wrappers around a recognized level. Unknown descriptions
        # must never be silently shortened (e.g. "Working proficiency" -> "Working").
        residue=re.sub(r'\b(?:CEFR|level|proficiency|proficient)\b','',residue,flags=re.I).strip(' /,;:-') if has_level else part.strip()
        if residue:unknown.append(residue)
    if len(set(mapped))>1 or (mapped and unknown) or len(unknown)>1:
        raise ValueError('Ambiguous language proficiency; resolve from the original CV: '+value)
    if unknown:
        raise ValueError('Unmapped language proficiency; supply Native, Fluent or Professional using source evidence or an explicit user instruction: '+value)
    level=mapped[0] if mapped else ''
    return name+(' ('+level+')' if level else ''),certifications

def language_label(value):
    return language_parts(value)[0]

MONTHS={}
for number,names in enumerate([
    'january janvier jan', 'february février fevrier feb', 'march mars mar',
    'april avril apr', 'may mai', 'june juin jun', 'july juillet jul',
    'august août aout aug', 'september septembre sep sept',
    'october octobre oct', 'november novembre nov', 'december décembre decembre dec',
],1):
    MONTHS.update((name,number) for name in names.split())

def date_parts(value):
    """Return known (month, year); do not manufacture missing precision."""
    value=value.strip().rstrip('.').casefold()
    if value in {'present','current','ongoing','now','présent','actuel','à ce jour',"aujourd'hui",'en cours'}:
        return 'Present'
    match=re.fullmatch(r'(?:(\d{1,2})/)?(\d{4})',value)
    if match:
        month=int(match[1]) if match[1] else None
        year=int(match[2])
    else:
        match=re.fullmatch(r'(\d{1,2})/(\d{1,2})/(\d{4})',value)
        if match:
            from datetime import date
            try:date(int(match[3]),int(match[2]),int(match[1]))
            except ValueError:raise ValueError('Invalid calendar date: '+value) from None
            month,year=int(match[2]),int(match[3])
        else:
            match=re.fullmatch(r'([^\d]+?)(?:\s+(\d{4}))?',value)
            if not match or match[1].strip().rstrip('.') not in MONTHS:
                raise ValueError('Unrecognized date; use MM/YYYY or preserve supplied years: '+value)
            month=MONTHS[match[1].strip().rstrip('.')]
            year=int(match[2]) if match[2] else None
    if month is not None and not 1<=month<=12:raise ValueError('Invalid month: '+value)
    if year is not None and not 1<=year<=9999:raise ValueError('Invalid year: '+value)
    return month,year

def date_label(value):
    if not value.strip():return ''
    value=re.sub(r'^(?:from\s+|de\s+|d[’\x27])','',value.strip(),flags=re.I).rstrip('.').strip()
    endpoints=re.split(r'\s*[-–—]\s*|\s+(?:to|à|au)\s+',value,flags=re.I)
    if len(endpoints)>2:raise ValueError('Unrecognized date range: '+value)
    parts=[date_parts(v) for v in endpoints]
    if parts[0]=='Present' and len(parts)>1:raise ValueError('Present cannot start a date range: '+value)
    # "March - May 2019" explicitly supplies a shared year; no missing month is inferred.
    if len(parts)==2:
        for i in range(2):
            other=parts[1-i]
            if parts[i]!='Present' and parts[i][1] is None and other!='Present' and other[1] is not None:
                parts[i]=(parts[i][0],other[1])
    for part in parts:
        if part!='Present' and part[1] is None:raise ValueError('Date year missing: '+value)
    if len(parts)==2 and parts[1]!='Present':
        start,end=parts
        if start[1]>end[1] or (start[1]==end[1] and start[0] and end[0] and start[0]>end[0]):
            raise ValueError('Date range ends before it starts: '+value)
    return ' - '.join('Present' if p=='Present' else (f'{p[0]:02d}/' if p[0] else '')+str(p[1]) for p in parts)

# Dates are metadata only at an entry boundary. Scores, product/version numbers,
# dates embedded in a qualification name, and certification status remain intact.
DATE_TOKEN=r'(?:\d{1,2}/\d{1,2}/\d{4}|\d{1,2}/\d{4}|\d{4})'
DATE_RANGE=DATE_TOKEN+r'(?:\s*[-–—]\s*(?:'+DATE_TOKEN+r'|Present))?'

def qualification_label(value):
    """Move explicit boundary dates to the end, preserving names, locations and status."""
    if '|' in value:
        content,dates=value.rsplit('|',1)
        if not content.strip():raise ValueError('Qualification content missing: '+value)
        if not dates.strip():raise ValueError('Qualification date missing after |: '+value)
        return content.strip()+' | '+date_label(dates)
    prefix=re.match(r'^('+DATE_RANGE+r')\s*:\s*(.+)$',value,re.I)
    if prefix:return prefix[2].strip().rstrip('.')+' | '+date_label(prefix[1])
    # Only explicit punctuation marks a trailing metadata date. A bare year can
    # belong to a certificate title such as "Windows Server 2022".
    suffix=re.search(r'(?:\s*[,;]\s*|\s*\(\s*)('+DATE_RANGE+r')\s*\)?\.?$',value,re.I)
    if suffix and value[:suffix.start()].strip():
        content=value[:suffix.start()].strip().rstrip('.')
        # Preserve enclosing score/status parentheses when the date was inside
        # them: IELTS (8.0, 2024) -> IELTS (8.0) | 2024.
        closing=len(re.findall(r'\)',value[suffix.start():]))
        content+=')'*min(closing,max(0,content.count('(')-content.count(')')))
        return content+' | '+date_label(suffix[1])
    # No source date or location? Do not create a date, placeholder, or diploma.
    return value

def responsibility_list(values):
    seen=set()
    for value in values:
        if re.match(r'^(?:(?:objective|objectif)(?:\s+(?:project|projet)(?:\s+IAM)?(?:\s+\d+)?)?|main responsibilities|activités récurrentes|recurring activities|interest|intérêt)\s*(?::|$)',value,re.I):
            raise ValueError('Redundant responsibility label; integrate its source content into the relevant responsibility: '+value)
        key=re.sub(r'\s+',' ',value).casefold().rstrip(' .;')
        if key in seen:raise ValueError('Duplicate responsibility; consolidate only within the same project or clarify distinct project scope: '+value)
        seen.add(key)
    return values

def validate_lists(prototypes, parts, slots=None):
    """Fail before writing if any list slot has lost its native square numbering."""
    numbering=minidom.parseString(parts['word/numbering.xml'])
    nums={n.getAttributeNS(W,'numId'):n for n in children(numbering.documentElement,'num')}
    abstracts={n.getAttributeNS(W,'abstractNumId'):n for n in children(numbering.documentElement,'abstractNum')}
    for slot in slots if slots is not None else ['experience_bullet','education_bullet','skill_bullet','certification_bullet','language_bullet']:
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
    allowed={'initials','experience','education','skills','certifications','languages'}
    unknown=set(data)-allowed
    if unknown: raise ValueError('Unmapped fields: '+', '.join(sorted(unknown)))
    result={'initials':string(data.get('initials'),'initials')}
    for key in ['education','certifications','languages']:
        result[key]=strings(data.get(key,[]),key)
    languages=[]
    for value in result['languages']:
        label,certifications=language_parts(value)
        languages.append(label)
        for certificate in certifications:
            if certificate.casefold() not in {v.casefold() for v in result['certifications']}:
                result['certifications'].append(certificate)
    result['languages']=languages
    result['education']=[qualification_label(v) for v in result['education']]
    result['certifications']=[qualification_label(v) for v in result['certifications']]
    # Exam annotations can match existing entries only after date normalization.
    result['certifications']=list({v.casefold():v for v in reversed(result['certifications'])}.values())[::-1]
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
            if key=='experience':
                record['dates']=date_label(record['dates'])
                record['bullets']=responsibility_list(record['bullets'])
            if not any(record.values()): raise ValueError('Empty '+key+' entry')
            result[key].append(record)
    if len(result['skills'])>4:
        raise ValueError('IT SKILLS supports at most four groups; consolidate categories without dropping tools or methods')
    if not any(result[k] for k in allowed-{'initials'}): raise ValueError('No CV content supplied')
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
    parser.add_argument('output',type=Path,nargs='?',help='New .docx output file')
    parser.add_argument('--template',type=Path,help='Explicit approved DOCX master')
    parser.add_argument('--check',action='store_true',help='Validate and normalize input without writing a document')
    args=parser.parse_args()
    if not args.check and args.output is None:parser.error('output is required unless --check is used')
    if args.check and args.output is not None:parser.error('--check does not accept an output path')
    try:
        data=json.loads(args.input.read_text(encoding='utf-8-sig'))
        if args.check:normalize(data)
        else:build(data,args.output,args.template)
    except (ValueError,KeyError,OSError,zipfile.BadZipFile) as error:parser.exit(1,str(error)+'\n')
    print('Input checks passed' if args.check else 'Created '+str(args.output))

if __name__=='__main__': main()
