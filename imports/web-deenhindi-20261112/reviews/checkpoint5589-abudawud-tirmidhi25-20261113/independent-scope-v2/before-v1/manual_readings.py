"""Explicit own-field decisions after freezing all53 complete source readings."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
CHECKPOINT = '5589a3ffc3b43c3324ae26f2b6c4d33152834456'
NOTES = {r['key']: r for r in json.loads((ROOT/'source-first-notes.json').read_bytes())}
records = []

def cut(text, reason, count=1):
    return {'text': text, 'expected_count': count, 'reason': reason}
def part(start, end, component, kind, speaker, family):
    return {'from': start, 'to': end, 'component_id': component, 'report_type': kind,
            'speaker': speaker, 'source_report_family_id': family}
def field(key, lang, speaker, kind='prophetic_report', end=None, cuts=(), parts=None):
    return {'action': 'excerpt', 'reason': NOTES[key]['finding']+' '+NOTES[key]['language_notes'][lang],
            'spans': parts or [part(None, end, 'reported-account', kind, speaker, key+':'+lang+':reported-account')],
            'omit_source_context': list(cuts)}
def add(key, hi, ur):
    records.append({'key': key, 'decision': 'register', 'reason': NOTES[key]['finding'], 'fields': {'hi': hi, 'ur': ur}})
FOOTNOTE = 'Source footnote label; all surrounding actual narration is preserved.'

k='abudawud:2306'
add(k, field(k,'hi','Per explicitly attributed component.', cuts=[
    cut('(वह बनी आमिर बिन लुअय्य के एक फ़र्द और बद्री सहाबी हैं)', 'Inserted genealogy/Badri biographical explanation, retained as source context.'),
    cut('(की इद्दत)', 'Lexical waiting-period label following the already explicit four-month-ten-day period.')], parts=[
    part(None,'इब्न शिहाब कहते हैं:','subayah-correspondence-account','transmitted_companion_report_with_nested_dialogue','IbnShihab through Ubaydullah transmits the actual correspondence and Subayah account, preserving AbuSanabil objection and Messenger permission.',k+':hi:subayah-correspondence'),
    part('इब्न शिहाब कहते हैं:',None,'ibnshihab-legal-opinion','named_scholar_legal_statement','IbnShihab explicitly gives his own legal opinion; it is not a direct Prophetic statement.',k+':hi:ibnshihab-opinion')]),
 field(k,'ur','Per explicitly attributed component.', cuts=[
    cut('( وہ بنی عامر بن لوی کے ایک فرد، اور بدری صحابی ہیں )','Inserted genealogy/Badri biographical explanation, retained as source context.'),
    cut('( کی عدت )','Lexical waiting-period label following the already explicit four-month-ten-day period.'),cut('۱؎',FOOTNOTE)],parts=[
    part(None,'ابن شہاب کہتے ہیں:','subayah-correspondence-account','transmitted_companion_report_with_nested_dialogue','IbnShihab through Ubaydullah transmits the actual correspondence and Subayah account, preserving AbuSanabil objection and Messenger permission.',k+':ur:subayah-correspondence'),
    part('ابن شہاب کہتے ہیں:',None,'ibnshihab-legal-opinion','named_scholar_legal_statement','IbnShihab explicitly gives his own legal opinion; it is not a direct Prophetic statement.',k+':ur:ibnshihab-opinion')]))
k='abudawud:2310'
add(k,field(k,'hi','Per actual source voice.',cuts=[
    cut('...','Source omitted-continuation ellipsis; no missing recitation is supplied.'),
    cut('(सौराह आल-फ़ुरक़ान: ६८)','Explicit source chapter/verse locator; printed recitation and translation remain.')],parts=[
    part(None,'निज़ा कहा:','ranked-sins-question-answer','prophetic_report','IbnMasud explicitly asks the Messenger the ranked sins and transmits the printed answers.',k+':hi:ranked-sins'),
    part('निज़ा कहा:',None,'narratorial-revelation-confirmation','transmitted_narratorial_confirmation','The following also-said source voice reports revelation confirmation and the supplied verse wording; this is not converted into direct Messenger speech.',k+':hi:ranked-sins')]),
 field(k,'ur','Per actual source voice.',cuts=[
    cut('الخ','Explicit omitted-continuation pointer; actual preceding verse wording remains.'),
    cut('( سورۃ الفرقان: ۶۸ )','Explicit source chapter/verse locator; printed recitation and translation remain.')],parts=[
    part(None,'نیز کہا:','ranked-sins-question-answer','prophetic_report','IbnMasud explicitly asks the Messenger the ranked sins and transmits the printed answers, including the source-supplied answer-ranking frame.',k+':ur:ranked-sins'),
    part('نیز کہا:',None,'narratorial-revelation-confirmation','transmitted_narratorial_confirmation','The following also-said source voice reports revelation confirmation and the supplied verse wording; this is not converted into direct Messenger speech.',k+':ur:ranked-sins')]))
k='abudawud:2322'
add(k,field(k,'hi','IbnMasud reports the actual group fasts with the Prophet; twenty-nine versus thirty stays exact.','companion_copractice_testimony'),
 field(k,'ur','IbnMasud reports the actual group fasts with the Prophet; twenty-nine versus thirty stays exact.','companion_copractice_testimony'))
k='abudawud:2324'
add(k,field(k,'hi','AbuHurayra transmits the explicitly named Prophet; defective place/action joins and the absent explicit Makkah name are not filled.',cuts=[cut('(ठहरने)','Lexical definition of the already printed wuquf term.')]),
 field(k,'ur','AbuHurayra transmits the explicitly named Prophet; the source explicitly includes Makkah streets and all-place qualifiers.',cuts=[cut('( ٹھہرنے )','Lexical definition of the already printed wuquf term.'),cut('۱؎',FOOTNOTE)]))
k='abudawud:2330'
add(k,field(k,'hi','Sulaiman through the source-spelled Walid says he heard AbuAmr, explicitly identified as Auzai, give this definition; no Prophetic attribution is supplied.','named_scholar_lexical_saying',cuts=[cut('(महीने के शुरू)','Hindi lexical rendering of the already printed awail-e-mah expression, outside the attributed source wording.')]),
 field(k,'ur','Sulaiman through Walid says he heard AbuAmr, explicitly identified as Auzai, give this definition; no Prophetic attribution is supplied.','named_scholar_lexical_saying'))
k='abudawud:2331'
add(k,field(k,'hi','The source-spelled AbuMushir transmits Saeed ibnAbdulAziz actual finite definition. Compiler unnamed alternatives remain context.','named_scholar_lexical_saying',end='अबू दाऊद कहते हैं:'),
 field(k,'ur','AbuMishar transmits Saeed ibnAbdulAziz actual finite definition. Compiler unnamed alternatives remain context.','named_scholar_lexical_saying',end='ابوداؤد کہتے ہیں:'))
k='abudawud:2352'
add(k,field(k,'hi','SulaimanShaybani hears Abdullah ibnAbiAwfa recount the Messenger and Bilal, keeping all three instructions, sunset timing and eastward gesture.'),
 field(k,'ur','SulaimanShaybani hears Abdullah ibnAbiAwfa recount the Messenger and Bilal; the sole vehicle-from descent qualifier remains substantive.'))
k='abudawud:2368'
add(k,field(k,'hi','AbuQilabah reports Shaddad walking with the Prophet. Only that finite action is supplied; the subsequent speech body is absent.','abbreviated_companion_action_report',end='के इसी दौरान'),
 field(k,'ur','AbuQilabah reports Shaddad walking with the Prophet. Only that finite action is supplied; the subsequent speech body is absent.','abbreviated_companion_action_report',end='کہ اسی دوران'))

k='tirmidhi:2296'
records.append({'key':k,'decision':'exclude','reason':NOTES[k]['finding'],'fields':{
    lang:{'action':'source_context','reason':NOTES[k]['finding']+' '+NOTES[k]['language_notes'][lang], 'report_type':'chain_grade_and_transmitter_apparatus_only','speaker':'No underlying narrative or independent finite saying is supplied by this own field.'}
    for lang in ('hi','ur','ar','en','ur-Latn')}})
k='tirmidhi:2329'
add(k,field(k,'hi','Abdullah ibnBusr transmits the unnamed Arab question and the explicitly addressed Messenger answer.',end='इमाम तिर्मिज़ी कहते हैं:'),
 field(k,'ur','Abdullah ibnBusr transmits the unnamed Arab question and the explicitly addressed Messenger answer.',end='امام ترمذی کہتے ہیں:',cuts=[cut('۱؎',FOOTNOTE)]))
k='tirmidhi:2330'
add(k,field(k,'hi','AbuBakrah transmits the unnamed questioner and Messenger two answers about best and worst.',end='इमाम तिरमिधि कहते हैं:'),
 field(k,'ur','AbuBakrah transmits the unnamed questioner and Messenger two answers about best and worst.',end='امام ترمذی کہتے ہیں:',cuts=[cut('۱؎',FOOTNOTE)]))
k='tirmidhi:2335'
add(k,field(k,'hi','Abdullah ibnAmr recounts the Messenger passing and asking during hut repairs and the own printed comparative-nearness statement.',end='इमाम तिर्मिज़ी कहते हैं:',cuts=[cut('(पुराना)','Lexical synonym of the already printed decayed/old word.'),cut('(मौत)','Explanatory identification of the already printed matter term.')]),
 field(k,'ur','Abdullah ibnAmr recounts the Messenger passing and asking during hut repairs and the own printed comparative-nearness statement.',end='امام ترمذی کہتے ہیں:',cuts=[cut('( موت )','Explanatory identification of the already printed matter term.'),cut('۱؎',FOOTNOTE)]))
k='tirmidhi:2342'
add(k,field(k,'hi','Abdullah ibnShikhir observes the Prophet actual recitation and transmits the ensuing wealth statement.',end='इमाम तिर्मिज़ी कहते हैं:'),
 field(k,'ur','Abdullah ibnShikhir observes the Prophet actual recitation and transmits the ensuing wealth statement.',end='امام ترمذی کہتے ہیں:',cuts=[cut('۱؎',FOOTNOTE)]))
k='tirmidhi:2350'
add(k,field(k,'hi','Abdullah ibnMughaffal transmits the unnamed man professions and explicitly named Prophet replies, preserving repetitions and the conditional poverty comparison.',cuts=[cut('(लिबास)','Lexical garment explanation of the already printed tat term.')]),
 field(k,'ur','Abdullah ibnMughaffal transmits the unnamed man professions and explicitly named Prophet replies, preserving repetitions and the conditional poverty comparison.'))
k='tirmidhi:2356'
add(k,field(k,'hi','Per actual voice; the Hindi memory is incomplete and its absent bread/meat/frequency clause is not supplied.',parts=[
    part(None,'ऐसा (रज़ियल्लाहु अन्हा) ने कहा:','masruq-encounter','successor_eyewitness_report_with_nested_dialogue','Masruq narrates the Aisha encounter, her crying statement and his question.',k+':hi:masruq-aisha-encounter'),
    part('ऐसा (रज़ियल्लाहु अन्हा) ने कहा:','इमाम तिरमिधि कहते हैं:','aisha-retrospective-memory','companion_retrospective_statement_with_source_truncation','Aisha, whose second printed name is damaged, states her own memory; Hindi stops at the condition of the Messenger death.',k+':hi:masruq-aisha-encounter')]),
 field(k,'ur','Per actual voice.',parts=[
    part(None,'عائشہ رضی الله عنہا نے کہا:','masruq-encounter','successor_eyewitness_report_with_nested_dialogue','Masruq narrates the Aisha encounter, her crying statement and his question.',k+':ur:masruq-aisha-encounter'),
    part('عائشہ رضی الله عنہا نے کہا:','امام ترمذی کہتے ہیں:','aisha-retrospective-memory','companion_retrospective_statement','Aisha supplies her own oath and memory including the explicit bread/meat and twice-in-one-day statement.',k+':ur:masruq-aisha-encounter')]))
k='tirmidhi:2357'
add(k,field(k,'hi','Aisha retrospectively reports the Messenger two-consecutive-day barley-bread condition until death.','companion_observation_of_prophetic_practice',end='इमाम तिर्मिज़ी कहते हैं:'),
 field(k,'ur','Aisha retrospectively reports the Messenger two-consecutive-day barley-bread condition until death.','companion_observation_of_prophetic_practice',end='امام ترمذی کہتے ہیں:'))
k='tirmidhi:2358'
add(k,field(k,'hi','AbuHurayra reports the Messenger and household three-consecutive-day wheat-bread condition until death.','companion_observation_of_prophetic_household',end='इमाम तिरमिधि कहते हैं:'),
 field(k,'ur','AbuHurayra reports the Messenger and household three-consecutive-day wheat-bread condition until death.','companion_observation_of_prophetic_household',end='امام ترمذی کہتے ہیں:'))
k='tirmidhi:2359'
add(k,field(k,'hi','AbuUmamah reports barley bread relative to the explicitly supplied household need; the parenthetic scope remains.','companion_observation_of_prophetic_household',end='इमाम तिर्मिज़ी कहते हैं:'),
 field(k,'ur','AbuUmamah reports barley bread relative to the explicitly supplied household need; the parenthetic scope remains.','companion_observation_of_prophetic_household',end='امام ترمذی کہتے ہیں:',cuts=[cut('۱؎',FOOTNOTE)]))
k='tirmidhi:2363'
add(k,field(k,'hi','Anas reports the Messenger eating-support and fine-flour-bread conditions until death.','companion_observation_of_prophetic_practice',end='इमाम तिरमिधि कहते हैं:',cuts=[cut('(या मेज़)','Lexical alternative name of the already printed chauki support.')]),
 field(k,'ur','Anas reports the Messenger eating-support and fine-flour-bread conditions until death.','companion_observation_of_prophetic_practice',end='امام ترمذی کہتے ہیں:',cuts=[cut('( یا میز )','Lexical alternative name of the already printed chauki support.')]))
k='tirmidhi:2365'
add(k,field(k,'hi','Saad ibnAbiWaqqas gives his own early-history testimony and present conditional response to BanuAsad criticism; no direct Messenger speech.','companion_historical_testimony_and_admonition',end='इमाम तिर्मिज़ी कहते हैं:',cuts=[
    cut('(यानी काफ़िर को क़त्ल किया)','Explanatory gloss of bloodshed, retained as source context.'),
    cut('(ख़ारदार दरख़्त के फल)','Lexical definition of the printed hablah food term.')]),
 field(k,'ur','Saad ibnAbiWaqqas gives his own early-history testimony and present conditional response to BanuAsad criticism; no direct Messenger speech.','companion_historical_testimony_and_admonition',end='امام ترمذی کہتے ہیں:',cuts=[
    cut('( یعنی کافر کو قتل کیا )','Explanatory gloss of bloodshed, retained as source context.'),
    cut('( خاردار درخت کے پھل )','Lexical definition of the printed hablah food term.'),cut('۱؎',FOOTNOTE)]))
k='tirmidhi:2366'
add(k,field(k,'hi','Saad ibnMalik, explicitly source-identified as AbiWaqqas, gives his own first-archer/hardship testimony and present conditional response.','companion_historical_testimony_and_admonition',end='इमाम तिर्मिज़ी कहते हैं:'),
 field(k,'ur','Saad ibnMalik, explicitly source-identified as AbiWaqqas, gives his own first-archer/hardship testimony and present conditional response.','companion_historical_testimony_and_admonition',end='امام ترمذی کہتے ہیں:',cuts=[cut('۱؎',FOOTNOTE)]))
k='tirmidhi:2367'
add(k,field(k,'hi','Per actual source voice.',parts=[
    part(None,'वाह वाह,','ibnsirin-encounter','successor_eyewitness_framing','Muhammad ibnSirin describes his own presence, the garments and AbuHurayra nose-wiping and speech introduction.',k+':hi:ibnsirin-abuhurayra-encounter'),
    part('वाह वाह,','इमाम तिर्मिज़ी कहते हैं:','abuhurayra-retrospective-speech','companion_retrospective_statement','AbuHurayra speaks about his own former hunger and rejects the observer assumption of madness; no Prophet speech is supplied.',k+':hi:ibnsirin-abuhurayra-encounter')]),
 field(k,'ur','Per actual source voice.',cuts=[cut('۱؎',FOOTNOTE)],parts=[
    part(None,'واہ واہ،','ibnsirin-encounter','successor_eyewitness_framing','Muhammad ibnSirin describes his own presence, the garments and AbuHurayra nose-wiping and speech introduction.',k+':ur:ibnsirin-abuhurayra-encounter'),
    part('واہ واہ،','امام ترمذی کہتے ہیں:','abuhurayra-retrospective-speech','companion_retrospective_statement','AbuHurayra speaks about his own former hunger and rejects the observer assumption of madness; no Prophet speech is supplied.',k+':ur:ibnsirin-abuhurayra-encounter')]))
k='tirmidhi:2371'
add(k,field(k,'hi','AbuTalha reports the hunger complaint and printed one/two-stone sequence; the second garment-lifting actor is absent from the defective Hindi join and is not filled.','companion_report_with_source_attribution_defect',end='इमाम तिरमिधि कहते हैं:'),
 field(k,'ur','AbuTalha reports the hunger complaint, companions one-stone display and explicitly identified Messenger two-stone display.','companion_eyewitness_report',end='امام ترمذی کہتے ہیں:'))
k='tirmidhi:2372'
add(k,field(k,'hi','The source-spelled Numan ibnBashir admonishes his addressees and gives his own observation of the Prophet insufficient dates.','companion_admonition_with_prophetic_observation',end='इमाम तिरमिधि कहते हैं:'),
 field(k,'ur','Numan ibnBashir admonishes his addressees and gives his own observation of the Prophet insufficient dates.','companion_admonition_with_prophetic_observation',end='امام ترمذی کہتے ہیں:'))
k='tirmidhi:2377'
add(k,field(k,'hi','IbnMasud reports the Messenger, companions offer and Messenger comparison; the damaged departure wording stays exact.',end='इमाम तिरमिधि कहते हैं:'),
 field(k,'ur','IbnMasud reports the Messenger, companions offer and Messenger comparison, including the own full departure wording.',end='امام ترمذی کہتے ہیں:'))

def main():
    assert len(records)==len(NOTES)==25 and {r['key'] for r in records}==set(NOTES)
    for book in ('abudawud','tirmidhi'):
        obj={'schema':'hadith-bank-manual-source-reading-instructions-v1','source_checkpoint':CHECKPOINT,
             'actual_complete_field_scope':'All50 own Hindi/Urdu fields, plus Ar/En/UrduRoman of Tirmidhi2296;53 complete fields. No other reading is claimed.',
             'records':[r for r in records if r['key'].startswith(book+':')]}
        (ROOT/('manual-'+book+'.json')).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
if __name__=='__main__': main()
