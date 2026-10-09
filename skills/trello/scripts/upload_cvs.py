"""Upload two local CVs directly to a private Talent Pool card. Stdlib only."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

BOARD = '6996e43b0c990427965789b8'
WORKSPACE = '5cd2eb4e4bd3b0081259a24e'
TARGET = 'BTO-CV/TrelloUploader'
MAX_BYTES = 10 * 1024 * 1024


class UploadError(Exception):
    pass


class Credential(ctypes.Structure):
    _fields_ = [('Flags', wintypes.DWORD), ('Type', wintypes.DWORD),
                ('TargetName', wintypes.LPWSTR), ('Comment', wintypes.LPWSTR),
                ('LastWritten', wintypes.FILETIME), ('CredentialBlobSize', wintypes.DWORD),
                ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)),
                ('Persist', wintypes.DWORD), ('AttributeCount', wintypes.DWORD),
                ('Attributes', ctypes.c_void_p), ('TargetAlias', wintypes.LPWSTR),
                ('UserName', wintypes.LPWSTR)]


def credential_api():
    if os.name != 'nt':
        raise UploadError('This uploader requires Windows Credential Manager.')
    api = ctypes.WinDLL('advapi32', use_last_error=True)
    api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                             ctypes.POINTER(ctypes.POINTER(Credential))]
    api.CredReadW.restype = wintypes.BOOL
    api.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]
    api.CredWriteW.restype = wintypes.BOOL
    api.CredFree.argtypes = [ctypes.c_void_p]
    api.CredFree.restype = None
    return api


def validate_secrets(key, token):
    if not re.fullmatch(r'[A-Za-z0-9]{16,128}', key) or not re.fullmatch(r'[A-Za-z0-9_-]{16,512}', token):
        raise UploadError('Invalid key/token format; enter Trello credentials in the local setup window.')
    return key, token


def read_credentials():
    api = credential_api()
    pointer = ctypes.POINTER(Credential)()
    if not api.CredReadW(TARGET, 1, 0, ctypes.byref(pointer)):
        raise UploadError('Credentials unavailable. Run this script with --configure locally first.')
    try:
        data = json.loads(ctypes.string_at(pointer.contents.CredentialBlob,
                                         pointer.contents.CredentialBlobSize).decode('utf-8'))
        return validate_secrets(data['key'], data['token'])
    except (ValueError, KeyError, UnicodeError):
        raise UploadError('Stored credentials are invalid; configure them again.') from None
    finally:
        api.CredFree(pointer)


def store_credentials(key, token):
    validate_secrets(key, token)
    api = credential_api()
    blob = json.dumps({'key': key, 'token': token}).encode('utf-8')
    buffer = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
    credential = Credential(Type=1, TargetName=TARGET, CredentialBlobSize=len(blob),
                            CredentialBlob=buffer, Persist=2, UserName='TrelloUploader')
    try:
        if not api.CredWriteW(ctypes.byref(credential), 0):
            raise UploadError('Windows could not save the credentials.')
    finally:
        ctypes.memset(buffer, 0, len(blob))


def configure():
    # Secrets are entered in masked local GUI fields, never CLI args or chat.
    credential_api()
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.title('BTO Trello uploader — credential setup')
    tk.Label(root, text='Enter your Trello API key and read/write token.\nStored in Windows Credential Manager.').pack(padx=20, pady=12)
    entries = []
    for label in ('API key', 'Token'):
        tk.Label(root, text=label).pack()
        field = tk.Entry(root, show='*', width=60)
        field.pack(padx=20, pady=5)
        entries.append(field)

    def save():
        try:
            store_credentials(*(entry.get().strip() for entry in entries))
        except UploadError as error:
            messagebox.showerror('Setup', str(error))
            return
        for entry in entries:
            entry.delete(0, tk.END)
        messagebox.showinfo('Setup', 'Credentials saved. No CV files were uploaded.')
        root.destroy()

    tk.Button(root, text='Save credentials', command=save).pack(pady=12)
    root.mainloop()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Client:
    def __init__(self, key, token):
        validate_secrets(key, token)
        self.authorization = f'OAuth oauth_consumer_key="{key}", oauth_token="{token}"'
        self.opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), NoRedirect(),
            urllib.request.HTTPSHandler(context=ssl.create_default_context()))

    def request(self, path, body=None, content_type=None):
        if not re.fullmatch(r'/(?:cards|boards)/[a-f0-9]{24}(?:/attachments)?(?:\?[A-Za-z0-9=,%]+)?', path):
            raise UploadError('Invalid Trello API path.')
        headers = {'Authorization': self.authorization, 'Accept': 'application/json'}
        if content_type:
            headers['Content-Type'] = content_type
        request = urllib.request.Request('https://api.trello.com/1' + path,
                                         data=body, headers=headers)
        try:
            with self.opener.open(request, timeout=60) as response:
                return json.loads(response.read(2 * 1024 * 1024).decode('utf-8'))
        except urllib.error.HTTPError as error:
            # Never echo response bodies, secrets, paths, or file contents.
            raise UploadError(f'Trello HTTP {error.code}. Stop and verify the card before retrying.') from None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            raise UploadError('Trello request failed. Upload outcome may be uncertain; verify the card before retrying.') from None


def card_id(value):
    match = re.fullmatch(r'(?:ari:cloud:trello::card/workspace/' + WORKSPACE + r'/)?([a-f0-9]{24})', value)
    if not match:
        raise UploadError('Use the card object ID or its Talent Pool workspace ARI, not a URL.')
    return match.group(1)


def prepare_file(path, role):
    path = Path(path).resolve(strict=True)
    if not path.is_file() or path.suffix.lower() not in ({'.pdf', '.docx', '.doc'} if role == 'original' else {'.docx'}):
        raise UploadError('Original must be PDF/DOC/DOCX; BTO must be DOCX.')
    with path.open('rb') as source:
        content = source.read(MAX_BYTES + 1)
    if not content or len(content) > MAX_BYTES:
        raise UploadError('Files must be nonempty and at most 10 MiB each.')
    digest = hashlib.sha256(content).hexdigest()
    # Stable identity enables safe resumption; names omit candidate personal data.
    name = f'{role}-cv-{digest}{path.suffix.lower()}'
    mime = mimetypes.guess_type(name)[0] or 'application/octet-stream'
    return {'name': name, 'content': content, 'mime': mime, 'role': role}


def multipart(file):
    boundary = 'BTO' + uuid.uuid4().hex
    name = file['name']
    head = (f'--{boundary}\r\nContent-Disposition: form-data; name="name"\r\n\r\n{name}\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="setCover"\r\n\r\nfalse\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
            f'Content-Type: {file["mime"]}\r\n\r\n').encode('ascii')
    return head + file['content'] + f'\r\n--{boundary}--\r\n'.encode('ascii'), 'multipart/form-data; boundary=' + boundary


def verify_destination(client, identifier):
    card = client.request(f'/cards/{identifier}?fields=idBoard,closed')
    if card.get('idBoard') != BOARD or card.get('closed') is not False:
        raise UploadError('Destination must be an open card on the approved Talent Pool board.')
    board = client.request(f'/boards/{BOARD}?fields=prefs,idOrganization,closed')
    if (board.get('idOrganization') != WORKSPACE or board.get('closed') is not False
            or board.get('prefs', {}).get('permissionLevel') != 'private'):
        raise UploadError('Talent Pool must be private, open, and in the approved BTO LUX workspace. No upload performed.')


def matches(attachments, file):
    return [item for item in attachments if item.get('name') == file['name']
            and item.get('bytes') == len(file['content']) and item.get('isUpload') is True]


def upload_pair(client, identifier, files, check_only=False):
    verify_destination(client, identifier)
    if check_only:
        return {'status': 'ready', 'files': len(files)}
    outcomes = []
    for file in files:
        # Repeat board check immediately before each file upload.
        verify_destination(client, identifier)
        attachments = client.request(f'/cards/{identifier}/attachments')
        existing = matches(attachments, file)
        if len(existing) > 1:
            raise UploadError('Duplicate matching attachments exist. Review the card before continuing.')
        if not existing:
            body, mime = multipart(file)
            created = client.request(f'/cards/{identifier}/attachments', body, mime)
            verified = matches(client.request(f'/cards/{identifier}/attachments'), file)
            if len(verified) != 1 or verified[0].get('id') != created.get('id'):
                raise UploadError('Upload metadata verification failed. Review the card before retrying.')
        outcomes.append({'role': file['role'], 'status': 'already_present' if existing else 'uploaded'})
    verify_destination(client, identifier)
    final = client.request(f'/cards/{identifier}/attachments')
    if any(len(matches(final, file)) != 1 for file in files):
        raise UploadError('Both attachments were not found in the final check.')
    return {'status': 'complete', 'attachments': outcomes,
            'verification': 'attachment identity, uploaded-file flag, and size'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configure', action='store_true')
    parser.add_argument('--card')
    parser.add_argument('--original', type=Path)
    parser.add_argument('--bto', type=Path)
    parser.add_argument('--check', action='store_true', help='Validate destination and files without uploading')
    args = parser.parse_args()
    try:
        if args.configure:
            configure()
            return 0
        if not args.card or not args.original or not args.bto:
            raise UploadError('Provide --card, --original and --bto, or use --configure.')
        identifier = card_id(args.card)
        files = [prepare_file(args.original, 'original'), prepare_file(args.bto, 'bto')]
        result = upload_pair(Client(*read_credentials()), identifier, files, args.check)
        print(json.dumps(result))
        return 0
    except UploadError as error:
        print(json.dumps({'status': 'incomplete', 'message': str(error)}))
        return 1
    except Exception:
        print(json.dumps({'status': 'incomplete', 'message': 'Local setup or file access failed; no diagnostic contents were printed.'}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
