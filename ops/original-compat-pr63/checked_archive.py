from hashlib import sha256
import tarfile
import production_io as io

maximum = 950_000_000

class CheckedBody:
    def __init__(self, stream):
        self.stream = stream
        self.hash = sha256()
        self.size = 0

    def read(self, amount):
        body = self.stream.read(amount)
        self.hash.update(body)
        self.size += len(body)
        return body


def bundle_artifact(entries, total, tar_path=None):
    assert sum(entry['bytes'] for entry in entries.values())==total<maximum
    if tar_path is None:
        for name,entry in entries.items():
            p=entry['file']
            assert p.stat().st_size==entry['bytes'] and io.file_sha(p)==entry['sha256'],name
        return {'expandedBytes':total,'regularFiles':len(entries),'allSourceBodiesExact':True}

    output_format = tarfile.USTAR_FORMAT
    for name in entries:
        try:
            tarfile.TarInfo(name).tobuf(format=output_format)
        except ValueError:
            output_format=tarfile.PAX_FORMAT
            break
    with tarfile.open(tar_path,'x',format=output_format) as archive:
        for name,entry in sorted(entries.items()):
            member = tarfile.TarInfo(name)
            member.mode = 0o644
            member.size = entry['bytes']
            with entry['file'].open('rb') as source:
                checked = CheckedBody(source)
                archive.addfile(member,checked)
                assert (checked.size,checked.hash.hexdigest())==(entry['bytes'],entry['sha256']),name
                assert not source.read(1),name

    remaining = set(entries)
    measured = 0
    with tarfile.open(tar_path,'r|') as archive:
        for member in archive:
            name = io.safe_relative(member.name)
            assert member.isfile() and name in remaining,name
            expected = entries[name]
            assert member.size == expected['bytes'],name
            check = sha256()
            with archive.extractfile(member) as file:
                while body:=file.read(262144):
                    check.update(body)
            assert check.hexdigest()==expected['sha256'],name
            measured += member.size
            remaining.remove(name)
    assert not remaining and measured==total
    packed_size=tar_path.stat().st_size
    assert packed_size<1_000_000_000, 'Choose compact Pages packaging before treating the artifact as deployable'
    return {'file':tar_path.name,'expandedBytes':measured,'tarBytes':packed_size,'regularFiles':len(entries),
            'tarFormat':'ustar' if output_format==tarfile.USTAR_FORMAT else 'pax',
            'tarSHA256':io.file_sha(tar_path),'allPackagedBodiesExact':True}


