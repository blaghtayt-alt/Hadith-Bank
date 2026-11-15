"""Deterministic, lossless gzip transport choice for generated (never source) shards.

Always compare against the existing gzip9 encoding. Alternative zlib
parameters are admissible ONLY if they produce fewer bytes and decode to the
exact original byte stream. No change to shard boundaries or decoded JSON.
"""
import gzip
import zlib


def smallest_gzip(raw):
    if not isinstance(raw, bytes):
        raise TypeError('gzip transport input must be immutable bytes')
    baseline = gzip.compress(raw, compresslevel=9, mtime=0)
    best = baseline
    # Avoid broad strategies that inflate JSON. The baseline is always safe.
    for mem_level, strategy in ((9, zlib.Z_DEFAULT_STRATEGY),
                                (9, zlib.Z_FILTERED),
                                (8, zlib.Z_FILTERED)):
        compressor = zlib.compressobj(level=9, method=zlib.DEFLATED,
                                       wbits=31, memLevel=mem_level, strategy=strategy)
        candidate = compressor.compress(raw) + compressor.flush()
        if len(candidate) < len(best):
            if gzip.decompress(candidate) != raw:
                raise ValueError('Alternative gzip did not reproduce exact source data')
            best = candidate
    if len(best) > len(baseline) or best[:2] != b'\x1f\x8b':
        raise ValueError('Adaptive gzip violated lossless/size invariant')
    return best
