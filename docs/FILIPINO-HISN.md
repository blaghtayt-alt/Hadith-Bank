# Filipino Hisn al-Muslim

The reconstructed Filipino source edition is an active public bank import. The owner requested bank and HTML integration on 12 November 2026 and explicitly requested that it not remain on publication hold. Its material uses `owner_requested_public_source_import`; the earlier reconstruction's audit assessment remains historical evidence.

## Source and scope

The source is **Hisnul Muslim — Hisn al-Muslim**, subtitled **KUTANG-TANGGULAN NG MUSLIM**, with the printed Filipino translator credit **ABDULKHALIQ SHARIF SARIPADA** and corrector credit **DAUD M. ANGNI**. The printed edition is the third edition; its exact publication year is unknown. The original PDF has 276 pages, while its catalogue entry states 280 pages. That difference does not establish missing narration text.

The original [FIL-HISN-PRIVATE.pdf](../materials/fil-hisn-muslim-3e409dd7/FIL-HISN-PRIVATE.pdf) is 5,321,887 bytes, SHA256 `3e409dd7266c2a150645ecfea548f266edf80c9c5df5129aa8df7a977d248a07`. The stable source identity is `fil-hisn-muslim-3e409dd7`; occurrence IDs append the original record ID. This edition remains distinct from the two older Filipino Hisn quotations copied from Quran-study materials.

| Source route | Occurrences | Bank / Hadith HTML |
| --- | ---: | --- |
| Hadith, narrated dhikr and coherent narration context | 298 | Active |
| Independent non-Prophetic sayings | 14 | Preserved separately |
| Quran and author-only material | 6 | Preserved separately |
| Unresolved attribution | 5 | Preserved separately |
| Complete preserved source | 323 | All source records retained |

These are source occurrences, not a count of unique authenticated Prophetic sayings. Another speaker's words, narrator framing, prayer instructions, variants and hadith-bearing footnotes can belong to a coherent hadith context. They are not automatically excluded. Quran, compiler commentary and independent sayings retain their distinctions. Classification does not establish an authenticity grade.

## Reader projection

The adapter preserves the original component order. This includes the 34 reader records whose Filipino narration exists without a `translation` aggregate, and records with interleaved dialogue, translated prayers and transliterations. Exact component IDs, source hashes and display joins are recorded so the projection can be checked against the preserved source. Source instructions and Quran/author spans retain their scope annotations.

The 259 reader records with Arabic in the original extraction retain that text; the other 39 remain without original Arabic. External Arabic evidence retained during reconstruction is not substituted for absent printed text. The material disables automatic counterpart matching until a separate source-bound mapping is approved. This is a restriction on adding external counterparts, not a publication hold on the imported source.

Filipino and Arabic have separate language panels, with the edition's printed references and language-appropriate notes. The Filipino version is a published human translation. OCR and extraction history do not change that translation-origin attribution. No new translation, chain, grade, date or canonical number is generated.

## Evidence and reproducibility

The [preservation manifest](../imports/filipino-hisn-reconstructed-20261112/preservation-manifest.json) lists each exact reconstructed file and its checksum. Larger files are stored as deterministic gzip archives, with both compressed and original byte hashes. Decompression reproduces the original files byte-for-byte, including the complete 323-record dataset and 1,500 components, partitions, before/after log, replayable patch, scoped exceptions, metadata and coverage logs.

The reconstruction was made from the exact v1 checkpoint, SHA256 `8043d352e722d8c38ba49bdb54f4f273bb91e3fe4fba111d0d809b36ed17c7ad`, and the provided instructions. It is a new reconstruction, not recovery of the lost byte-identical v2. The complete reconstructed delivery retains v1 and every prior original; its persistent location and exact archive hash are recorded in the preservation manifest. The large original checkpoint archive is not duplicated in Git.

To regenerate the registered material and reader:

```bash
python scripts/import_filipino_hisn.py --root .
python -m unittest discover -s tests -p 'test_filipino_hisn_import.py'
python scripts/refresh_bank.py --root . --site-output _site
```

The import script validates the fixed source hashes and routes before writing the active source projection. The website workflow builds the HTML, language/book/source filters, search and original-PDF downloads from the registered material.

## Current publication and review facts

The [material manifest](../materials/fil-hisn-muslim-3e409dd7/manifest.json) and [publication policy](../catalog/publication-policy.json) record the owner's current public-source decision. The source is available for reading; it is not held from publication. The original reconstructed files remain unchanged and therefore retain their earlier HOLD filenames and historical assessment.

Source fidelity and metadata still have specific partial or unresolved findings. The preserved record blocker index separates localized text questions, metadata limits and the earlier package review gate. A missing edition year or one uncertain glyph does not make every narration incorrect. The reconstruction retained all 493 earlier Prophetic candidate components; publication does not convert those candidates into independently certified components.

Independent evaluation of the final reconstructed bytes remains `NOT_RUN`, and `certified_release_eligible=false`. The integration performs source-preservation, routing, software and browser checks; it is not a new scholarly certification. Existing OCR evidence and review facts remain accurate. Rights remain unassessed; the owner's publication decision does not create a publisher license.
