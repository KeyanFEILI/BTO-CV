import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('uploader', ROOT / 'skills/trello/scripts/upload_cvs.py')
uploader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(uploader)
CARD = '0123456789abcdef01234567'


class FakeClient:
    def __init__(self):
        self.board = {'idOrganization': uploader.WORKSPACE, 'closed': False,
                      'prefs': {'permissionLevel': 'private'}}
        self.card = {'idBoard': uploader.BOARD, 'closed': False}
        self.attachments = []
        self.posts = 0
        self.fail_post = None

    def request(self, path, body=None, content_type=None):
        if path.startswith('/boards/'):
            return self.board
        if not path.endswith('/attachments'):
            return self.card
        if body is None:
            return list(self.attachments)
        self.posts += 1
        if self.fail_post == self.posts:
            raise uploader.UploadError('Simulated uncertain upload')
        name = body.split(b'\r\n\r\n', 1)[1].split(b'\r\n', 1)[0].decode()
        content = body.split(b'Content-Type:', 1)[1].split(b'\r\n\r\n', 1)[1].rsplit(b'\r\n--', 1)[0]
        item = {'id': str(self.posts), 'name': name, 'bytes': len(content), 'isUpload': True}
        self.attachments.append(item)
        return item


class UploadTests(unittest.TestCase):
    def setUp(self):
        self.files = [{'name': 'original-cv-' + 'a' * 64 + '.pdf', 'content': b'fictional original',
                       'mime': 'application/pdf', 'role': 'original'},
                      {'name': 'bto-cv-' + 'b' * 64 + '.docx', 'content': b'fictional BTO',
                       'mime': 'application/octet-stream', 'role': 'bto'}]

    def test_private_board_required_before_upload(self):
        for visibility in ['public', 'org', None]:
            client = FakeClient()
            client.board['prefs']['permissionLevel'] = visibility
            with self.assertRaises(uploader.UploadError):
                uploader.upload_pair(client, CARD, self.files)
            self.assertEqual(client.posts, 0)

    def test_other_board_or_workspace_blocked(self):
        for change in ['board', 'workspace', 'closed']:
            client = FakeClient()
            if change == 'board': client.card['idBoard'] = 'other'
            if change == 'workspace': client.board['idOrganization'] = 'other'
            if change == 'closed': client.card['closed'] = True
            with self.assertRaises(uploader.UploadError):
                uploader.upload_pair(client, CARD, self.files)
            self.assertEqual(client.posts, 0)

    def test_pair_upload_and_repeat_skips_existing(self):
        client = FakeClient()
        self.assertEqual(uploader.upload_pair(client, CARD, self.files)['status'], 'complete')
        self.assertEqual(client.posts, 2)
        result = uploader.upload_pair(client, CARD, self.files)
        self.assertEqual(client.posts, 2)
        self.assertTrue(all(item['status'] == 'already_present' for item in result['attachments']))

    def test_partial_failure_resumes_only_missing(self):
        client = FakeClient()
        client.fail_post = 2
        with self.assertRaises(uploader.UploadError):
            uploader.upload_pair(client, CARD, self.files)
        self.assertEqual(len(client.attachments), 1)
        client.fail_post = None
        self.assertEqual(uploader.upload_pair(client, CARD, self.files)['status'], 'complete')
        self.assertEqual(len(client.attachments), 2)
        self.assertEqual(client.posts, 3)

    def test_metadata_mismatch_not_completed(self):
        client = FakeClient()
        request = client.request
        def corrupt(path, body=None, content_type=None):
            result = request(path, body, content_type)
            if body is not None: client.attachments[-1]['bytes'] = 0
            return result
        client.request = corrupt
        with self.assertRaises(uploader.UploadError):
            uploader.upload_pair(client, CARD, self.files)

    def test_check_only_does_not_upload(self):
        client = FakeClient()
        self.assertEqual(uploader.upload_pair(client, CARD, self.files, True)['status'], 'ready')
        self.assertEqual(client.posts, 0)

    def test_file_validation_and_stable_names(self):
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / 'Sensitive Name.pdf'
            original.write_bytes(b'fictional')
            first = uploader.prepare_file(original, 'original')
            self.assertNotIn('Sensitive', first['name'])
            self.assertEqual(first['name'], uploader.prepare_file(original, 'original')['name'])
            with self.assertRaises(uploader.UploadError): uploader.prepare_file(original, 'bto')
            original.write_bytes(b'')
            with self.assertRaises(uploader.UploadError): uploader.prepare_file(original, 'original')
            original.write_bytes(b'12345')
            with patch.object(uploader, 'MAX_BYTES', 4), self.assertRaises(uploader.UploadError):
                uploader.prepare_file(original, 'original')

    def test_secrets_not_in_url_and_errors_redacted(self):
        client = uploader.Client('k' * 32, 't' * 64)
        error = urllib.error.HTTPError('SECRET_URL', 401, 'SECRET_TOKEN', {}, None)
        with patch.object(client.opener, 'open', side_effect=error) as opened:
            with self.assertRaises(uploader.UploadError) as caught:
                client.request(f'/cards/{CARD}?fields=idBoard,closed')
        self.assertNotIn('SECRET', str(caught.exception))
        request = opened.call_args.args[0]
        self.assertNotIn('token=', request.full_url)
        self.assertIn('Authorization', request.headers)
        self.assertIsNone(uploader.NoRedirect().redirect_request(None, None, None, None, None, None))
        with self.assertRaises(uploader.UploadError): client.request('/evil/endpoint')

    def test_card_identifier_validation(self):
        self.assertEqual(uploader.card_id(CARD), CARD)
        self.assertEqual(uploader.card_id(f'ari:cloud:trello::card/workspace/{uploader.WORKSPACE}/{CARD}'), CARD)
        for value in ['https://trello.com/c/example', '../other', f'ari:cloud:trello::card/workspace/other/{CARD}']:
            with self.assertRaises(uploader.UploadError): uploader.card_id(value)


if __name__ == '__main__':
    unittest.main()
