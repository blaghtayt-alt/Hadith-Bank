"""Rebuild the prepared Original Pages compatibility artifact on GitHub Actions."""
import argparse
from gzip import decompress
from hashlib import sha256
from html import escape
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

import production_io as io
from checked_archive import bundle_artifact


SITE = 'https://blaghtayt-alt.github.io'
ALIASES = ('index.html', 'hadith-bank-reader.html')
DATA = 'hadith-bank-reader-data/'
HERE = Path(__file__).resolve().parent
EXPECTED_REPO = 'blaghtayt-alt/Hadith-Bank'


def read(path):
    return json.loads(path.read_bytes())


def digest(body):
    return sha256(body).hexdigest()


def public_body(path):
    req = Request(SITE+path, headers={'Cache-Control':'no-cache', 'User-Agent':'Hadith-Bank-Pages-check'})
    with urlopen(req, timeout=40) as response:
        if response.url != SITE+path:
            raise RuntimeError(f'Unexpected redirect for {path}')
        return response.read()


def check_public(plan, token):
    assert os.environ['GITHUB_REPOSITORY'] == EXPECTED_REPO
    revision = os.environ['GITHUB_SHA']
    assert re.fullmatch(r'[0-9a-f]{40}',revision)
    assert io.json_http(io.REPOSITORY+'/git/ref/heads/main',token)['object']['sha'] == revision
    with urlopen(SITE+'/Hadith-Bank/build-info.json', timeout=30) as response:
        info = json.load(response)
    assert (info['source_commit'],info['record_count'],info['search_sha256']) == (
        plan['source'],plan['records'],plan['search'])
    assert digest(public_body('/Hadith-Bank/index.html')) in (
        plan['shell']['sha256'],plan['rollback']['replaceReaderAliasesOnly']['index.html']['sha256'])
    for row in plan['publicChecks']:
        body = public_body(row['url'])
        assert (len(body),digest(body)) == (row['bytes'],row['sha256']), row['url']


def stage_source(source, output, token=None, fixture=None):
    output.mkdir()
    for key in ('archive','inventory'):
        if fixture is None:
            row = source[key]
            downloaded = output / row['name']
            io.download_artifact(row, downloaded, token)
        else:
            downloaded = fixture / source[key]['name']
            assert io.file_sha(downloaded) == source[key]['digest'].removeprefix('sha256:')
        if key == 'inventory':
            header, entries = io.read_inventory(downloaded)
        else:
            packed = downloaded
    assert header['source_commit'] == source['source']
    root = fixture/'site' if fixture else output/'site'
    entries = {path:row for path,row in entries.items() if path not in source['omit']}
    if not fixture:
        assert io.unpack_site(packed,root,entries) == set(entries)
    assert len(entries) == source['files'] and sum(row['bytes'] for row in entries.values()) == source['bytes']
    return root,entries


def forwarder(url):
    target = escape(url, quote=True)
    return (f'<!doctype html><meta charset=utf-8><title>Continue to the Hadith Bank page</title>'
            f'<meta http-equiv=refresh content="0;url={target}#content"><link rel=canonical href="{target}">'
            f'<h1>Continue to the Hadith Bank page</h1><a href="{target}#content">Open the full source page</a>\n').encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('transition','rollback','check-live'), required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--fixtures', type=Path, nargs=2)
    args = parser.parse_args()
    token = None if args.fixtures else os.environ['GH_TOKEN']
    plan = read(HERE/'plan.json')
    if not args.fixtures:
        check_public(plan,token)
    if args.mode == 'check-live':
        assert not args.fixtures
        return
    out = args.output
    out.mkdir()
    fixtures = args.fixtures or (None,None)
    sources = {}
    for n, fixture in zip((62,63),fixtures,strict=True):
        sources[n] = stage_source(plan['inputs'][str(n)],out/str(n),token,fixture)
    root, current = sources[63]
    files = {path:{**row,'file':root/path} for path,row in current.items()}
    layout = decompress((HERE/'layout.json.gz').read_bytes())
    assert digest(layout) == plan['layoutSHA256']
    layout = json.loads(layout)
    for path in layout['retainedOlder']:
        safe = io.safe_relative(path)
        assert safe.startswith(DATA) and safe != DATA+'manifest.json'
        earlier, rows = sources[62]
        if path in files:
            assert (current[path]['bytes'],current[path]['sha256']) == (rows[path]['bytes'],rows[path]['sha256'])
        files[path] = {**rows[path],'file':earlier/safe}

    if args.mode == 'transition':
        body = decompress((HERE/'reader.html.gz').read_bytes())
        shell = plan['shell']
        assert (len(body),digest(body)) == (shell['bytes'],shell['sha256'])
        (out/'reader.html').write_bytes(body)
        for alias in ALIASES:
            files[alias] = {**shell,'file':out/'reader.html'}
        limit = plan['primary']['expandedBytes']
    else:
        for alias in ALIASES:
            for key in ('sha256','bytes'):
                assert files[alias][key] == plan['rollback']['replaceReaderAliasesOnly'][alias][key]
        limit = plan['rollback']['expandedOriginalBytes']

    target = out/'forward'
    for path in layout['forwardedDetails']:
        safe = io.safe_relative(path)
        assert path.startswith('hadith/') and path.endswith('.html') and path in current
        body = forwarder(plan['archiveRoot']+path)
        file = target/safe
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_bytes(body)
        files[path] = {'bytes':len(body),'sha256':digest(body),'file':file}
    assert len(files) == plan['primary']['regularFiles'] and set(current) <= files.keys()
    result = bundle_artifact(files,limit,out/'artifact.tar')
    if args.mode == 'transition':
        assert {k:v for k,v in result.items() if k!='file'} == plan['primary']
    result.update(source=plan['source'],mode=args.mode,retainedCohorts=[62,63])
    (out/'packaged.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result),flush=True)


if __name__ == '__main__':
    main()
