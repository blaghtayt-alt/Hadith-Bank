"""Explicit own-field selections authored after the frozen complete source-first pass."""
from source_first_notes import NOTES

def part(key, lang, name, kind, speaker, start=None, end=None, family='source-numbered-report'):
    return {'from':start,'to':end,'component_id':name,'report_type':kind,'speaker':speaker,
            'source_report_family_id':key+':'+lang+':'+family}

def field(key,lang,kind,speaker,start=None,end=None,cuts=(),parts=None,refinement=None):
    return {'action':'excerpts','reason':NOTES[(key,lang)]+(' Final boundary refinement: '+refinement if refinement else ''),
            'report_type':kind,'speaker':speaker,
            'spans':parts if parts is not None else [part(key,lang,'reported-account',kind,speaker,start,end)],
            'omit_source_context':[{'text':literal,'expected_count':1,'reason':reason} for literal,reason in cuts]}

def context(key,lang):
    return {'action':'source_context','reason':NOTES[(key,lang)],'spans':[]}

records=[]
def row(key,fields,decision='register',reason=None):
    records.append({'key':key,'decision':decision,'reason':reason or
        ('The individually read own fields supply a finite report, actual observation or expressly abbreviated quoted body under its source-limited attribution. Every unselected original byte and unreviewed sibling remains source context; no absent speaker, wording or canonical identity is supplied.' if decision=='register' else
         'Every nonempty own field was read. This numbered source supplies a term or place-name explanation without an independent report-bearing body; preserve the complete source and metadata as context.'),
        'fields':fields})

k='abudawud:2548';speaker='Sahl ibn Hanzaliyah reports the emaciated camel and the Messenger’s actual riding/eating instructions about the speechless beasts.'
row(k,{'hi':field(k,'hi','companion_observation_with_prophetic_instruction',speaker),
       'ur':field(k,'ur','companion_observation_with_prophetic_instruction',speaker,end='۱؎')})
k='abudawud:2552';speaker='Abu Bashir reports the journey, resting-place setting and dispatched command to remove the camels’ neck strings. Malik’s conjectural evil-eye explanation is source context.'
row(k,{'hi':field(k,'hi','companion_report_of_prophetic_dispatched_instruction',speaker,end='मालिक कहते हैं:'),
       'ur':field(k,'ur','companion_report_of_prophetic_dispatched_instruction',speaker,end='مالک کہتے ہیں:')})
k='abudawud:2558';speaker='The source-named Abdullah ibn Umar reports the Messenger’s prohibition of riding the dung-eating camels; all source spellings and the restricted object remain exact.'
row(k,{l:field(k,l,'companion_report_of_prophetic_prohibition',speaker) for l in ('hi','ur')})
k='abudawud:2562';speaker='Ibn Abbas transmits the actual prohibition of making animals fight. No absent occasion or animal list is supplied.'
row(k,{'hi':field(k,'hi','companion_report_of_prophetic_prohibition',speaker),
       'ur':field(k,'ur','companion_report_of_prophetic_prohibition',speaker,end='۱؎')})
k='abudawud:2563';fs={}
for lang,variant,cuts in [
    ('hi','हिशाम कहते हैं:', [('(घुट्टी)','Lexical synonym for tahnik, retained as context.'),('(दाग़)','Lexical synonym for the already printed marking action, retained as context.')]),
    ('ur','ہشام کہتے ہیں:', [('( گھٹی )','Lexical synonym for tahnik, retained as context.'),('۱؎','Exact numbered footnote marker, not narrative.'),('( داغ )','Lexical synonym for the already printed marking action.')])]:
    main='Anas supplies bringing the newborn brother for tahnik and the animal-branding observation. '+('The Hindi observation link/subject is abbreviated and is not completed from Urdu.' if lang=='hi' else 'The Urdu explicitly supplies the observation of the Prophet branding sheep.')
    variant_speaker='Hisham expressly qualifies this as what he thinks Anas said: the actual ear-branding location is retained as a transmitted variant, not Hisham’s eyewitness account.'
    fs[lang]=field(k,lang,'companion_observation_with_uncertain_transmitted_variant',main+' '+variant_speaker,cuts=cuts,
        parts=[part(k,lang,'newborn-and-branding-observation','qualified_companion_observation',main,None,variant),
               part(k,lang,'uncertain-ear-location-variant','uncertain_transmitted_wording_variant',variant_speaker,variant,None)])
row(k,fs)
k='abudawud:2578';speaker='Aisha reports both races, the later heavier-body circumstance and the Messenger’s matching-win reply. The supplied repetition qualifier remains part of the second occasion.'
row(k,{l:field(k,l,'companion_personal_report_with_prophetic_reply',speaker) for l in ('hi','ur')})
k='abudawud:2582'
row(k,{l:context(k,l) for l in ('hi','ur','ar','en','ur-Latn')},'exclude')
k='abudawud:2583'
row(k,{'hi':field(k,'hi','companion_description_of_prophetic_possession','Anas supplies the sword-fitting description; the defective Hindi material word चंडी is preserved without substitution from another language.'),
       'ur':field(k,'ur','companion_description_of_prophetic_possession','Anas supplies the sword-fitting description and its own silver wording, with no added dimensions or externally repaired identity.')})
k='abudawud:2592';speaker='Jabir reports the white flag on the day the Messenger entered Makkah; no calendar date or larger campaign identity is added.'
row(k,{l:field(k,l,'companion_historical_observation',speaker) for l in ('hi','ur')})
k='abudawud:2610';kind='companion_report_of_prophetic_prohibition';speaker='Abdullah ibn Umar reports the prohibition of travelling with the Quran into enemy territory. Appended causal conjecture or the damaged unassigned rationale remains source context.'
short='The short Nafi-to-Ibn-Umar attribution is retained as coherent report framing; it is not stripped merely because it names an intermediary. The longer Arabic multi-step prefatory route is separately context.'
row(k,{
    'hi':field(k,'hi',kind,speaker,end='मन किया कि',refinement=short+' The damaged Hindi tail is not assigned Malik’s name from another field.'),
    'ur':field(k,'ur',kind,speaker,end='مالک کہتے ہیں:',refinement=short),
    'ar':field(k,'ar',kind,speaker,start='أَنَّ عَبْدَ اللَّهِ بْنَ عُمَرَ، قَالَ',end='قَالَ مَالِكٌ أُرَاهُ'),
    'en':field(k,'en',kind,speaker,end='The narrator Malik said'),
    'ur-Latn':field(k,'ur-Latn',kind,speaker,end='Malik kehte hain:',refinement=short),
})
k='abudawud:2617'
row(k,{l:context(k,l) for l in ('hi','ur','ar','en','ur-Latn')},'exclude')
k='abudawud:2618';speaker='Anas reports the Messenger’s actual spy dispatch to inspect Abu Sufyan’s caravan. The envoy’s source spelling, mission and purpose remain exact.'
row(k,{l:field(k,l,'companion_report_of_prophetic_mission',speaker) for l in ('hi','ur')})
k='tirmidhi:2549';q='سعید بن مسیب نے کہا: کیا';a='ابوہریرہ رضی الله عنہ نے کہا: ہاں';end='امام ترمذی کہتے ہیں:'
hi_speaker='The short Said-to-Abu-Hurayrah frame introduces this own condensed transmitted Paradise-market account. Urdu’s longer dialogue is not inserted, and its nested divine/inhabitant actions remain within reported narration.'
ur_parts=[
    part(k,'ur','encounter-and-companion-wish','successor_encounter_and_companion_wish','Said ibn al-Musayyab reports meeting Abu Hurayrah; the latter gives his actual wish to meet in the Paradise market.',None,q,'market-report-reception'),
    part(k,'ur','saids-market-question','successor_question_in_report_reception','Said ibn al-Musayyab asks whether there is a market there; these are his words, not the Messenger’s.',q,a,'market-report-reception'),
    part(k,'ur','companion-reply-and-transmitted-paradise-account','prophetic_account_transmitted_in_companion_reply','Abu Hurayrah replies yes and explicitly reports the Messenger’s account, including his own question to the Messenger and the supplied replies. Nested divine and inhabitant speech remains reported within that account; no separate canonical occurrences are invented.',a,end,'transmitted-paradise-market-account'),
]
row(k,{
    'hi':field(k,'hi','condensed_source_transmission_of_prophetic_account',hi_speaker,
        refinement='The complete short Said frame is retained because Abu Hurayrah’s printed told-him predicate refers back to that actual recipient. Removing it would discard supplied reception framing rather than merely remove a multi-step chain.'),
    'ur':field(k,'ur','reception_dialogue_with_transmitted_prophetic_account','The actual Said/Abu-Hurayrah reception dialogue is separately attributed from the transmitted Paradise account. The no-truly-inferior qualification remains actual narrative scope.',parts=ur_parts,
        cuts=[('( ادنیٰ مرتبے والے کو )','Explanatory referent label repeating the already supplied lower-rank participant; the full narrative rank comparison remains.'),
              ('( جنتی )','Explanatory identification of the already framed first-person Paradise inhabitants, not additional action or scope.')]),
})
k='tirmidhi:2551';speaker='Jarir reports the seated moon scene, seeing/crowding comparison, own time-qualified instruction and actual recitation with its source translation. The after-setting wording is not corrected from outside knowledge.'
row(k,{
    'hi':field(k,'hi','companion_report_with_prophetic_instruction_and_recitation',speaker,end='इमाम तिरमिज़ी कहते हैं:',
        cuts=[('(फ़ज्र और मग़रिब)','Prayer-name explanation of the already supplied times. The source’s wording, including Maghrib, remains context; no alternative name is substituted. The distinct verse-translation parenthesis remains selected.')]),
    'ur':field(k,'ur','companion_report_with_prophetic_instruction_and_recitation',speaker,end='۱؎',
        cuts=[('( فجر اور مغرب )','Prayer-name explanation of the printed time domains. Preserve it as context without harmonizing the source; the actual verse and translation remain selected.')]),
})
k='tirmidhi:2558';speaker='Abu Said transmits the ram/slaughter account and the two joy/grief counterfactuals under the printed Prophetic attribution; no longer wording is supplied.'
row(k,{'hi':field(k,'hi','companion_transmission_of_prophetic_account',speaker,end='इमाम तिरमिज़ी कहते हैं:'),
       'ur':field(k,'ur','companion_transmission_of_prophetic_account',speaker,end='امام ترمذی کہتے ہیں:')})
k='tirmidhi:2565';speaker='The source expressly quotes a finite hadith fragment about the houris raising their voices, but gives no ultimate speaker or complete parent report here. Yahya’s verse interpretation and the compiler’s listening explanation remain context, not Prophetic speech.'
starts={'hi':'जो हैदिथ में आया है की','ur':'جو حدیث میں آیا ہے کہ','ar':'مَا وَرَدَ فِي الْحَدِيثِ','en':'what has been mentioned in the Hadith','ur-Latn':'jo hadith mein aaya hai ki'}
row(k,{l:field(k,l,'abbreviated_report_fragment_with_unknown_ultimate_speaker',speaker,start=start) for l,start in starts.items()},reason='All five complete own fields were read. Each expressly contains a finite quoted hadith clause inside verse/listening explanation. Only that supplied fragment and its local reporting frame enter as abbreviated, ultimately unattributed report content; all exegesis, verse context and prefatory routes remain complete source context, with no inferred parent identity.')
k='tirmidhi:2579';speaker='Abu Hurayrah transmits the actual molar/Uhud comparison under its printed Prophetic attribution; grading remains separate context.'
row(k,{'hi':field(k,'hi','companion_transmission_of_brief_prophetic_saying',speaker,end='इमाम तिरमिधि कहते हैं:'),
       'ur':field(k,'ur','companion_transmission_of_brief_prophetic_saying',speaker,end='امام ترمذی کہتے ہیں:')})
k='tirmidhi:2619';speaker='This own field reports the finite prayer-abandonment clause but leaves its ultimate utterer unnamed. A’mash and the previous-chain pointer remain source context; neither a Companion nor the Prophet is inferred from familiar wording.'
row(k,{'hi':field(k,'hi','abbreviated_report_with_unknown_ultimate_speaker',speaker,start='जिस में कहा गया:'),
       'ur':field(k,'ur','abbreviated_report_with_unknown_ultimate_speaker',speaker,start='جس میں کہا گیا:')})
