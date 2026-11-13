"""Explicit decisions after all forty complete Hindi/Urdu source fields were read."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
CHECKPOINT='c2ab74d74821e244d8a83620f0e8e68dda694b16'
records=[]
def whole(reason,speaker,kind='prophetic_report',**extra):
    return dict(action='whole',reason=reason,speaker=speaker,report_type=kind,**extra)
def span(start,end,speaker,kind='prophetic_report',component='report-1',family=None):
    d=dict(start=start,end=end,speaker=speaker,kind=kind,component=component)
    if family:d['family']=family
    return d
def excerpt(reason,parts,cuts=(),**extra):
    out=[]
    for s in parts:
        x={'from':s['start'],'to':s['end'],'speaker':s['speaker'],'report_type':s['kind'],'component_id':s['component']}
        if s.get('family'):x['source_report_family_id']=s['family']
        out.append(x)
    return dict(action='excerpts',reason=reason,spans=out,omit_source_context=[{'text':t,'expected_count':1,'reason':r} for t,r in cuts],**extra)
def record(key,hi,ur):
    records.append({'key':key,'decision':'register','reason':'Both complete own Hindi and Urdu fields were read separately. Finite source-supplied material is admitted under the stated actual voices; unread siblings remain source context and no canonical identity or authentication is asserted.','fields':{'hi':hi,'ur':ur}})
FOOT='Exact footnote marker is source apparatus, retained as context without changing surrounding words or punctuation.'
GLOSS='Explicit lexical or identifying source gloss is retained as context; the surrounding finite narrative remains in its original wording.'
LOCATOR='Explicit Surah/verse locator is source context; actual quoted scripture and its supplied translation remain admitted.'

record('abudawud:823',
 whole('Read all470 characters in the provider Hindi field. Its actual script is Latin transliteration: preserve the hi field identity and every spelling while making the observed script explicit. The Fajr difficulty, question, quick-reading reply, Fatiha exception and stated consequence are complete own-source wording.',
       'Ubada ibn Samit recounting the Fajr prayer, group reply and the Prophet’s stated exception.',
       observed_script='Latn',source_script_note='The provider Hindi field contains Latin-script transliteration, not Devanagari. Its source field/language identity and exact wording are preserved; only the observed script metadata is corrected after complete reading.'),
 excerpt('Read every Urdu word. Preserve the Fajr setting, the Prophet’s question, the group’s own quick-reading response and the Fatiha exception/consequence. Only the single footnote marker is context.',
         [span(None,None,'Ubada ibn Samit recounting the Prophet’s question and instruction and the group’s actual reply.')],[('۱؎',FOOT)]))
record('abudawud:2157',
 whole('Read the complete Hindi field. Preserve the explicitly named Awtas-captive setting and both printed restrictions, including until childbirth and until one menstrual period; no contemporary legal application or endorsement is inferred.',
       'Abu Saeed Khudri reporting the Prophet’s two restrictions in the stated historical setting.'),
 whole('Read the complete Urdu field independently, including its nonbreaking space and quotation punctuation. Both source conditions remain exactly as printed; no circumstance or legal conclusion is added.',
       'Abu Saeed Khudri reporting the two restrictions expressly attributed to the Prophet.'))
record('abudawud:2166',
 whole('Read the full Hindi field. Aisha’s shared-cloth/menstruation account and the finite washing description are present, but the ending is repetitive and truncated. Preserve that damaged Hindi ending exactly; do not supply the Urdu clothing continuation or prayer statement.',
       'Aisha’s account heard by Khallas ibn Amr Hijri; the source Hindi ending remains incomplete and repetitive.'),
 whole('Read the entire Urdu field separately. It supplies both body/clothing washing limits and prayer in the same cloth. Preserve those own Urdu clauses without transferring them into the shorter damaged Hindi sibling.',
       'Aisha describing the shared cloth and the Prophet’s washing and prayer actions, heard by Khallas ibn Amr Hijri.'))
record('abudawud:2171',
 excerpt('Read all Hindi text. Preserve the unnamed questioner’s stated circumstances, the reported Jewish claim and the Prophet’s reply as this source’s dialogue. The parenthetic English technical definition of azl is source explanation, not an additional utterance.',
         [span(None,None,'Abu Saeed transmitting an unnamed man’s question and the Prophet’s reply.')],
         [('(कोइटस इंटरप्टस)',GLOSS)]),
 whole('Read the complete Urdu field. The unnamed man’s statement, reported claim and reply are all finite source dialogue; preserve the actual conditional about creation and do not convert it into new commentary.',
       'Abu Saeed transmitting an unnamed man’s own words and the Prophet’s reply.'))
record('abudawud:2172',
 whole('Read the whole Hindi field. Abdullah ibn Muhayriz asks Abu Saeed; the campaign experience belongs to Abu Saeed and his group. Keep both the inner-thought qualifier and the finite rhetorical consequence in parentheses, since they are the source’s own reported inner question, not a lexical definition. Preserve the question and reply without changing its wording.',
       'Abu Saeed recounting his group’s experience and their question to the Prophet, in answer to Abdullah ibn Muhayriz.'),
 whole('Read the entire Urdu field separately. The parentheses mark the group’s inner thought and actual rhetorical predicate; retain those source-supplied clauses, the temporal question and the reported reply. Abdullah ibn Muhayriz is the later questioner, not an invented eyewitness of the campaign.',
       'Abu Saeed’s group experience and reported question/reply, relayed in his answer to Abdullah ibn Muhayriz.'))
record('abudawud:2182',
 whole('Read the complete Hindi field. Preserve the source divorce event, Umar’s report, anger, return instruction, successive periods of purity/menstruation and the final without-touching condition. Keep every supplied timing restriction without importing a different version.',
       'Ibn Umar’s event conveyed through Umar to the Prophet, followed by the printed instruction.'),
 whole('Read the complete Urdu field. Preserve the same source’s actual temporal sequence and no-touching condition exactly; no external reconciliation or legal extrapolation is made.',
       'Ibn Umar’s event and the Prophet’s instruction conveyed through Umar.'))
record('abudawud:2188',
 excerpt('Read the full Hindi field. Initial chain/sigah comparison is context. The actual Ibn Abbas statement about one remaining divorce and its ascribed adjudication is finite material; preserve the defective repeated Allah/Rasul wording and do not reconstruct the missing original case.',
         [span('इब्न अब्बास (रदी अल्लाहु अन्हु) ने कहा:',None,
               'Ibn Abbas stating one remaining divorce and ascribing this decision to the Messenger in the source’s defective wording.','companion_statement')]),
 excerpt('Read the entire Urdu field including the source-critical tail. Admit the finite Ibn Abbas statement separately from the actual named Ibn Mubarak-to-Mamar question transmitted by Abu Dawud through Ahmad and Abdurrazzaq. That question is a bounded scholarly historical utterance, with no supplied answer or inferred Abu al-Hasan identity. The surrounding bare chain comparison, transmitter biography, grading and practice assessment remain context.',
         [span('ابن عباس رضی اللہ عنہما نے کہا:','ابوداؤد کہتے ہیں: میں نے احمد بن حنبل',
               'Ibn Abbas stating one remaining divorce and its source-ascribed Prophetic adjudication; the absent case is not reconstructed.','companion_statement','ruling-fragment'),
          span('ابوداؤد کہتے ہیں: میں نے احمد بن حنبل','ابوداؤد کہتے ہیں: ابوالحسن وہی',
               'Ibn Mubarak’s actual question addressed to Mamar, reported by Abu Dawud through Ahmad ibn Hanbal and Abdurrazzaq; no answer or external transmitter identity is asserted.','scholarly_historical_dialogue','ibn-mubarak-question')],
         [('۱؎',FOOT)]))
record('abudawud:2191',
 excerpt('Read the whole Hindi field. The opening same-chain/similar-report pointer is context, but two actual finite added oath clauses follow. Admit those exact clauses as a transmitted fragment; the chain names Abdullah ibn Amr, while the ultimate speaker is not supplied and is not upgraded to the Prophet.',
         [span('जिस ने गुनाह करने की क़सम',None,'The unnamed ultimate voice of the actual added clauses transmitted from Abdullah ibn Amr; no earlier body or Prophetic speaker is imported.','attributed_narration_fragment')]),
 excerpt('Read every Urdu word. Preserve the two finite added clauses and their actual negations. The earlier-chain pointer is context; ultimate attribution remains unspecified beyond the named transmission framing.',
         [span('جس نے گناہ کرنے کی قسم',None,'The unnamed ultimate voice in the supplied addition transmitted from Abdullah ibn Amr; no missing predecessor is filled.','attributed_narration_fragment')]))
record('abudawud:2203',
 whole('Read the complete Hindi field. Retain the source-supplied marital-choice domain in parentheses because it states what the reported choice concerns. Preserve the final defective/abbreviated wording and do not supply the Urdu sibling’s explicit final actor.',
       'Aisha describing the Prophet’s specified marital choice and the wives’ selection, with the Hindi final clause preserved as supplied.'),
 excerpt('Read the complete Urdu field. The parenthetic remain-or-not-in-marriage domain restricts the actual offered choice and stays with it; the final not-counting clause remains exactly as supplied. Only the footnote is context.',
         [span(None,None,'Aisha describing the Prophet’s specified choice, the wives’ selection and the supplied final clause.')],[('۱؎',FOOT)]))
record('abudawud:2213',
 excerpt('Read all1989 Hindi characters. Preserve Salama’s whole episode, the printed two-month and sixty-sa quantities, the sequential replies and the final me/or-for-me uncertainty. His return-to-people appraisal is separately attributed to him, while both parts share one source episode family; no quantity is normalized from a parallel.',
         [span(None,'इस के बाद मैं ने अपनी क़ौम','Salama ibn Sakhr describing his experience, his group’s refusal and his dialogue with the Prophet.','prophetic_report','case-and-dialogue','salama-zihar-episode'),
          span('इस के बाद मैं ने अपनी क़ौम',None,'Salama’s own return statement comparing the advice he received and reporting what was assigned to him.','companion_personal_statement','return-statement','salama-zihar-episode')]),
 excerpt('Read all1864 Urdu characters separately. Preserve duplicated source words, the full finite episode, sixty-sa wording and me/or-for-me alternative. The final appraisal is Salama’s own actual statement, not the Prophet’s speech, and stays in the same single episode family.',
         [span(None,'اس کے بعد میں نے اپنی قوم','Salama ibn Sakhr recounting his experience and the actual dialogue with the Prophet.','prophetic_report','case-and-dialogue','salama-zihar-episode'),
          span('اس کے بعد میں نے اپنی قوم',None,'Salama’s own statement to his people about their advice and the assignment he received.','companion_personal_statement','return-statement','salama-zihar-episode')]))
record('abudawud:2214',
 excerpt('Read every Hindi word. Keep the actual Quran incipit, the woman’s finite give-this-basket request, the complete dialogue and the separately attributed unnamed narrator’s sixty-sa measurement. The verse locator, husband-identification gloss and Abu Dawud’s later deduction/identity notes are source context. The two report components share the same case family; source spelling defects remain.',
         [span(None,'रावी का बयान है','The source-named Khawla bint Malik describing her complaint, the revealed wording and the reported dialogue.','prophetic_report','case','khawla-zihar-case'),
          span('रावी का बयान है','अबू दाऊद कहते हैं: इस औरत ने','An unnamed narrator supplying the basket’s sixty-sa measure in this same case; not silently attributed to Khawla.','narrator_observation','basket-measure','khawla-zihar-case')],
         [('(सूरह अल-मुजादिलाह: 1)',LOCATOR),('(यानी शौहर)',GLOSS)]),
 excerpt('Read all Urdu text. Preserve the Arabic Quran quotation with its actual supplied Urdu rendering and the finite request inside the woman’s dialogue. Keep the unnamed narrator’s sixty-sa measure as a separate component of the same case. The explicit locator, spouse gloss and Abu Dawud’s later deduction/biographical notes remain context.',
         [span(None,'راوی کا بیان ہے','The source-named Khuwaila bint Malik describing the complaint, revelation and dialogue with the Prophet.','prophetic_report','case','khawla-zihar-case'),
          span('راوی کا بیان ہے','ابوداؤد کہتے ہیں: کہ اس عورت نے','An unnamed narrator reporting the basket’s sixty-sa measure; the speaker is not replaced with the woman.','narrator_observation','basket-measure','khawla-zihar-case')],
         [('( سورۃ المجادلہ: ۱ )',LOCATOR),('( یعنی شوہر )',GLOSS)]))

record('tirmidhi:823',
 excerpt('Read the whole Hindi field. The named debate between Dahhak and Saad is actual historical dialogue, including the reported Umar prohibition and Saad’s own claim of doing the act with the Prophet. Keep each voice as printed; Tirmidhi’s final authenticity assessment is context.',
         [span(None,'इमाम तिर्मिज़ी कहते हैं:','Muhammad ibn Abdullah ibn Harith ibn Nawfal recounting the actual Dahhak/Saad exchange, with Saad’s own report of the Prophet’s practice.','historical_dialogue_with_attributed_prophetic_report')]),
 excerpt('Read the complete Urdu field separately. Admit the actual named exchange and its source-supplied attribution distinctions; do not collapse Dahhak’s or Saad’s words into one Prophetic statement. The final grade is source context.',
         [span(None,'امام ترمذی کہتے ہیں:','Muhammad ibn Abdullah ibn Harith ibn Nawfal reporting Dahhak and Saad’s dialogue and Saad’s source-ascribed practice report.','historical_dialogue_with_attributed_prophetic_report')]))
record('tirmidhi:2157',
 excerpt('Read the complete Hindi field. Preserve the reported dispute and the actual transliterated Quran quotation with its supplied translation, including the parenthetic address connective within that translation. The explicit chapter/verse locator and Tirmidhi’s grade/transmission tail are context; no new translation is created.',
         [span(None,'इमाम तिरमिज़ी कहते हैं:','Abu Hurayra recounting the dispute and the source-supplied revealed quotation and rendering.')],
         [('(अल-क़मर: 48-49)',LOCATOR)]),
 excerpt('Read every Urdu word. Keep the Arabic quotation and its own Urdu rendering as printed, including the address connective, with no theological or linguistic expansion. The explicit verse locator and compiler grading/chain tail remain source context.',
         [span(None,'امام ترمذی کہتے ہیں:','Abu Hurayra reporting the dispute and the source-supplied Quran quotation with its rendering.')],
         [('( القمر: ۴۸-۴۹ )',LOCATOR)]))
record('tirmidhi:2161',
 whole('Read all Hindi text. Preserve the source’s explicit father Yazid wording, farewell-pilgrimage circumstance and the narrator’s age seven. Do not replace the printed father/child relationship or repair this occurrence from another version.',
       'Saib ibn Yazid describing the source’s named Yazid/farewell-pilgrimage event and his own age.'),
 excerpt('Read the complete Urdu field including the later transmitter discussion. Admit the finite pilgrimage/age report and retain the source-supplied parenthetic father relationship, which qualifies the named actor rather than identifying an externally supplied person. The subsequent Yahya/Muhammad ibn Yusuf grading, genealogy and transmission statements remain source context.',
         [span(None,'یحییٰ بن سعید قطان کہتے ہیں:','Saib ibn Yazid reporting his source-identified father Yazid’s pilgrimage with the Prophet and his own age.')]))
record('tirmidhi:2179',
 excerpt('Read all1498 Hindi characters. The source introduces two Prophetic trust statements, then explicitly assigns the pebble gesture and following prediction to Hudhayfa, followed by his own trading memory. Preserve these source voices instead of normalizing a familiar parallel. The withdrawal report and its Hudhayfa demonstration share one report family; descent and personal trade memory remain separately described families. Retain night/morning conditions; the blister synonym and final grade are context.',
         [span(None,'फिर आप ने हम से अमानत','Hudhayfa reporting the Prophet’s first trust-descent statement.','prophetic_report','descent','trust-descent-report'),
          span('फिर आप ने हम से अमानत','फिर हुज़ैफ़ा (रज़ियल्लाहु अन्हु) एक कंकरी','Hudhayfa reporting the Prophet’s trust-withdrawal statement and its source-supplied timing and simile.','prophetic_report','withdrawal','trust-withdrawal-report'),
          span('फिर हुज़ैफ़ा (रज़ियल्लाहु अन्हु) एक कंकरी','हुज़ैफ़ा (रज़ियल्लाहु अन्हु) कहते हैं: मेरे ऊपर','Hudhayfa performing the pebble gesture and speaking the following prediction as explicitly assigned by this Hindi source.','companion_demonstration_and_statement','gesture-and-statement','trust-withdrawal-report'),
          span('हुज़ैफ़ा (रज़ियल्लाहु अन्हु) कहते हैं: मेरे ऊपर','इमाम तिर्मिज़ी कहते हैं:','Hudhayfa recounting his own former and current trading experience.','companion_personal_statement','trade-memory','hudhayfa-trade-memory')],
         [('(फफोला)',GLOSS)]),
 excerpt('Read all1514 Urdu characters including the repeated Quran wording. Retain both Prophetic statements, and separately preserve Hudhayfa’s explicitly assigned pebble demonstration/prediction and his personal trading memory. Do not reassign the printed Hudhayfa speech to the Prophet. Night/morning conditions remain; the blister synonym, three footnotes and final grade are context. Four ordered components represent three specified source families.',
         [span(None,'پھر آپ نے ہم سے امانت','Hudhayfa reporting the Prophet’s first trust-descent statement.','prophetic_report','descent','trust-descent-report'),
          span('پھر آپ نے ہم سے امانت','پھر حذیفہ رضی الله عنہ ایک کنکری','Hudhayfa reporting the Prophet’s trust-withdrawal statement, timing and simile.','prophetic_report','withdrawal','trust-withdrawal-report'),
          span('پھر حذیفہ رضی الله عنہ ایک کنکری','حذیفہ رضی الله عنہ کہتے ہیں: میرے اوپر','Hudhayfa performing the pebble gesture and uttering the following prediction as explicitly assigned by this Urdu source.','companion_demonstration_and_statement','gesture-and-statement','trust-withdrawal-report'),
          span('حذیفہ رضی الله عنہ کہتے ہیں: میرے اوپر','امام ترمذی کہتے ہیں:','Hudhayfa describing his personal former and current trading experience.','companion_personal_statement','trade-memory','hudhayfa-trade-memory')],
         [('۱؎',FOOT),('۲؎',FOOT),('۳؎',FOOT),('( پھپھولا )',GLOSS)]))
record('tirmidhi:2186',
 excerpt('Read the entire Hindi field. Keep Abu Dharr’s event, the question/reply and the actual supplied recitation with its Hindi translation in parentheses. The narrator’s subsequent recension attribution and the compiler’s grading/parallel list remain context; no conventional verse wording is substituted.',
         [span(None,'रावी कहते हैं:','Abu Dharr describing the Prophet’s question, answer and source-supplied recitation and rendering.')]),
 excerpt('Read the whole Urdu field independently. Preserve its printed Quran wording and own translation exactly, including the stated temporal/conditional response. The later Ibn Masud-recension identification and grading/parallel list are apparatus context.',
         [span(None,'راوی کہتے ہیں:','Abu Dharr recounting the question, answer and source-supplied recitation and rendering.')]))
record('tirmidhi:2187',
 excerpt('Read all Hindi text. Keep the waking event, actual repeated invocation, source’s gesture with fingers and its numerical form, question and conditional reply. The finger-instrument qualifier is part of the printed action; the fitna synonym and the compiler’s grading/chain comparison and transmitter lists are context.',
         [span(None,'इमाम तिर्मिज़ी कहते हैं:','Zaynab bint Jahsh describing the Prophet’s waking, invocation, gesture and reply.')],
         [('(फ़ितना)',GLOSS)]),
 excerpt('Read the complete Urdu field, including all compiler apparatus. Keep the actual Arabic invocation with Urdu rendering, three repetitions, finger gesture, question and conditional answer. The lexical fitna synonym, footnote and source grading/chain-list discussion are context; no standalone report body is reconstructed from those chain lists.',
         [span(None,'امام ترمذی کہتے ہیں:','Zaynab bint Jahsh describing the Prophet’s waking, invocation, gesture and reply.')],
         [('( فتنہ )',GLOSS),('۱؎',FOOT)]))
record('tirmidhi:2198',
 whole('Read the full Hindi field. Hasan Basri’s named explanation is an actual scholarly saying under the expanded source scope, including its quoted finite hadith wording whose ultimate speaker is not named here. Preserve the printed blood/life-only explanation and honorific; do not import the Urdu sibling’s honor/property words or promote it to a directly attributed Prophetic saying.',
       'Hasan Basri giving his own explanation and quoting the finite wording called a hadith by this source; its ultimate speaker is not supplied.','successor_explanatory_statement'),
 whole('Read every Urdu word. Admit Hasan Basri’s own explanation with its printed life, honor and property list and the quoted finite wording. Those own Urdu objects remain distinct from the shorter Hindi wording. No missing ultimate speaker or independent authenticity is asserted.',
       'Hasan Basri’s explanatory statement, with its source-quoted hadith wording retained under that frame and no ultimate speaker filled.','successor_explanatory_statement'))
record('tirmidhi:2203',
 excerpt('Read the entire Hindi field. Preserve Udaisa’s account of her father’s exchange with Ali, the conditional wooden-sword advice as actually relayed, his completed action and offer, and Ali’s response. Retain the parenthetic Messenger identification because it is the source’s actual advisor attribution, not an identity filled from elsewhere. The compiler’s grade/parallel tail is context.',
         [span(None,'इमाम तिर्मिज़ी कहते हैं:','Udaisa recounting her father Ahban’s exchange with Ali and the advice explicitly attributed within this own field to the source-identified Messenger through Ahban.','historical_dialogue_with_attributed_prophetic_report')]),
 excerpt('Read the whole Urdu field. Keep the finite historical exchange, conditional advice and the source-supplied parenthetic Messenger identification: that own-language phrase identifies the actual advisor. No external identity or missing body is supplied. The footnote and compiler grade/parallel tail are context.',
         [span(None,'امام ترمذی کہتے ہیں:','Udaisa describing her father Ahban’s exchange with Ali and the advice explicitly attributed by this own field to the source-identified Messenger through Ahban.','historical_dialogue_with_attributed_prophetic_report')],
         [('۱؎',FOOT)]))
record('tirmidhi:2206',
 excerpt('Read all Hindi text. Preserve Zubayr’s visit/complaint, Anas’s actual statement and explicit heard-from-your-Prophet attribution. The parenthetic comparison with the preceding year restricts the statement and remains admitted. The final compiler grade is context.',
         [span(None,'इमाम तिरमिज़ी कहते हैं:','Anas relaying the statement he expressly says he heard from the Prophet, in reply to Zubayr ibn Adi and companions.')]),
 excerpt('Read every Urdu word. Retain the complaint, Anas’s reply and explicit hearing attribution, including the previous-year comparison and endpoint. Only the final compiler grade is context.',
         [span(None,'امام ترمذی کہتے ہیں:','Anas’s source-attributed hearing from the Prophet, relayed to Zubayr ibn Adi’s group.')]))

if __name__=='__main__':
    source={r['collection']+':'+r['number']:r for r in map(json.loads,(ROOT/'input/cohort.jsonl').read_text().splitlines())}
    assert len(records)==len(source)==20 and {r['key'] for r in records}==set(source)
    reading_receipts=[]
    for r in records:
        for lang,instruction in r['fields'].items():
            name={'hi':'translationHindi','ur':'translationUrdu'}[lang]
            text=source[r['key']]['source_record'][name]
            reading_receipts.append({'id':'deenhindi-'+r['key'],'language':lang,'source_field':name,
                'source_text_sha256':hashlib.sha256(text.encode()).hexdigest(),'characters':len(text),
                'utf8_bytes':len(text.encode()),'complete_own_field_read':True,'primary_reading_note':instruction['reason']})
    assert len(reading_receipts)==40 and sum(r['characters'] for r in reading_receipts)==25926
    assert sum(r['utf8_bytes'] for r in reading_receipts)==54943
    for book in ('abudawud','tirmidhi'):
        out={'source_checkpoint':CHECKPOINT,'records':[r for r in records if r['key'].startswith(book+':')]}
        (ROOT/('manual-'+book+'.json')).write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    (ROOT/'complete-source-first-readings.json').write_text(json.dumps({'source_checkpoint':CHECKPOINT,'complete_fields_read':40,
        'characters':25926,'utf8_bytes':54943,'scope':'Only the forty own Hindi/Urdu source fields were read. These explicit source-bound notes were authored before native serialization. No other sibling is claimed as read.',
        'fields':reading_receipts},ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print('Wrote explicit notes for20 occurrences/40 complete fields; no network or source edits.')

