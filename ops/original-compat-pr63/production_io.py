"""Fetch and extract one completed Original Pages run for a private rehearsal."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
from zipfile import ZipFile

REPOSITORY = 'https://api.github.com/repos/blaghtayt-alt/Hadith-Bank'
MARKERS = {'.hadith-bank-generated-site', '.nojekyll'}

def json_http(url, token):
    with urlopen(Request(url, headers={'Accept': 'application/vnd.github+json', 'Authorization': 'Bearer '+token}), timeout=30) as response:
        return json.load(response)

def file_sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def read_inventory(archive):
    with ZipFile(archive) as container:
        doc = json.loads(container.read('site-size-final.json'))
    rows = doc['files']
    payload = json.dumps(rows, ensure_ascii=False, separators=(',', ':')).encode()
    if hashlib.sha256(payload).hexdigest() != doc['file_manifest_sha256']:
        raise ValueError('Site inventory digest mismatch')
    result = {}
    for item in rows:
        relative = item['path']
        safe_relative(relative)
        if relative in result or type(item['bytes']) is not int or item['bytes'] < 0 or not re.fullmatch(r'[a-f0-9]{64}', item['sha256']):
            raise ValueError('Invalid inventory row')
        result[relative] = item
    if len(result) != doc['file_count'] or sum(item['bytes'] for item in rows) != doc['final_site_bytes']:
        raise ValueError('Site inventory totals mismatch')
    return doc, result

def safe_relative(raw):
    # Explicitly reject drive names, alternate separators, and normalized aliases.
    path = PurePosixPath(raw)
    if not re.fullmatch(r'[-A-Za-z0-9_./]+', raw) or path.is_absolute() or raw != path.as_posix() or any(part in ('.','..') for part in path.parts):
        raise ValueError('Unsafe archive member path')
    return path.as_posix()

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None

def download_artifact(artifact, destination, token):
    expected = artifact['digest'].removeprefix('sha256:')
    if not re.fullmatch(r'[a-f0-9]{64}', expected):
        raise ValueError('Artifact digest missing')
    if not destination.exists():
        api = f"{REPOSITORY}/actions/artifacts/{artifact['id']}/zip"
        try:
            build_opener(NoRedirect).open(Request(api, headers={'Authorization': 'Bearer '+token}), timeout=30)
            raise RuntimeError('Artifact endpoint did not redirect')
        except HTTPError as err:
            if err.code != 302:
                raise RuntimeError(f'Artifact endpoint returned {err.code}') from None
            target = err.headers['Location']
        parsed = urlsplit(target)
        if parsed.scheme != 'https' or parsed.username or parsed.password:
            raise ValueError('Unexpected artifact redirect')
        part = destination.with_suffix('.part')
        with urlopen(target, timeout=60) as stream, part.open('xb') as output:
            shutil.copyfileobj(stream, output, length=1024**2)
        if part.stat().st_size != artifact['size_in_bytes'] or file_sha(part) != expected:
            raise ValueError('Downloaded artifact bytes mismatch')
        part.rename(destination)
    if destination.stat().st_size != artifact['size_in_bytes'] or file_sha(destination) != expected:
        raise ValueError('Existing artifact bytes mismatch')
    return expected

def unpack_site(archive, output, expected):
    seen = set()
    with ZipFile(archive) as container:
        payload, = (member for member in container.infolist() if not member.is_dir())
        if payload.filename != 'artifact.tar':
            raise ValueError('Unexpected Pages ZIP layout')
        with container.open(payload) as source, tarfile.open(fileobj=source, mode='r|*') as tar:
            for member in tar:
                if member.isdir():
                    # The production tar uses ./ for its root.
                    if member.name not in ('.', './'):
                        safe_relative(member.name.removeprefix('./').rstrip('/'))
                    continue
                relative = safe_relative(member.name.removeprefix('./'))
                row = expected.get(relative)
                if not member.isfile() or row is None or relative in seen or member.size != row['bytes']:
                    raise ValueError(f'Invalid deployed archive item {relative}')
                file = output / relative
                file.parent.mkdir(parents=True, exist_ok=True)
                content_hash = hashlib.sha256()
                with tar.extractfile(member) as src, file.open('xb') as dst:
                    while chunk := src.read(1024**2):
                        content_hash.update(chunk)
                        dst.write(chunk)
                if content_hash.hexdigest() != row['sha256']:
                    raise ValueError(f'Deployed archive file digest mismatch {relative}')
                seen.add(relative)
    if not set(expected).difference(seen).issubset(MARKERS):
        raise ValueError('Deployed paths differ from final inventory')
    return seen

