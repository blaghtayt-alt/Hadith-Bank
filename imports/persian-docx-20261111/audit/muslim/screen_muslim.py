#!/usr/bin/env python3
"""Reproducible targeted screen of consuming hadith fields, with exact contexts."""
import collections,json,pathlib,re,unicodedata
HERE=pathlib.Path(__file__).resolve().parent
PATTERNS={
 'sect_names':r'شیع[هةه]|تشیع|رافض|روافض|اثناعشر|اثنی عشری|امامی[هةه]',
 'infallibility':r'معصوم|عصمة الایمة|عصمت.{0,12}امام',
 'twelve':r'اثنا عشر|اثنی عشر|دوازده',
 'appointment':r'وصیی|اوصیاء|خلیفتی|خلیفه.{0,15}بعد|ولی.{0,15}بعدی|جانشین.{0,15}علی|نص.{0,15}امامت',
 'occultation':r'امام زمان|غیبت.{0,12}امام|امام غایب|الغیبة|القایم',
 'taqiyya_bada_return':r'(?:^|\W)تقی[ةه](?:\W|$)|بداء|رجعة',
 'quran_alteration':r'تحریف.{0,15}قران|تحریف.{0,15}القران',
 'curse_companions':r'لعن.{0,30}(?:ابی بکر|ابوبکر|عمر|عثمان|عایشه)|سب.{0,15}اصحاب',
 'ahl_al_bayt':r'اهل.{0,2}بیت|اهل.{0,2}البیت|ثقلین',
}
TRANSLATE=str.maketrans({'ي':'ی','ى':'ی','ك':'ک','أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ئ':'ی'})
def normal_with_map(text):
 out=[];positions=[]
 for i,c in enumerate(text):
  for n in unicodedata.normalize('NFKC',c).translate(TRANSLATE):
   if unicodedata.category(n).startswith('M'):continue
   out.append(n);positions.append(i)
 return ''.join(out),positions

def screen_consuming_records(records):
 hits=[]
 for r in records:
  for field in ['arabic','translation']:
   raw=r['text'].get(field)or'';norm,positions=normal_with_map(raw)
   for category,pattern in PATTERNS.items():
    contexts=[]
    for m in re.finditer(pattern,norm):
     start=positions[max(0,m.start()-80)];end=positions[min(len(positions)-1,m.end()+170)]+1
     contexts.append({'start':start,'end':end,'exact_source_excerpt':raw[start:end],'normalized_trigger':m.group()})
    if contexts:hits.append({'id':r['id'],'kind':r['record_kind'],'field':field,'category':category,'source_local_number':r.get('number',{}).get('source_local'),'references':r.get('references'),'contexts':contexts})
 return hits

def build_screen_extension(records):
 hits=screen_consuming_records(records)
 (HERE/'doctrinal-primary-ancillary-hits.json').write_text(json.dumps(hits,ensure_ascii=False,indent=2)+'\n')
 return {'consuming_records_scanned':len(records),
 'main_records_scanned':sum(r['record_kind']=='main_hadith_occurrence'for r in records),
 'ancillary_records_scanned':sum(r['record_kind']!='main_hadith_occurrence'for r in records),
 'fields_scanned':['text.arabic','text.translation'],
 'normalization':'NFKC, removal of combining marks, Arabic/Persian kaf/ya and alef variants for retrieval only; quoted contexts retain exact consuming source strings',
 'patterns':PATTERNS,'candidate_field_category_counts':dict(collections.Counter(r['category']for r in hits)),
 'candidate_contexts_file':'doctrinal-primary-ancillary-hits.json',
 'manual_contextual_adjudications':[
  {'record_id':'fa-muslim-mundhiri-tarshabi-v2-p01581','source_local_number':1196,'source_citation':'Muslim 1822','finding':'Twelve caliphs, all Quraysh. The supplied narration and Persian translation do not name a line of twelve Imams, assert their infallibility, or add a Shia-specific identification.'},
  {'record_id':'fa-muslim-mundhiri-tarshabi-v2-p03139','source_local_number':1656,'source_citation':'Muslim 2424','finding':'Mantle and Quranic purification narration; no additional claim of Imam infallibility or divinely designated political succession is added.'},
  {'record_id':'fa-muslim-mundhiri-tarshabi-v2-p03141','source_local_number':1657,'source_citation':'Muslim 2408','finding':'Thaqalayn and care for the Prophet’s family, with the source’s clarification about wives and the families prohibited from receiving charity. No added sect-specific doctrinal claim identified.'},
  {'record_id':'fa-muslim-mundhiri-tarshabi-v2-p01300','source_local_number':1148,'source_citation':'Muslim 1759','finding':'Historical narration of Fatimah’s inheritance request, disagreement, Ali’s later reconciliation and pledge. Reporting the disagreement is not treated as a translator’s sectarian endorsement.'},
  {'record_id':'fa-muslim-mundhiri-tarshabi-v2-p03264','source_local_number':1693,'source_citation':'Muslim 2460','finding':'Ibn Masud and his mother were thought to belong to the household because of their frequent presence; no sect-specific doctrine.'},
  {'record_ids':['fa-muslim-mundhiri-tarshabi-v2-p01596','fa-muslim-mundhiri-tarshabi-v2-p04517'],'finding':'Appointment retrieval matches are two competing caliphs and Allah’s care for Muslims during the Dajjal ordeal, not appointment of an Imam.'},
  {'record_ids':['fa-muslim-mundhiri-tarshabi-v2-p03266','fa-muslim-mundhiri-tarshabi-v2-p03602','fa-muslim-mundhiri-tarshabi-v2-p03717'],'finding':'Occultation retrieval matches refer to a standing person, a worshipper standing in prayer, and backbiting (ghiba); none asserts an occulted Imam.'},
  {'category':'other_twelve_matches','finding':'Other matched quantities concern angels, prayer units, months, Friday attendees, dowry, camels, group leaders and hypocrites; none supplies a doctrine of twelve Imams.'},
  {'record_id':'fa-muslim-mundhiri-tarshabi-v2-p03529','source_local_number':1746,'source_citation':'Muslim 2540','finding':'The candidate about insulting companions explicitly prohibits it: لا تسبوا أصحابي. This is not an endorsement of insulting companions.'},
  {'category':'other_household_matches','finding':'The remaining Ahl al-Bayt keyword contexts concern ordinary households, charitable gifts, family responsibilities, permission for ruqya, sharing food and the narration vindicating Aishah. No added sect-specific doctrinal claim identified.'},
  {'category':'family_blessings','finding':'The explicit source-font blessing includes وآله. Family blessings and ordinary virtues are not classified as Shia-specific doctrine.'},
 ],
 'explicit_shia_doctrinal_endorsements_found':[],
 'limitations':'Targeted pattern retrieval followed by reading candidate passages and relevant surrounding source context; no claim that a comprehensive theological interpretation of every sentence was independently certified.'}
if __name__=='__main__':
 records=[]
 for v in [1,2]:
  for suffix in ['main','confirmed-ancillary-hadiths']:
   records.extend(json.loads(s)for s in(HERE/f'muslim-v{v}.{suffix}.jsonl').read_text().splitlines())
 report=build_screen_extension(records)
 print(json.dumps({k:report[k]for k in ['consuming_records_scanned','candidate_field_category_counts']},ensure_ascii=False))
