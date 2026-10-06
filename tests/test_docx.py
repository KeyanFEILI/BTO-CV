import hashlib,importlib.util,json,tempfile,unittest,zipfile
from unittest.mock import patch
from pathlib import Path
from xml.dom import minidom
ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills/bto-cv'
spec=importlib.util.spec_from_file_location('builder',SKILL/'scripts/build_docx.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
W=builder.W
class NativeWordTests(unittest.TestCase):
 def test_language_display_mapping_and_retention(self):
  for source,expected in [('Native','Native'),('mother tongue','Native'),('Fluent','Fluent'),('C1','Fluent'),('C2','Fluent'),('B2','Full Professional'),('Basic','Professional'),('A1','Professional'),('A2','Professional'),('B1','Professional')]:
   for entry in ['French - '+source,'French ('+source+')','French: '+source.lower()]:
    with self.subTest(entry=entry):self.assertEqual(builder.language_label(entry),'French ('+expected+')')
  data={'initials':'T.E.','languages':['French (Native)','English - C2','Spanish - A1','German - B1','Italian - B2','Japanese','Dutch - Intermediate','Portuguese - C2 (Business certified)','French - B1 (DELF certified)']}
  expected=['French (Native)','English (Fluent)','Spanish (Professional)','German (Professional)','Italian (Full Professional)','Japanese','Dutch - Intermediate','Portuguese (Fluent) (Business certified)','French (Professional) (DELF certified)']
  self.assertEqual(builder.normalize(data)['languages'],expected)
  self.assertEqual(builder.language_label('French (CEFR B1)'),'French (Professional)')
  self.assertEqual(builder.language_label('English (Fluent / C2)'),'English (Fluent)')
  self.assertEqual(builder.normalize(dict(data,languages=expected))['languages'],expected)
  with tempfile.TemporaryDirectory() as tmp:
   output=Path(tmp)/'cv.docx';builder.build(data,output)
   with zipfile.ZipFile(output) as z:doc=minidom.parseString(z.read('word/document.xml'))
   paras=doc.getElementsByTagNameNS(W,'p')
   self.assertEqual([builder.text(p) for p in paras if p.getElementsByTagNameNS(W,'numPr')],expected)
 def test_exact_blank_lines_for_jobs_and_optional_sections(self):
  for mask in range(32):
   data={'initials':'T.E.'}
   sections=[('experience',[{'dates':'2025','role':'First','bullets':['A']},{'employer':'Second','bullets':[]},{'bullets':['B']}]),('education',['Degree']),('skills',[{'category':'Tools','bullets':['SQL']}]),('certifications',['Certificate']),('languages',['English'])]
   expected=['T.E.',''];populated=False
   for i,(key,value) in enumerate(sections):
    if not mask & (1<<i):continue
    data[key]=value
    if populated:expected+=['','']
    expected+=[builder.HEADINGS[i]];populated=True
    expected+=([ '2025','First','Main responsibilities:','A','','Second','','Main responsibilities:','B'] if key=='experience' else ['Tools','SQL'] if key=='skills' else value)
   if not populated:continue
   with self.subTest(mask=mask),tempfile.TemporaryDirectory() as tmp:
    output=Path(tmp)/'cv.docx';builder.build(data,output)
    with zipfile.ZipFile(output) as z:doc=minidom.parseString(z.read('word/document.xml'))
    paras=builder.children(doc.getElementsByTagNameNS(W,'body')[0],'p')[1:]
    self.assertEqual([builder.text(p) for p in paras],expected)
    for p in paras:
     if builder.text(p):continue
     self.assertFalse(p.getElementsByTagNameNS(W,'numPr'))
     self.assertFalse(builder.children(p,'r'))
     self.assertTrue(p.getElementsByTagNameNS(W,'keepNext'))
     spacing=p.getElementsByTagNameNS(W,'spacing')[0]
     self.assertEqual([spacing.getAttribute('w:'+a) for a in ['before','after','line']],['0','120' if p is paras[1] else '0','240'])
     self.assertEqual(p.getElementsByTagNameNS(W,'sz')[0].getAttribute('w:val'),'22')

 def test_installed_pair_generates_offline_from_any_working_directory(self):
  data=json.loads((SKILL/'references/input-example.json').read_text())
  with tempfile.TemporaryDirectory() as tmp:
   output=Path(tmp)/'cv.docx'
   # Neither a current checkout nor Git credentials are needed for conversion.
   import os
   previous=Path.cwd()
   try:
    os.chdir(tmp)
    with patch('socket.create_connection',side_effect=AssertionError('Network used')),patch('subprocess.run',side_effect=AssertionError('Git/CLI used')):
     builder.build(data,output)
   finally:os.chdir(previous)
   with zipfile.ZipFile(output) as z:
    content=builder.text(minidom.parseString(z.read('word/document.xml')))
    self.assertIn('Product Owner',content);self.assertNotIn('{{',content)

 def test_incompatible_external_master_can_recover_with_installed_pair(self):
  data={'initials':'A.E.','languages':['English']}
  with tempfile.TemporaryDirectory() as tmp:
   template=Path(tmp)/'external.docx';output=Path(tmp)/'cv.docx'
   with zipfile.ZipFile(SKILL/'assets/BTO_CV_Template.docx') as src,zipfile.ZipFile(template,'w') as dst:
    for name in src.namelist():dst.writestr(name,src.read(name).replace(b'{{layout_rr_afr_v2}}',b'{{other_release}}') if name=='word/document.xml' else src.read(name))
   with self.assertRaisesRegex(ValueError,'omit --template'):
    builder.build(data,output,template)
   self.assertFalse(output.exists())
   builder.build(data,output)
   with zipfile.ZipFile(output) as z:
    content=builder.text(minidom.parseString(z.read('word/document.xml')))
    self.assertIn('English',content);self.assertNotIn('other_release',content)

 def test_reference_banner_fonts_numbering_and_margins(self):
  with zipfile.ZipFile(SKILL/'assets/BTO_CV_Template.docx') as z:
   self.assertEqual(hashlib.sha256(z.read('word/media/image1.png')).hexdigest(),'aaa03ec16e78150da31f576946e12651c07167defe1b03fc382d9d9146b12cfc')
   doc=minidom.parseString(z.read('word/document.xml'))
   extent=doc.getElementsByTagNameNS('http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','extent')[0]
   self.assertEqual((extent.getAttribute('cx'),extent.getAttribute('cy')),('6172200','789232'))
   margin=doc.getElementsByTagNameNS(W,'pgMar')[0]
   self.assertEqual([margin.getAttribute('w:'+k) for k in ['top','right','bottom','left']],['850','1134','709','1134'])
   styles=minidom.parseString(z.read('word/styles.xml'))
   normal=next(n for n in styles.getElementsByTagNameNS(W,'style') if n.getAttribute('w:styleId')=='Normal')
   self.assertEqual(normal.getElementsByTagNameNS(W,'rFonts')[0].getAttribute('w:ascii'),'Century Gothic')
   nums=minidom.parseString(z.read('word/numbering.xml'))
   abstract=next(n for n in nums.getElementsByTagNameNS(W,'abstractNum') if n.getAttribute('w:abstractNumId')=='10')
   ind=abstract.getElementsByTagNameNS(W,'lvl')[0].getElementsByTagNameNS(W,'ind')[0]
   self.assertEqual((ind.getAttribute('w:left'),ind.getAttribute('w:hanging')),('360','360'))
   for p in doc.getElementsByTagNameNS(W,'p'):
    if builder.text(p) in builder.HEADINGS:
     self.assertEqual(p.getElementsByTagNameNS(W,'color')[0].getAttribute('w:val'),'00665F')
     self.assertEqual(p.getElementsByTagNameNS(W,'sz')[0].getAttribute('w:val'),'26')

 def test_long_content_and_missing_dates_preserved(self):
  bullets=[('Responsibility '+str(i)+' '+('long editable text ' * 20)).strip() for i in range(80)]
  data={'initials':'T.E.','experience':[{'dates':'2025','role':'One','bullets':bullets},{'role':'Two','bullets':['Final']},{'bullets':['Undated role']}],'languages':['English']}
  with tempfile.TemporaryDirectory() as tmp:
   output=Path(tmp)/'cv.docx';builder.build(data,output)
   with zipfile.ZipFile(output) as z:doc=minidom.parseString(z.read('word/document.xml'))
   paras=builder.children(doc.getElementsByTagNameNS(W,'body')[0],'p')
   self.assertEqual([builder.text(p) for p in paras if p.getElementsByTagNameNS(W,'numPr')],bullets+['Final','Undated role','English'])
   for label in ['Two','Main responsibilities:']:
    if label=='Two':p=next(p for p in paras if builder.text(p)==label)
    else:p=[p for p in paras if builder.text(p)==label][-1]
    self.assertEqual(builder.text(paras[list(paras).index(p)-1]),'')
   self.assertFalse(doc.getElementsByTagNameNS(W,'pageBreakBefore'))
   self.assertFalse(doc.getElementsByTagNameNS(W,'br'))

 def test_reject_typed_markers_and_invalid_unicode(self):
  for value in ['\u25aa item','\u2022 item','- item','* item','bad\ud800','bad\uffff']:
   with self.subTest(value=repr(value)),self.assertRaises(ValueError):
    builder.normalize({'initials':'A.E.','languages':[value]})
  self.assertEqual(builder.normalize({'initials':'A.E.','languages':['C++; C#; *SQL*']})['languages'],['C++; C#; *SQL*'])

 def test_reject_broken_native_lists_before_writing(self):
  with tempfile.TemporaryDirectory() as tmp:
   template=Path(tmp)/'broken.docx';output=Path(tmp)/'cv.docx'
   for mutation in ['glyph','reference','override']:
    with self.subTest(mutation=mutation):
     with zipfile.ZipFile(SKILL/'assets/BTO_CV_Template.docx') as src,zipfile.ZipFile(template,'w') as dst:
      for name in src.namelist():
       content=src.read(name)
       if name=='word/numbering.xml':
        doc=minidom.parseString(content)
        if mutation=='glyph':
         for n in doc.getElementsByTagNameNS(W,'lvlText'):n.setAttribute('w:val','\u2022')
        else:
         num=next(n for n in doc.getElementsByTagNameNS(W,'num') if n.getAttribute('w:numId')=='9')
         if mutation=='reference':num.getElementsByTagNameNS(W,'abstractNumId')[0].setAttribute('w:val','999')
         else:
          override=minidom.parseString('<w:lvlOverride xmlns:w="'+W+'" w:ilvl="0"><w:lvl w:ilvl="0"><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/></w:lvl></w:lvlOverride>').documentElement
          num.appendChild(doc.importNode(override,True))
        content=doc.toxml(encoding='UTF-8')
       dst.writestr(name,content)
     with self.assertRaisesRegex(ValueError,'Template native square list invalid'):
      builder.build({'initials':'A.E.','languages':['English']},output,template)
     self.assertFalse(output.exists())

 def test_content_fidelity_and_pagination_properties(self):
  data={'initials':'A.E.','experience':[{'dates':'2025','role':'D\u00e9veloppeur & analyst','bullets':['Built <tools>\nUsed SQL']},{'employer':'Client','bullets':[]}], 'education':['Degree 2022'], 'skills':[{'category':'Tools','bullets':['C++; SQL']}], 'languages':['French']}
  with tempfile.TemporaryDirectory() as tmp:
   output=Path(tmp)/'cv.docx';builder.build(data,output)
   with zipfile.ZipFile(output) as z:doc=minidom.parseString(z.read('word/document.xml'))
   paras=builder.children(doc.getElementsByTagNameNS(W,'body')[0],'p')
   actual=[builder.text(p) for p in paras if builder.text(p)]
   self.assertEqual(actual,['A.E.','WORK EXPERIENCE','2025','D\u00e9veloppeur & analyst','Main responsibilities:','Built <tools>Used SQL','Client','EDUCATION','Degree 2022','IT SKILLS','Tools','C++; SQL','LANGUAGES','French'])
   with zipfile.ZipFile(SKILL/'assets/BTO_CV_Template.docx') as z:base=minidom.parseString(z.read('word/document.xml'))
   prototypes={builder.text(p):p for p in builder.children(base.getElementsByTagNameNS(W,'body')[0],'p')}
   for p in paras:
    content=builder.text(p)
    if content in builder.HEADINGS:self.assertTrue(p.getElementsByTagNameNS(W,'keepNext'),content)
    if p.getElementsByTagNameNS(W,'numPr'):self.assertTrue(p.getElementsByTagNameNS(W,'keepLines'),content)
   for content,slot in [('2025','dates'),('D\u00e9veloppeur & analyst','role'),('Tools','skill_category')]:
    p=next(p for p in paras if builder.text(p)==content)
    self.assertEqual(builder.children(p,'pPr')[0].toxml(),builder.children(prototypes['{{'+slot+'}}'],'pPr')[0].toxml())

 def test_native_lists_and_unchanged_design(self):
  original=json.loads((SKILL/'references/input-example.json').read_text())
  original['experience'][0]['bullets'].append('R&D <systems> "quoted" â€” cafÃ©\nSecond line')
  expected=sum(len(x['bullets']) for x in original['experience']+original['skills'])+sum(len(original[k]) for k in ['education','certifications','languages'])
  for layout in ['rr_afr']:
   with self.subTest(layout=layout),tempfile.TemporaryDirectory() as tmp:
    output=Path(tmp)/'cv.docx';builder.build(original,output)
    template=SKILL/'assets'/'BTO_CV_Template.docx'
    with zipfile.ZipFile(template) as source,zipfile.ZipFile(output) as result:
     self.assertEqual(set(source.namelist()),set(result.namelist()))
     for name in source.namelist():
      if name!='word/document.xml':self.assertEqual(source.read(name),result.read(name),name)
     doc=minidom.parseString(result.read('word/document.xml'));base=minidom.parseString(source.read('word/document.xml'))
     self.assertEqual(doc.getElementsByTagNameNS(W,'sectPr')[0].toxml(),base.getElementsByTagNameNS(W,'sectPr')[0].toxml())
     self.assertEqual(len(doc.getElementsByTagNameNS(W,'numPr')),expected)
     self.assertEqual(len(doc.getElementsByTagNameNS(W,'drawing')),1)
     content=builder.text(doc);self.assertIn('R&D <systems> "quoted" â€” cafÃ©',content);self.assertNotIn('{{',content)
     nums=minidom.parseString(result.read('word/numbering.xml'))
     num={x.getAttribute('w:numId'):x.getElementsByTagNameNS(W,'abstractNumId')[0].getAttribute('w:val') for x in nums.getElementsByTagNameNS(W,'num')}
     abstracts={x.getAttribute('w:abstractNumId'):x for x in nums.getElementsByTagNameNS(W,'abstractNum')}
     for p in doc.getElementsByTagNameNS(W,'numPr'):
      identifier=p.getElementsByTagNameNS(W,'numId')[0].getAttribute('w:val');level=abstracts[num[identifier]].getElementsByTagNameNS(W,'lvl')[0]
      self.assertEqual(level.getElementsByTagNameNS(W,'numFmt')[0].getAttribute('w:val'),'bullet')
      self.assertEqual(level.getElementsByTagNameNS(W,'lvlText')[0].getAttribute('w:val'),'\uf0a7')
      self.assertEqual(level.getElementsByTagNameNS(W,'rFonts')[0].getAttribute('w:ascii'),'Wingdings')
 def test_rr_afr_alignment_and_spacing(self):
  data={'initials':'A.E.','experience':[{'dates':'2025','role':'First role','employer':'One','bullets':['First','Last']},{'dates':'2024','role':'Second role','employer':'Two','bullets':['Next']}],'languages':['English']}
  with tempfile.TemporaryDirectory() as tmp:
   output=Path(tmp)/'cv.docx';builder.build(data,output)
   with zipfile.ZipFile(output) as z:doc=minidom.parseString(z.read('word/document.xml'))
   paras=doc.getElementsByTagNameNS(W,'p');bytext={builder.text(p):p for p in paras}
   for key in ['2025','First role','One','2024','Second role','Two','WORK EXPERIENCE','LANGUAGES','A.E.']:
    self.assertFalse(bytext[key].getElementsByTagNameNS(W,'ind'),key)
   self.assertFalse(bytext['Last'].getElementsByTagNameNS(W,'br'))
   self.assertEqual(builder.text(paras[list(paras).index(bytext['2024'])-1]),'')
   idx=list(paras).index(bytext['WORK EXPERIENCE'])
   self.assertEqual(builder.text(paras[idx+1]),'2025')
   spacing=bytext['WORK EXPERIENCE'].getElementsByTagNameNS(W,'spacing')[0]
   self.assertEqual(spacing.getAttribute('w:before'),'0');self.assertEqual(spacing.getAttribute('w:after'),'80')
   section=doc.getElementsByTagNameNS(W,'pgSz')[0]
   self.assertEqual(section.getAttribute('w:w'),'11906');self.assertEqual(section.getAttribute('w:h'),'16838')
   for p in paras:
    if p.getElementsByTagNameNS(W,'numPr'):
     spacing=p.getElementsByTagNameNS(W,'spacing')[0]
     self.assertEqual(spacing.getAttribute('w:after'),'10');self.assertEqual(spacing.getAttribute('w:line'),'228')
 def test_reject_legacy_master(self):
  with tempfile.TemporaryDirectory() as tmp:
   template=Path(tmp)/'legacy.docx'
   with zipfile.ZipFile(SKILL/'assets/BTO_CV_Template.docx') as src,zipfile.ZipFile(template,'w') as dst:
    for name in src.namelist():dst.writestr(name,src.read(name).replace(b'{{layout_rr_afr_v2}}',b'{{legacy_layout}}') if name=='word/document.xml' else src.read(name))
   with self.assertRaisesRegex(ValueError,'Template slot missing'):
    builder.build({'initials':'A.E.','languages':['English']},Path(tmp)/'cv.docx',template)
 def test_missing_sections_and_no_overwrite(self):
  with tempfile.TemporaryDirectory() as tmp:
   output=Path(tmp)/'cv.docx';builder.build({'initials':'A.E.','languages':['English']},output)
   with zipfile.ZipFile(output) as z:
    content=builder.text(minidom.parseString(z.read('word/document.xml')))
    self.assertIn('LANGUAGES',content);self.assertNotIn('WORK EXPERIENCE',content)
   with self.assertRaises(FileExistsError):builder.build({'initials':'A.E.','languages':['English']},output)
 def test_reject_unmapped_or_invalid_data(self):
  for data in [{'initials':'A.E.','unknown':'value'},{'initials':'A.E.','languages':'English'},{'initials':'A.E.','languages':['bad\x00text']},{'initials':'A.E.'}]:
   with self.subTest(data=data),self.assertRaises(ValueError):builder.normalize(data)
if __name__=='__main__':unittest.main()
