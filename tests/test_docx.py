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
  original['experience'][0]['bullets'].append('R&D <systems> "quoted" — café\nSecond line')
  expected=sum(len(x['bullets']) for x in original['experience']+original['skills'])+sum(len(original[k]) for k in ['education','certifications','languages'])
  for layout in ['mm','dp']:
   with self.subTest(layout=layout),tempfile.TemporaryDirectory() as tmp:
    output=Path(tmp)/'cv.docx';builder.build(original,output,layout)
    template=SKILL/'assets'/('BTO_CV_Template_DP.docx' if layout=='dp' else 'BTO_CV_Template.docx')
    with zipfile.ZipFile(template) as source,zipfile.ZipFile(output) as result:
     self.assertEqual(set(source.namelist()),set(result.namelist()))
     for name in source.namelist():
      if name!='word/document.xml':self.assertEqual(source.read(name),result.read(name),name)
     doc=minidom.parseString(result.read('word/document.xml'));base=minidom.parseString(source.read('word/document.xml'))
     self.assertEqual(doc.getElementsByTagNameNS(W,'sectPr')[0].toxml(),base.getElementsByTagNameNS(W,'sectPr')[0].toxml())
     self.assertEqual(len(doc.getElementsByTagNameNS(W,'numPr')),expected)
     self.assertEqual(len(doc.getElementsByTagNameNS(W,'drawing')),1)
     content=builder.text(doc);self.assertIn('R&D <systems> "quoted" — café',content);self.assertNotIn('{{',content)
     nums=minidom.parseString(result.read('word/numbering.xml'))
     num={x.getAttribute('w:numId'):x.getElementsByTagNameNS(W,'abstractNumId')[0].getAttribute('w:val') for x in nums.getElementsByTagNameNS(W,'num')}
     abstracts={x.getAttribute('w:abstractNumId'):x for x in nums.getElementsByTagNameNS(W,'abstractNum')}
     for p in doc.getElementsByTagNameNS(W,'numPr'):
      identifier=p.getElementsByTagNameNS(W,'numId')[0].getAttribute('w:val');level=abstracts[num[identifier]].getElementsByTagNameNS(W,'lvl')[0]
      self.assertEqual(level.getElementsByTagNameNS(W,'numFmt')[0].getAttribute('w:val'),'bullet')
      self.assertEqual(level.getElementsByTagNameNS(W,'lvlText')[0].getAttribute('w:val'),'\u25aa')
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
