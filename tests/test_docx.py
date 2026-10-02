import importlib.util,json,tempfile,unittest,zipfile
from pathlib import Path
from xml.dom import minidom
ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills/bto-cv'
spec=importlib.util.spec_from_file_location('builder',SKILL/'scripts/build_docx.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
W=builder.W
class NativeWordTests(unittest.TestCase):
 def test_native_lists_and_unchanged_design(self):
  original=json.loads((SKILL/'references/input-example.json').read_text())
  original['experience'][0]['bullets'].append('R&D <systems> "quoted" â€” cafÃ©\nSecond line')
  expected=sum(len(x['bullets']) for x in original['experience']+original['skills'])+sum(len(original[k]) for k in ['education','certifications','languages'])
  for layout in ['dp']:
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
      self.assertEqual(level.getElementsByTagNameNS(W,'lvlText')[0].getAttribute('w:val'),'\u25aa')
 def test_dp_alignment_and_spacing(self):
  data={'initials':'A.E.','experience':[{'dates':'2025','role':'First role','employer':'One','bullets':['First','Last']},{'dates':'2024','role':'Second role','employer':'Two','bullets':['Next']}],'languages':['English']}
  with tempfile.TemporaryDirectory() as tmp:
   output=Path(tmp)/'cv.docx';builder.build(data,output)
   with zipfile.ZipFile(output) as z:doc=minidom.parseString(z.read('word/document.xml'))
   paras=doc.getElementsByTagNameNS(W,'p');bytext={builder.text(p):p for p in paras}
   for key in ['2025','First role','One']:
    ind=bytext[key].getElementsByTagNameNS(W,'ind')[0]
    self.assertEqual(ind.getAttribute('w:left'),'426');self.assertEqual(ind.getAttribute('w:hanging'),'284')
   for key in ['2024','Second role','Two','WORK EXPERIENCE','LANGUAGES','A.E.']:
    self.assertFalse(bytext[key].getElementsByTagNameNS(W,'ind'),key)
   self.assertEqual(len(bytext['Last'].getElementsByTagNameNS(W,'br')),1)
   idx=list(paras).index(bytext['WORK EXPERIENCE']);blank=paras[idx+1]
   self.assertEqual(builder.text(blank),'');self.assertFalse(builder.children(blank,'r'))
   self.assertEqual(blank.getElementsByTagNameNS(W,'sz')[0].getAttribute('w:val'),'26')
   for p in paras:
    if p.getElementsByTagNameNS(W,'numPr'):
     ind=p.getElementsByTagNameNS(W,'ind')[0]
     self.assertEqual(ind.getAttribute('w:left'),'567');self.assertEqual(ind.getAttribute('w:hanging'),'387')
 def test_reject_legacy_master(self):
  with tempfile.TemporaryDirectory() as tmp:
   template=Path(tmp)/'legacy.docx'
   with zipfile.ZipFile(SKILL/'assets/BTO_CV_Template.docx') as src,zipfile.ZipFile(template,'w') as dst:
    for name in src.namelist():dst.writestr(name,src.read(name).replace(b'{{first_dates}}',b'{{legacy_dates}}') if name=='word/document.xml' else src.read(name))
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
