#!/usr/bin/env python3
"""Serialize the recorded, complete 2026-11-13 review of the 244 held IDs.

This script records human/assistant source reading decisions; running it is not
a substitute for reviewing the text. All offsets are exact Unicode codepoints.
"""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import shutil

REPOSITORY = 'fawazahmed0/hadith-api'
REVISION = 'df57907be35291c91ad6a6691180e22ca9920784'
BASE_COMMIT = '7b22548d43bccce94cce0e04d734e47458460fac'
REPORT = 'reports/fawaz-held-resolution-20261113'
RECOVERED = {('abudawud', n) for n in ('2424', '3338', '3339', '3587')} | {
    ('nasai', '4221'), ('nasai', '5752')}

# Each nonempty ID was read in every supplied language, including long Urdu
# legal discussions. These notes record the actual field content, not a
# classification inferred from the provider number or another language.
RATIONALES = {
 'abudawud': {
  '2330': 'A lexical explanation of sirrahu. The chain introduces a word gloss and supplies no separately bounded report.',
  '2331': 'A lexical explanation of sirrahu, followed by compiler comparisons of its meaning. Keep the complete discussion as context.',
  '2423': 'Ibn Shihab identifies or criticizes the referenced Saturday-fasting transmission as Himsi. The referenced report body is not supplied; the transmission assessment remains context.',
  '2424': 'Al-Awzai reports his own withholding of a transmission and his observation that it circulated. That source-bound historical account is separable from the explanatory identification and appended criticism attributed to Malik. The criticism is retained verbatim as context, without adopting it as a bank authenticity verdict.',
  '2582': 'A definition of jalab/janab in horse-racing terminology; no separately narrated event is supplied.',
  '2617': 'A geographic identification or correction of Ubna/Yubna. Retain the explanatory place-name material.',
  '2806': 'A definition of the defect called adab, explaining the extent of ear or horn damage. This is a lexical/legal explanation.',
  '2832': 'A definition of fara, the pre-Islamic first-born-animal sacrifice. The definition remains source commentary.',
  '2840': 'An explanation that removal of harm refers to shaving the head. This gloss does not contain the referenced report as a separate body.',
  '2938': 'A definition of sahib maks, the tax or toll collector. It is lexical explanation.',
  '2981': 'An explanation identifying the relatives denoted by dhul-qurba as Banu Abd al-Muttalib. Preserve it as explanatory context.',
  '3065': 'An explanation of the expression about camel hooves and grazing arak. The explanatory wording is not a separately bounded narrated event.',
  '3078': 'Hisham and Malik explain the meaning of an unjust root in land. These definitions remain legal/lexical commentary.',
  '3086': 'A definition of rikaz and related treasure terminology. Keep the definition as source explanation.',
  '3338': 'The first passage reports an exchange between an unnamed man and Shubah. Preserve that historical exchange as supplied. The appended comparative transmission criticism attributed to Yahya ibn Main and the English explanatory parenthesis remain context.',
  '3339': 'Shubah explicitly gives his own testimonial comparison of Sufyans memory with his. This is an attributed scholarly saying, not a statement attributed to the Prophet.',
  '3365': 'An explanatory definition of ariyya and the relevant fruit-transfer arrangement. Keep it outside narration search.',
  '3366': 'An explanation of araya and its transaction terminology. The numbered gloss remains source context.',
  '3453': 'A criticism of interpreting the phrase not one of us as not like us. It discusses the meaning of a quoted expression without supplying a separately bounded report.',
  '3471': 'An explanation of agricultural blight and related loss. Retain the definition as commentary.',
  '3560': 'Legal definitions of umra and ruqba arrangements. These explanatory rulings remain source context.',
  '3587': 'Arabic, English and Urdu attribute the testimonial observation to Muadh ibn Muadh. The Bengali field explicitly assigns the first-person assessment to Abu Uthman instead; retain that complete discrepant field as source context. Do not silently repair its speaker from another language. Identity glosses and the Urdu note marker remain context.',
  '3650': 'A question and explanation identifying what write for him refers to: a sermon heard on that day. The sermon itself is not supplied here and is not reconstructed.',
  '3908': 'Definitions of divination-related terms. Preserve the lexical explanation and supplied assessment separately from narration text.',
  '3918': 'Folkloric and lexical explanations of safar and hamah. The full explanatory discussion remains context.',
  '4067': 'An explanation of the colour term mudarrajah. A word definition does not establish separate narration text.',
  '4251': 'A geographic identification of Salah near Khaybar. Keep the place-name explanation as supplied.',
  '4266': 'A narrator-name or epithet variant for Ziyad, including siminkush/white ears. This is identity commentary.',
  '4300': 'Another source occurrence identifying Salah near Khaybar. Preserve its distinct provider ID even though the explanatory subject repeats another entry.',
  '4414': 'Mujahid and Sufyan explain verses and legal hadd terminology. Keep these verse/legal explanations as commentary under the project scope.',
  '4424': 'An explanation of kuthba as a small amount of milk. It is a lexical gloss.',
  '4619': 'Hasan explains a verse concerning belief and association. Keep the exegesis and the supplied Urdu citation as source context; do not silently correct or convert it into narration text.',
  '4620': 'Hasan explains a verse concerning a barrier to faith. Preserve this verse explanation as commentary.',
 },
 'bukhari': {
  '4843': 'All four fields supply a chain and identification of Thabit ibn Dahhak but no transmitted report body; English ends at the introduction. Bengali also supplies a cross-reference. Preserve these exact fragments and reference, but do not import a body from another entry to fill this pinned source gap.',
 },
 'malik': {
  '807': 'An unnamed scholar explains why the Hijr was enclosed. This explanatory discussion remains context.',
  '1093': 'Qasim explains the marriage-proposal wording of Quran 2:235 with an example. Preserve the exegesis and example as explanation.',
  '1131': 'Said ibn al-Musayyab explains muhsanat. The English field also contains extended Malik legal discussion; all supplied text is explanatory context.',
  '1519': 'The supplied Urdu field is Malik legal discussion about relations involving a jointly owned slave. Preserve the historical legal commentary without treating it as narration text.',
  '1569': 'The supplied Arabic and English fields contain Malik legal reasoning about wounds and discretionary assessment. They remain legal commentary.',
  '1597': 'The supplied Bengali field contains Malik legal commentary about a slave, homicide and oaths. Retain the full discussion as context.',
  '631.5': 'The only nonempty field is the four-codepoint Urdu marker مسنگ. It signifies missing material; it contains no report to recover.',
  '787.5': 'The supplied Urdu field introduces and quotes Quran 5:95 in discussion of hunting compensation. This is Quran quotation and legal context, not an independently supplied narration body.',
  '874.5': 'The supplied Urdu field contains Malik pilgrimage purification rulings and legal questions and answers. Preserve it as commentary.',
  '904.5': 'The supplied Urdu field contains Malik legal discussion of Meccans shortening prayer at Mina. It remains commentary.',
  '926.5': 'The supplied Urdu field contains extended Malik rulings about pledged property and creditors. Every part is retained as legal context.',
  '943.5': 'The supplied Urdu field contains Malik rulings about ihram clothing, compensation and missed fasts. It remains legal commentary.',
  '956.5': 'The supplied Urdu field contains Malik legal discussion about women travelling for pilgrimage without a mahram. Preserve the historical ruling as context.',
  '974.5': 'The supplied Urdu field contains Malik legal discussion of a non-Muslim shipwreck and shore-related case. It remains legal commentary.',
  '1014.5': 'The supplied Urdu field contains Malik legal rules for a vow to walk to the Kaaba. No separate narrated event is supplied.',
  '1063.5': 'The supplied Urdu field contains Malik legal opinion about horses, mules and donkeys, with Quran quotations. Preserve the discussion as context.',
  '1066.5': 'The supplied Urdu field contains Malik legal rules about eating carrion under necessity. It remains commentary.',
  '1167.75': 'The supplied Urdu field contains Malik legal rules about valuation of pledged property and an oath. It remains commentary.',
  '1208.5': 'The supplied Urdu field contains Malik legal discussion of maintenance after irrevocable divorce. It remains commentary.',
  '1226.5': 'The supplied Urdu field contains Malik legal rules about slave women, waiting periods and divorce. Preserve it as historical legal commentary.',
  '1322.25': 'The supplied Urdu field contains Malik legal rules about fruit barter. It remains commentary.',
  '1355.5': 'The supplied Urdu field contains Malik legal rules about meat barter. It remains commentary.',
  '1370.5': 'The supplied Urdu field contains Malik commercial rulings about joint purchases and rescission. It remains commentary.',
  '1388.5': 'The supplied Urdu field contains Malik mudaraba rules. It remains legal commentary.',
  '1408.5': 'The supplied Urdu field contains Malik discussion of debt, inheritance and oaths. It remains legal commentary.',
  '1424.5': 'The supplied Urdu field contains Malik legal examples concerning acknowledged paternity and inheritance. It remains commentary.',
  '1439.5': 'The supplied Urdu field contains Malik legal discussion of debt transfer and guarantees. It remains commentary.',
  '1441.5': 'The supplied Urdu field contains Malik legal rules about possession of gifts and charity. It remains commentary.',
  '1442.5': 'The supplied Urdu field contains Malik legal discussion of revocation of parental gifts. It remains commentary.',
  '1448.5': 'The supplied Urdu field contains Malik rules on a slaves liability for found property. Preserve the historical legal commentary.',
  '1460.5': 'The supplied Urdu field contains Malik legal rules about valuation in an invalid sale. It remains commentary.',
  '1462.5': 'The supplied Urdu field contains Malik legal discussion of liability for a slaves wrongs. It remains historical commentary.',
  '1515.5': 'The supplied Urdu field contains Malik historical legal discussion of pregnancy, proof of sexual assault and waiting periods. Preserve the source wording as legal commentary; no new narration is extracted.',
 },
 'muslim': {'5676': 'All four fields define al-hamw in terms of the husbands relatives. This is a lexical explanation.'},
 'nasai': {
  '916': 'Ibn Abbas explains the seven oft-repeated as the seven long chapters. This numbered verse explanation remains commentary under the project exclusion for explanations.',
  '4221': 'Habib reports the inquiry requested by Muhammad ibn Sirin and the reply of al-Hasan about from whom he heard the aqiqah tradition. The supplied dialogue is a historical transmission inquiry. The referenced aqiqah report body is not supplied or reconstructed; the Urdu source field is empty.',
  '5574': 'Ibrahim and Shabi explain sakar as khamr. This is lexical/verse explanation.',
  '5575': 'Said ibn Jubayr explains sakar as khamr. Keep the gloss as explanatory context.',
  '5576': 'A distinct source chain supplies Said ibn Jubayrs same gloss of sakar. Preserve this separate provider occurrence as commentary.',
  '5577': 'Said ibn Jubayr explains the verse by distinguishing strong drink and goodly provision. This is verse explanation.',
  '5752': 'Abu Usamah gives his own eyewitness testimonial comparison of Abdullah ibn al-Mubaraks pursuit of knowledge in the named regions. Preserve it as his attributed saying; the Urdu source field is empty.',
 },
}

def raw_json(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()

def digest(value):
    return hashlib.sha256(value).hexdigest()

def write_json(root, relative, value, compressed=False):
    raw=raw_json(value)
    stored=gzip.compress(raw, compresslevel=9, mtime=0) if compressed else raw
    path=root/relative
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(stored)
    spec={'path':relative,'bytes':len(stored),'sha256':digest(stored)}
    if compressed: spec.update(compression='gzip',raw_bytes=len(raw),raw_sha256=digest(raw))
    return spec

def before(text, marker):
    assert text.count(marker)==1,(marker,text)
    return [[0,text.index(marker)]]

def excluding(text, literal, stop=None):
    assert text.count(literal)==1,(literal,text)
    a=text.index(literal);b=a+len(literal)
    end=len(text) if stop is None else text.index(stop)
    return [[0,a],[b,end]]

def speaker(text, name, spans):
    start=text.index(name)
    assert any(a<=start and start+len(name)<=b for a,b in spans),(name,spans)
    return {'role':'other','name_as_supplied':name,'source_spans':[[start,start+len(name)]]}

def decision_for(book,number,prefix,text):
    if (book,number) not in RECOVERED or not text.strip(): return None
    d={'provider_book':book,'provider_edition':prefix+'-'+book,'typed_hadithnumber':number,
       'source_text_sha256':digest(text.encode()),'review_scope':'complete_own_language_source_boundary_and_attribution_review',
       'independent_authenticity_assessment':False,'span_unit':'unicode_codepoints',
       'decision_note':RATIONALES[book][number]}
    if (book,number,prefix)==('abudawud','3587','ben'):
        d.update(action='source_context_only',reason='The complete Bengali field explicitly assigns the first-person assessment to Abu Uthman. Arabic, English and Urdu assign it to Muadh ibn Muadh. Preserve the Bengali source unchanged as a confirmed content/speaker discrepancy; do not transfer the other languages attribution into this field.',review_status='resolved_source_content_mismatch')
        return d
    names=[];spans=[[0,len(text)]]
    if (book,number)==('abudawud','2424'):
        spans={'ara':lambda:before(text,'يَعْنِي حَدِيثَ'),
               'ben':lambda:before(text,'ইমাম আবূ দাঊদ'),
               'eng':lambda:before(text,', that is,'),
               'urd':lambda:excluding(text,' ( یعنی سنیچر ( ہفتے ) کے روزے کی ممانعت والی حدیث )','ابوداؤد کہتے ہیں')}[prefix]()
        names=[{'ara':'الأَوْزَاعِيِّ','ben':'আল-আওযাঈ','eng':"Al-Auza'i",'urd':'اوزاعی'}[prefix]]
        kind='historical_report'
        note='Al-Awzai reports his own withholding of a transmission and its later circulation. This is a historical transmission account; the referenced report body and an independent authenticity judgement are not supplied here.'
    elif (book,number)==('abudawud','3338'):
        spans={'ara':lambda:before(text,'وَبَلَغَنِي'),
               'ben':lambda:before(text,'ইমাম আবূ দাঊদ'),
               'eng':lambda:excluding(text,' (i.e. narrated a tradition which differs from your version)','I have been told'),
               'urd':lambda:before(text,'ابوداؤد کہتے ہیں')}[prefix]()
        names=[{'ara':'شُعْبَةَ','ben':'শু‘বাহ','eng':"Shu'bah",'urd':'شعبہ'}[prefix]]
        kind='historical_report'
        note='The source reports an exchange between an unnamed man and Shubah. The unnamed interlocutor is not identified by the bank. The appended transmission criticism attributed to Yahya ibn Main remains source context.'
    elif (book,number)==('abudawud','3339'):
        names=[{'ara':'شُعْبَةَ','ben':'শু‘বাহ','eng':"Shu'bah",'urd':'شعبہ'}[prefix]]
        kind='attributed_saying'
        note='This is Shubahs own testimonial statement comparing Sufyans memory with his. The source does not attribute it to the Prophet.'
    elif (book,number)==('abudawud','3587'):
        spans={'ara':lambda:before(text,'يَعْنِي حَرِيزَ'),
               'eng':lambda:excluding(text,", whose name is Hariz bin 'Uthman,"),
               'urd':lambda:excluding(text,' ( یعنی حریز بن عثمان سے )',' ۱؎')}[prefix]()
        names=[{'ara':'مُعَاذُ بْنُ مُعَاذٍ','eng':"Mu'adh bin Mu'adh",'urd':'معاذ بن معاذ'}[prefix]]
        kind='attributed_saying'
        note='Muadh ibn Muadh gives his own testimonial assessment of Abu Uthman al-Shami. The source speaker is Muadh, not the Prophet; the Bengali source discrepancy is retained separately.'
    elif (book,number)==('nasai','4221'):
        names={'ara':['حَبِيبِ بْنِ الشَّهِيدِ','مُحَمَّدُ بْنُ سِيرِينَ','الْحَسَنَ'],
               'ben':['হাবীব ইবন শাহীদ','মুহাম্মদ ইবন সীরীন','হাসান'],
               'eng':['Habib bin Ash-Shahid','Muhammad bin Sirin','Al-Hasan']}[prefix]
        kind='historical_report'
        note='Habib reports Ibn Sirins transmission inquiry and al-Hasans reply naming his source. Only the supplied dialogue is quoted; the aqiqah report body is not inserted or attributed to the Prophet here.'
    elif (book,number)==('nasai','5752'):
        names=[{'ara':'أَبَا أُسَامَةَ','ben':'আবু উসামা','eng':'Abu Usamah'}[prefix]]
        kind='attributed_saying'
        note='Abu Usamah gives his own observation of Abdullah ibn al-Mubaraks pursuit of knowledge. This is an attributed scholarly testimonial saying.'
    d.update(classification='source_numbered_attributed_report',quotation_spans=spans,
             report_type=kind,reported_speakers=[speaker(text,n,spans) for n in names],
             report_classification_note=note,review_status='resolved_source_report')
    if len(spans)>1:
        d.update(source_report_count=1,source_report_relationship='separate_passages_of_one_source_report',source_passage_boundaries=spans)
    return d

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-root',type=Path,required=True)
    p.add_argument('--output-root',type=Path,required=True)
    p.add_argument('--catalog-root',type=Path,required=True)
    a=p.parse_args()
    source=a.input_root;out=a.output_root
    state=json.loads((source/'imports/web-fawaz-20261112/state.json').read_text())
    prior_path=source/'reports/fawaz-import-review/continuation-20261113/fresh-reviews/held-final.json.gz'
    prior=json.loads(gzip.decompress(prior_path.read_bytes()))
    old={(r['provider_book'],r['typed_hadithnumber']):r for r in prior['records']}
    old_catalog=json.loads(gzip.decompress((a.catalog_root/'assembled-reviews.json.gz').read_bytes()))
    old_keys={(d['provider_book'],d['provider_edition'].split('-')[0],d['typed_hadithnumber']) for d in old_catalog['decisions']}
    records=[];decisions=[];inventory=[];c=collections.Counter();languages=collections.defaultdict(collections.Counter)
    original_files={}
    for path in (source/'upstream-editions').glob('*.json'):
        if path.name=='verified-primary-files.json':continue
        raw=path.read_bytes();spec=state['inputs']['editions/'+path.name]
        assert len(raw)==spec['bytes'] and digest(raw)==spec['sha256'],path
        original_files[path.stem]=json.loads(raw)
    for path in sorted((source/'imports/web-fawaz-20261112/held').glob('*.jsonl.gz')):
        book=path.name.split('.')[0];data=path.read_bytes();rel=REPORT+'/input/held/'+path.name
        dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        rows=[json.loads(line) for line in gzip.decompress(data).splitlines()]
        inventory.append({'path':rel,'bytes':len(data),'sha256':digest(data),'provider_book':book,'records':len(rows)})
        for row in rows:
            number=row['typed_hadithnumber'];key=(book,number);previous=old[key]
            assert row['classification']['classification']=='held'
            nonempty=any(v['row']['text'].strip() for vs in row['source_versions'].values() for v in vs)
            recovered=key in RECOVERED
            if nonempty:
                assert number in RATIONALES.get(book,{}),key
                rationale=RATIONALES[book][number]
            else:
                rationale='Every supplied source-language text field is empty at its exact saved source position. Preserve this provider occurrence and its own references. There is no supplied wording to extract; a different edition is not inserted into this pinned source.'
            if recovered: category='source_report_recovered'
            elif not nonempty: category='source_empty'
            elif key==('malik','631.5'): category='source_placeholder'
            elif key==('bukhari','4843'): category='source_chain_without_matn'
            elif key==('malik','787.5'): category='source_quran_and_legal_explanation'
            else: category='source_explanation_or_commentary'
            fields=[];own_decisions=[]
            for prefix,versions in sorted(row['source_versions'].items()):
                for v in versions:
                    original=v['row'];text=original['text'];length=len(text)
                    spec=state['inputs']['editions/'+prefix+'-'+book+'.json']
                    assert v['source_sha256']==spec['sha256'] and v['source_path']==spec['path']
                    assert digest(text.encode())==previous['source_field_sha256'][prefix]
                    d=decision_for(book,number,prefix,text)
                    if d:
                        assert (book,prefix,number) not in old_keys,(book,prefix,number)
                        decisions.append(d);own_decisions.append(prefix)
                    if prefix+'-'+book in original_files:
                        assert original_files[prefix+'-'+book]['hadiths'][v['position']]==original
                        c['verified_primary_source_rows']+=1;languages[prefix]['verified_primary_source_rows']+=1
                    else:c['primary_source_rows_requiring_full_checkout_validation']+=1;languages[prefix]['primary_source_rows_requiring_full_checkout_validation']+=1
                    outcome=('empty_source_field' if not text.strip() else
                             'resolved_source_content_mismatch' if d and d.get('action')=='source_context_only' else
                             'reviewed_report_passages' if d else category)
                    fields.append({'provider_edition':prefix+'-'+book,'position':v['position'],
                        'source_path':v['source_path'],'source_sha256':v['source_sha256'],
                        'source_row_sha256':digest(raw_json(original)),
                        'source_text_sha256':digest(text.encode()),'source_text_codepoints':length,
                        'source_text_utf8_bytes':len(text.encode()),'source_text_is_empty':not bool(text.strip()),
                        'checked_spans':[[0,length]] if text else [],
                        'inspection':'complete_nonempty_source_field_read' if text.strip() else 'exact_empty_source_field_verified',
                        'outcome':outcome,'source_numbering':{k:original.get(k) for k in ('hadithnumber','arabicnumber','reference')},
                        'source_grades_as_supplied':original.get('grades',[])})
                    c['source_fields']+=1;languages[prefix]['source_fields']+=1
                    c['nonempty_source_fields' if text.strip() else 'empty_source_fields']+=1
                    languages[prefix]['nonempty_source_fields' if text.strip() else 'empty_source_fields']+=1
                    if text.strip():c['nonempty_codepoints']+=length;languages[prefix]['nonempty_codepoints']+=length
            record={'provider_book':book,'typed_hadithnumber':number,
                'disposition':'registered_source_report' if recovered else 'resolved_source_exclusion',
                'category':category,'review_status':'complete','reason':rationale,
                'all_supplied_language_fields_checked':True,'source_fields':fields,
                'prior_review':{'category':previous['category'],'reason':previous['reason'],'automated_classification':row['classification']},
                'reader_admission_requires_separate_positive_span_decisions':True,
                'original_wording_and_references_preserved':True,'source_gap_filled':False,
                'independent_authenticity_assessment':False}
            if own_decisions:record['additional_review_editions']=[pre+'-'+book for pre in own_decisions]
            records.append(record);c[category]+=1
    assert len(records)==len(old)==244
    assert {(b,n) for b,rs in RATIONALES.items() for n in rs}=={(r['provider_book'],r['typed_hadithnumber']) for r in records if any(not f['source_text_is_empty'] for f in r['source_fields'])}
    assert len(decisions)==22 and sum(d.get('action')=='source_context_only' for d in decisions)==1
    assert c['source_fields']==895 and c['nonempty_source_fields']==204 and c['nonempty_codepoints']==50159
    new_catalog={'schema':'hadith-bank-fawaz-reviewed-spans-v1','repository':REPOSITORY,'revision':REVISION,
        'review_date_utc':'2026-11-13','scope':'Six conservatively recovered numbered source reports; all complete own-language fields read. One Bengali speaker discrepancy remains explicit source context.',
        'decisions':decisions}
    review_spec=write_json(out,REPORT+'/additional-reviews.json.gz',new_catalog,True)
    ledger={'schema':'hadith-bank-fawaz-held-dispositions-v1','repository':REPOSITORY,'revision':REVISION,
        'baseline_repository':'blaghtayt-alt/Hadith-Bank','baseline_commit':BASE_COMMIT,
        'review_date_utc':'2026-11-13','cohort_size':244,
        'scope':'All 244 formerly held provider occurrences. Resolved exclusions are preserved outside the reader; unresolved source availability is not converted into narration text. This does not review language-context queues belonging to already registered IDs.',
        'source_row_hash_encoding':'UTF-8 JSON with sorted keys, compact separators, ensure_ascii=false and one final newline',
        'prior_review':{'path':prior_path.relative_to(source).as_posix(),'bytes':prior_path.stat().st_size,'sha256':digest(prior_path.read_bytes())},
        'input_held_archives':inventory,'records':records}
    ledger_spec=write_json(out,REPORT+'/dispositions.json.gz',ledger,True)
    write_json(out,REPORT+'/dispositions.json',ledger)
    references=[]
    for book,number,ibook,ihad,evol,ebook,ehad in [
        ('abudawud','2424',14,112,None,13,2418),('abudawud','3338',23,13,None,22,3332),
        ('abudawud','3339',23,14,None,22,3333),('abudawud','3587',25,17,None,24,3580),
        ('nasai','4221',40,10,5,40,4226),('nasai','5752',51,214,6,51,5755)]:
        references.append({'provider_book':book,'typed_hadithnumber':number,
          'primary_reference_url':'https://sunnah.com/'+book+':'+number,'checked_date_utc':'2026-11-13',
          'observed_source_identity_matches':True,'check_scope':'Own reported speaker, complete report wording and separately labelled source numbering compared; no new wording or assessment imported.',
          'sunnah_collection_reference':{'collection':book,'number':int(number)},
          'sunnah_in_book_reference':{'book':ibook,'hadith':ihad},
          'sunnah_english_translation_reference':{'volume':evol,'book':ebook,'hadith':ehad},
          'numbering_systems_kept_separate':True,'canonical_mapping_inferred_from_fawaz_id':False,
          'source_grades_overwritten':False,'source_response_snapshot_claimed':False})
    write_json(out,REPORT+'/reference-checks.json',{'schema':'hadith-bank-separate-source-reference-checks-v1','records':references})
    summary={'schema':'hadith-bank-fawaz-held-resolution-summary-v1','repository':REPOSITORY,'revision':REVISION,
        'baseline_commit':BASE_COMMIT,'cohort_occurrences':244,'nonempty_occurrences':75,
        'recovered_occurrences':6,'resolved_excluded_occurrences':238,'unresolved_attribution_occurrences_in_cohort':0,
        'additional_decisions':22,'positive_language_decisions':21,'resolved_content_mismatch_fields':1,
        'source_gaps_not_filled':171,'counts':dict(c),'languages':{k:dict(v) for k,v in sorted(languages.items())},
        'full_checkout_primary_validation_required':c['primary_source_rows_requiring_full_checkout_validation']>0,
        'all_recovered_fields_verified_against_pinned_primary_editions':True,
        'existing_review_decisions_preserved':len(old_catalog['decisions']),
        'existing_decision_identity_conflicts':0,'expected_registered_occurrences_after_verified_export':36226,
        'expected_held_occurrences_after_verified_export':238,'provider_occurrences':36464,
        'publication_status':'prepared_for_parent_integration_not_published_by_this_review',
        'additional_review_descriptor':review_spec,'held_disposition_descriptor':ledger_spec,
        'scope_limit':'All 244 formerly held IDs are reviewed. Previously registered IDs with unreviewed sibling-language context are outside this cohort. Independent Pro QC and authenticity certification are not claimed.'}
    write_json(out,REPORT+'/summary.json',summary)
    manifest=json.loads((a.catalog_root/'catalog/fawaz-review-inputs.json').read_text())
    manifest.setdefault('additional_reviews',[]).append(review_spec)
    assert 'held_dispositions' not in manifest
    manifest['held_dispositions']=ledger_spec
    write_json(out,'catalog/fawaz-review-inputs.json',manifest)
    (out/REPORT/'build_resolution.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({'records':len(records),'new_decisions':len(decisions),'counts':dict(c),'languages':summary['languages']},sort_keys=True))

if __name__=='__main__':main()
