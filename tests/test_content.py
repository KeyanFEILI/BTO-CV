"""Fictional regressions for the content rules; no candidate data or network."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from xml.dom import minidom

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'skills/bto-cv/scripts'
def load(name):
    spec=importlib.util.spec_from_file_location(name,SCRIPTS/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
builder=load('build_docx')
verifier=load('verify_docx')
extractor=load('extract_text')

class ContentTests(unittest.TestCase):
    def test_utf8_extraction_retains_docx_paragraphs_and_tables(self):
        xml='<w:document xmlns:w="'+builder.W+'"><w:body><w:p><w:r><w:t>Example résumé</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Client A &amp; B</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>'
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'source.docx'
            with zipfile.ZipFile(source,'w') as z:z.writestr('word/document.xml',xml.encode('utf-8'))
            self.assertEqual(extractor.extract(source),'Example résumé\nClient A & B')
            textfile=Path(tmp)/'source.txt';textfile.write_text('Example résumé',encoding='utf-8-sig')
            self.assertEqual(extractor.extract(textfile),'Example résumé')

    def test_experience_dates_in_english_french_and_numeric(self):
        cases={
            'January 2025 - Present':'01/2025 - Present',
            'De Janvier 2026 à Mai 2026':'01/2026 - 05/2026',
            'D’Octobre 2023 à Février 2025':'10/2023 - 02/2025',
            'De Mars à Mai 2019':'03/2019 - 05/2019',
            'March - May 2019':'03/2019 - 05/2019',
            '5/2019 – 9/2020':'05/2019 - 09/2020',
            '15/05/2019 - 30/09/2020':'05/2019 - 09/2020',
            '2021 - 2024':'2021 - 2024',
            '2021 - 05/2024':'2021 - 05/2024',
            '2025':'2025', '':'',
        }
        for raw,expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(builder.date_label(raw),expected)
                self.assertEqual(builder.date_label(expected),expected)

    def test_missing_or_invalid_date_precision_is_not_invented(self):
        for raw in ['March - May','13/2025','00/2025','2024 - 2023',
                    '10/2025 - 02/2025','31/02/2024','Present - 2025','2025 - 02/0000']:
            with self.subTest(raw=raw),self.assertRaises(ValueError):builder.date_label(raw)

    def test_qualification_date_placement_preserves_names_locations_status_and_scores(self):
        cases={
            '2020: Example Certificate, Example City.':'Example Certificate, Example City | 2020',
            '2009 – 2011: Example School, Example City':'Example School, Example City | 2009 - 2011',
            'MSc Computer Science, Example University, Example City | 2024 - 2026':'MSc Computer Science, Example University, Example City | 2024 - 2026',
            'Example Training, Example City, 2022':'Example Training, Example City | 2022',
            'English - IELTS 8.0, 2024':'English - IELTS 8.0 | 2024',
            'English - IELTS (8.0, 2024)':'English - IELTS (8.0) | 2024',
            'German - Goethe-Zertifikat B2, pending, 2024':'German - Goethe-Zertifikat B2, pending | 2024',
            'Example course (2023)':'Example course | 2023',
            'Windows Server 2022':'Windows Server 2022',
            'ISO 27001 Lead Implementor, Example City':'ISO 27001 Lead Implementor, Example City',
        }
        for raw,expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(builder.qualification_label(raw),expected)
                self.assertEqual(builder.qualification_label(expected),expected)

    def test_school_only_does_not_gain_an_invented_diploma_or_studies(self):
        result=builder.normalize({'initials':'T.E.','education':['2009 - 2011: Example School, Example City']})
        self.assertEqual(result['education'],['Example School, Example City | 2009 - 2011'])
        for value in ['Example School |','| 2022']:
            with self.subTest(value=value),self.assertRaises(ValueError):builder.qualification_label(value)

    def test_all_proficiency_labels_and_french_conventions(self):
        for raw,expected in [('Bilingue','Native'),('Bilingual','Native'),('langue maternelle','Native'),
                             ('Usage courant','Fluent'),('courant','Fluent'),('C2','Fluent'),
                             ('B2','Professional'),('Full Professional','Professional'),
                             ('Intermediate','Professional'),('Très bonnes notions','Professional')]:
            with self.subTest(raw=raw):self.assertEqual(builder.language_label('Language ('+raw+')'),'Language ('+expected+')')
        self.assertEqual(builder.language_label('Japanese'),'Japanese')
        self.assertEqual(builder.language_label('German B1/B2'),'German (Professional)')

    def test_unknown_language_description_cannot_be_silently_shortened(self):
        for raw in ['English (Working proficiency)','Spanish (Strong foundational knowledge)','English (C1 / Native)']:
            with self.subTest(raw=raw),self.assertRaises(ValueError):builder.language_label(raw)

    def test_exam_scores_dates_status_and_source_levels_retained_once(self):
        data={'initials':'T.E.','certifications':['French - DELF B1 certified | 2022'],
              'languages':['French - B1 (DELF B1 certified, 2022)',
                           'English (C1; IELTS 8.0, planned, 2024)',
                           'Japanese (JLPT N2, 2021)']}
        before=copy.deepcopy(data)
        normalized=builder.normalize(data)
        self.assertEqual(normalized['languages'],['French (Professional)','English (Fluent)','Japanese'])
        self.assertEqual(normalized['certifications'],['French - DELF B1 certified | 2022',
            'English - IELTS 8.0, planned | 2024','Japanese - JLPT N2 | 2021'])
        self.assertEqual(data,before)
        self.assertEqual(builder.normalize(normalized),normalized)

    def test_four_skills_groups_preserve_every_item(self):
        groups=[{'category':'Group '+str(i),'bullets':['Tool '+str(i),'Method '+str(i)]} for i in range(4)]
        self.assertEqual(builder.normalize({'initials':'T.E.','skills':groups})['skills'],groups)
        with self.assertRaisesRegex(ValueError,'four groups'):
            builder.normalize({'initials':'T.E.','skills':groups+[{'category':'Extra','bullets':['Other tool']}]})

    def test_responsibilities_are_not_rephrased_or_merged_by_the_generator(self):
        bullets=['Monitored access requests; did not own deployment.',
                 'Project A: wrote specifications and ran tests.',
                 'Project B: wrote specifications and ran tests.',
                 'Technical environment: Objective-C, REST, SOAP.']
        data={'initials':'T.E.','experience':[{'dates':'2024','bullets':bullets}]}
        self.assertEqual(builder.normalize(data)['experience'][0]['bullets'],bullets)

    def test_redundant_labels_and_exact_duplicates_fail_before_output(self):
        for bullets in [['Objective: deploy an API gateway'],['Objectif projet IAM 1: integrate tools'],
                        ['Main responsibilities: analyse requirements'],['Interest: improve service'],
                        ['Recurring activities'],['Activités récurrentes'],
                        ['Wrote test plans.','Wrote test plans.']]:
            with self.subTest(bullets=bullets),tempfile.TemporaryDirectory() as tmp:
                output=Path(tmp)/'cv.docx'
                with self.assertRaises(ValueError):builder.build({'initials':'T.E.','experience':[{'bullets':bullets}]},output)
                self.assertFalse(output.exists())

    def test_same_activity_in_different_roles_is_not_a_duplicate(self):
        jobs=[{'employer':'Client A','bullets':['Wrote test plans.']},
              {'employer':'Client B','bullets':['Wrote test plans.']}]
        self.assertEqual(builder.normalize({'initials':'T.E.','experience':jobs})['experience'][0]['bullets'],['Wrote test plans.'])

    def test_full_fictional_conversion_verified_without_network_or_extra_generation(self):
        data=json.loads((ROOT/'skills/bto-cv/references/input-example.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'cv.docx'
            builder.build(data,output)
            result=verifier.verify(data,output)
            self.assertEqual(result['roles'],2)
            self.assertEqual(result['skill_groups'],2)

    def test_verifier_rejects_lost_text_changed_design_and_list_assignment(self):
        data={'initials':'T.E.','experience':[{'dates':'05/2024 - Present','bullets':['Monitored access requests.']}]}
        with tempfile.TemporaryDirectory() as tmp:
            original=Path(tmp)/'original.docx';builder.build(data,original)
            for mutation in ['content','design','numbering']:
                altered=Path(tmp)/(mutation+'.docx')
                with zipfile.ZipFile(original) as src,zipfile.ZipFile(altered,'w') as dst:
                    for name in src.namelist():
                        content=src.read(name)
                        if mutation=='design' and name=='word/styles.xml':content=content.replace(b'Century Gothic',b'Arial')
                        if name=='word/document.xml':
                            if mutation=='content':content=content.replace(b'Monitored access requests.',b'Implemented a new system.')
                            if mutation=='numbering':
                                doc=minidom.parseString(content)
                                node=doc.getElementsByTagNameNS(builder.W,'numPr')[0]
                                node.parentNode.removeChild(node);content=doc.toxml(encoding='UTF-8')
                        dst.writestr(name,content)
                with self.subTest(mutation=mutation),self.assertRaises(ValueError):verifier.verify(data,altered)

    def test_check_cli_writes_no_document_and_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'input.json'
            source.write_text(json.dumps({'initials':'T.E.','languages':['English (Fluent)']}))
            result=subprocess.run([sys.executable,str(SCRIPTS/'build_docx.py'),str(source),'--check'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(list(Path(tmp).glob('*.docx')),[])
            source.write_text(json.dumps({'initials':'T.E.','experience':[{'dates':'13/2025'}]}))
            result=subprocess.run([sys.executable,str(SCRIPTS/'build_docx.py'),str(source),'--check'],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertNotIn('Traceback',result.stderr)

if __name__=='__main__':unittest.main()
