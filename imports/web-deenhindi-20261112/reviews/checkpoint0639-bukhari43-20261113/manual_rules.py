"""Explicit boundaries after89 complete own-field readings; no heuristic approvals."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RECEIPT = json.loads((ROOT/'complete-source-first-reading-receipt.json').read_bytes())
READINGS = {}
for row in RECEIPT['readings']:
    READINGS.setdefault(row['occurrence_id'].replace('deenhindi-', ''), {})[row['language']] = row['source_first_note']
SPECS = {}

def put(number, kind, speaker, reason, **rules):
    key = 'bukhari:' + number
    SPECS[key] = {'id': key, 'decision': 'register', 'languages': ['hi','ur'],
        'read_languages': list(READINGS[key]), 'field_notes': dict(READINGS[key]),
        'report_type': kind, 'speaker': speaker, 'reason': reason, **rules}

def comp(start, end, kind, speaker):
    return {'start_at': start, 'stop_before': end, 'report_type': kind, 'speaker': speaker}

put('2228','prophetic_historical_marriage_report','Anas reporting the supplied Safiyyah/Dihyah/Prophet sequence',
    'Keep the complete own historical report and its literal names/spelling; no missing detail or external identity is supplied.')
put('2230','prophetic_sale_report','Jabir reporting the Prophet’s supplied sale',
    'The own field contains the complete finite action; the mudabbar term is not expanded or retranslated.')
put('2231','prophetic_sale_report','Jabir, explicitly heard by Amr, reporting the Messenger’s sale',
    'Preserve this independently read source occurrence and chain without merging it with2230.')
for number in ['2232','2233']:
    put(number,'prophetic_question_and_answer','Zayd ibn Khalid and Abu Hurayrah reporting the actual question and Prophet’s reply',
        'Each separate Hindi and Urdu field was read completely. Preserve the unmarried condition and the third-or-fourth alternative; matching strings do not merge parent identities.')
put('2239','prophetic_instruction_with_historical_practice_and_transmitter_uncertainty',
    'Ibn Abbas’s reported Medina practice and Prophetic instruction, with the source’s explicit Ismail duration uncertainty',
    'Keep the Medina population scope and the duration predicate, with the named one/two versus two/three uncertainty visible as transmission qualification rather than Prophetic uncertainty. Preserve the own measure-or-weight conjunction.')
put('2239.2','source_pointer_without_report_body','No finite report speaker/body is supplied by these five fields',
    'All five complete fields were read. Each supplies only a chain or same-way pointer plus measure/weight wording fragments. No predicate, command or missing report is borrowed from2239.',
    decision='exclude', languages=[])
put('2240','prophetic_trade_instruction_report','Ibn Abbas reporting the Prophet’s Medina instruction',
    'Preserve the own two/three-year practice and weight/term wording; do not insert a missing measure from adjacent records.')
put('2240.2','qualified_pronominal_abbreviated_instruction',
    'Ibn Abi Najih transmits an instruction from the respectful aap/آپ speaker with a printed honorific; the field does not spell out that person’s name',
    'The own field supplies an actual finite advance-payment instruction. Retain its pronominal/honorific attribution without borrowing an expanded speaker identity from2240. Only the synonymous transaction term is glossary context.',
    exclude_substrings={'hi':['(सलफ)'],'ur':['(سلف)']},
    annotations={'hi':'The respectful pronoun and honorific are printed, but no expanded name is supplied in this field. Its actual command is retained with that qualified source attribution.',
                 'ur':'The source gives آپ with its honorific and an actual instruction; an unprinted explicit name is not filled from the neighboring occurrence.'})
put('2241','prophetic_arrival_and_trade_instruction','Ibn Abbas reporting the explicitly named Prophet’s arrival and instruction',
    'Retain the source’s parenthetic arrival destination and the essential advance-sale subject; these define actual narrative and transaction scope rather than a dictionary synonym.')
for number in ['2242','2243']:
    put(number,'companion_inquiry_and_historical_trade_testimony',
        'The source’s Muhammad-or-Abdullah ibn Abi al-Mujalid reports Ibn Abi Awfa’s answer and the narrator’s subsequent inquiry/confirmation from Ibn Abza',
        'Preserve the explicit narrator-name alternative, actual inquiry and historical answer, and the within-field confirmatory response without synthesizing an expanded second quotation. The two terminology synonyms are context.',
        exclude_substrings={'hi':['(पेशगी सौदे)','(सलफ़)'],'ur':['(پیشگی سودے)','(سلف)']},
        annotations={'hi':'Muhammad or Abdullah remains an unresolved source name alternative. The final Ibn Abza reply is only the supplied within-field confirmation, not a reconstructed duplicate quotation.',
                     'ur':'The source’s narrator-name alternative and abbreviated confirmatory reply remain literal; no expanded identities or repeated wording are manufactured.'})
put('2244','distinct_companion_inquiries_with_language_specific_source_gap',
    'Muhammad ibn Abi al-Mujalid reports the source-named respondents; Hindi’s final voice/wording gap is not filled from Urdu',
    'Keep the coherent initial inquiry and each own-field finite continuation. Hindi preserves the finite dispatch clause but the following broken ka-mamla/first-person seam remains context. Urdu supplies the complete separately named second inquiry and answer. Do not transfer goods, names or missing wording between fields.',
    exclude_substrings={'hi':['(सलफ)'],'ur':['(سلف)']}, components={
      'hi':[comp(None,'फिर उन्हों ने मुझे अब्दुर रहमान बिन कब्ज़ी','companion_historical_trade_testimony','The Hindi source-named Abdullah respondent supplies the coherent initial testimony and follow-up answer.'),
            comp('फिर उन्हों ने मुझे अब्दुर रहमान बिन कब्ज़ी','का मामला करते थे','finite_dispatch_report_fragment','The source narrator states that he was sent to the Hindi-printed Abd al-Rahman bin Kabzi; the damaged following voice/body is not reconstructed.')],
      'ur':[comp(None,'پھر انہوں نے مجھے عبدالرحمن بن ابزی','companion_historical_trade_testimony','Abdullah ibn Abi Awfa’s answer and the source narrator’s inquiry.'),
            comp('پھر انہوں نے مجھے عبدالرحمن بن ابزی',None,'separate_companion_historical_trade_testimony','The narrator’s separately named Abd al-Rahman ibn Abza inquiry and his actual answer.') ]},
    annotations={'hi':'The source names/spellings and wheat-only wording remain literal. Only the finite sending clause is retained before the damaged final seam; its unassigned collective continuation remains complete context, and Urdu is not used to repair it.',
                 'ur':'This own field supplies wheat, barley and olives and a complete second answer. Those additional details remain its own text and are not transferred to Hindi.'})
put('2245','finite_transmitted_trade_practice_variants',
    'A collective voice in Muhammad ibn Abi al-Mujalid’s abbreviated transmission and two expressly Shaybani-introduced variants; no unprinted eyewitness era is asserted',
    'The actual first predicate, within-field olive addition and final finite wording are preserved as transmitted components in one report family. No Ibn Abi Awfa identity or Prophetic era is imported.',
    shared_report_family=True, components={
      'hi':[comp(None,'शैबानी ने कहा: और','transmitted_collective_trade_practice','The source’s collective we voice through Muhammad ibn Abi al-Mujalid; ultimate participants and time remain unspecified.'),
            comp('शैबानी ने कहा: और','शैबानी ने कहा: हम','transmitted_additive_trade_variant','Shaybani’s expressly supplied olive addition to the finite predicate already present in this own field.'),
            comp('शैबानी ने कहा: हम',None,'transmitted_collective_trade_variant','The collective-we variant explicitly introduced by Shaybani, without an invented eyewitness role.')],
      'ur':[comp(None,'شیبانی نے کہا: اور','transmitted_collective_trade_practice','The source’s collective we voice through Muhammad ibn Abi al-Mujalid; ultimate participants and time remain unspecified.'),
            comp('شیبانی نے کہا: اور','شیبانی نے کہا: ہم','transmitted_additive_trade_variant','Shaybani’s expressly supplied olive addition to the finite predicate already present in this own field.'),
            comp('شیبانی نے کہا: ہم',None,'transmitted_collective_trade_variant','The collective-we variant explicitly introduced by Shaybani, without an invented eyewitness role.')]})
put('2246','prophetic_report_and_anonymous_conversational_explanation',
    'Ibn Abbas relays the Prophet’s prohibition; an unnamed questioner and a different man seated near Ibn Abbas exchange the actual later explanation',
    'Keep the report separately from the anonymous actually quoted answer, which is not compiler dictionary text or Ibn Abbas’s own reply. The final Mu’adh route supplies only an objectless prohibition and same-hadith pointer and remains context.',
    shared_report_family=True, components={
      'hi':[comp(None,'एक शख़्स ने पूछा','prophetic_prohibition_report','Ibn Abbas, answering Abu al-Bakhtari’s own inquiry, relays the Prophet’s prohibition.'),
            comp('एक शख़्स ने पूछा',"और मु'आज़ ने बयान किया",'anonymous_question_and_explanatory_answer','An unnamed questioner and a man seated near Ibn Abbas; the estimate answer is this man’s actual utterance.')],
      'ur':[comp(None,'ایک شخص نے پوچھا','prophetic_prohibition_report','Ibn Abbas, answering Abu al-Bakhtari’s own inquiry, relays the Prophet’s prohibition.'),
            comp('ایک شخص نے پوچھا','اور معاذ نے بیان کیا','anonymous_question_and_explanatory_answer','An unnamed questioner and a man seated near Ibn Abbas; the estimate answer is this man’s actual utterance.')]})
for number in ['2247','2248']:
    put(number,'two_separately_attributed_prophetic_reports','Abu al-Bakhtari reports separate Ibn Umar and Ibn Abbas replies',
        'Each own field was read. Keep the distinct respondents, currencies and readiness alternatives; only the transaction-definition parenthesis is glossary context.',
        exclude_substrings={'hi':['(पेशगी सौदा)'],'ur':['(پیشگی سودا)']}, components={
          'hi':[comp(None,'और मैं ने इब्न अब्बास','prophetic_report_via_ibnumar','Ibn Umar replies with the supplied Prophetic prohibitions.'),
                comp('और मैं ने इब्न अब्बास',None,'prophetic_report_via_ibnabbas','Ibn Abbas gives his own source-supplied Prophetic prohibition wording.')],
          'ur':[comp(None,'اور میں نے ابن عباس','prophetic_report_via_ibnumar','Ibn Umar replies with the supplied Prophetic prohibitions.'),
                comp('اور میں نے ابن عباس',None,'prophetic_report_via_ibnabbas','Ibn Abbas gives his own source-supplied Prophetic prohibition wording.')]})
for number in ['2249','2250']:
    put(number,'two_prophetic_reports_and_anonymous_explanatory_dialogue',
        'Ibn Umar and Ibn Abbas relay their own reports; the final interpretation is spoken by an unnamed man beside Ibn Abbas',
        'Preserve all three actual voice groups and the source’s cut/storage answer. Do not harmonize it to2246 or attribute it to the Prophet.',
        components={
          'hi':[comp(None,'मैं ने इब्न अब्बास से भी','prophetic_report_via_ibnumar','Ibn Umar’s actual answer relaying the Prophet’s prohibitions.'),
                comp('मैं ने इब्न अब्बास से भी','मैं ने पूछा: वज़न','prophetic_report_via_ibnabbas','Ibn Abbas’s separate actual answer relaying the Prophet’s prohibition.'),
                comp('मैं ने पूछा: वज़न',None,'anonymous_explanatory_dialogue','The source narrator asks; an unnamed man seated near Ibn Abbas gives the actual harvest/storage interpretation.')],
          'ur':[comp(None,'میں نے ابن عباس سے بھی','prophetic_report_via_ibnumar','Ibn Umar’s actual answer relaying the Prophet’s prohibitions.'),
                comp('میں نے ابن عباس سے بھی','میں نے پوچھا: وزن','prophetic_report_via_ibnabbas','Ibn Abbas’s separate actual answer relaying the Prophet’s prohibition.'),
                comp('میں نے پوچھا: وزن',None,'anonymous_explanatory_dialogue','The source narrator asks; an unnamed man seated near Ibn Abbas gives the actual harvest/storage interpretation.')]})
put('2251','prophetic_credit_purchase_and_pledge_report','Aisha reporting the Prophet’s source-supplied purchase and armour pledge',
    'Retain the complete report and unnamed counterparty without an external identity, altered object or new legal interpretation.')
put('2253','prophetic_instruction_with_finite_transmitted_variant','Ibn Abbas’s report and the Abdullah ibn Walid/Sufyan/Ibn Abi Najih variant',
    'The variant’s quoted measure/weight wording plus its own parenthetic should-be predicate supply an actual finite instruction. Retain them together under the stated route; the bare chain/comparison introduction remains context.',
    shared_report_family=True, components={
      'hi':[comp(None,'और अब्दुल्लाह बिन वलीद ने कहा','prophetic_instruction_report','Ibn Abbas’s own historical-practice and Prophetic instruction report.'),
            comp("'पैमाने और वज़न की ताअय्युन के साथ'",None,'finite_transmitted_instruction_variant','The actual quoted instruction in the Abdullah ibn Walid route, completed by its printed parenthetic transaction predicate.')],
      'ur':[comp(None,'اور عبداللہ بن ولید نے کہا','prophetic_instruction_report','Ibn Abbas’s own historical-practice and Prophetic instruction report.'),
            comp('”پیمانے اور وزن کی تعیین کے ساتھ“',None,'finite_transmitted_instruction_variant','The actual quoted instruction in the Abdullah ibn Walid route, completed by its printed parenthetic transaction predicate.')]})
for number in ['2254','2255']:
    put(number,'joint_companion_historical_trade_testimony',
        'The source-named Abd al-Rahman ibn Abza and Abdullah ibn Abi Awfa jointly answer Muhammad ibn Abi Mujalid',
        'Retain the collective named answer, historical practice and actual follow-up inquiry without splitting unassigned words between the two respondents. Only the synonymous transaction label is context.',
        exclude_substrings={'hi':['(सलाम)'],'ur':['(سلم)']})
put('2256','prophetic_prohibition_with_attributed_transmitter_clarification',
    'The source-named Abdullah relays the prohibition; Nafi supplies his own explicitly quoted clarification',
    'Do not expand Abdullah’s name or transfer Nafi’s explanation into Prophetic speech. Preserve Hindi’s printed defective jaan-le wording without correcting it to the Urdu birth verb.',
    shared_report_family=True, components={
      'hi':[comp(None,"नाफ़े' ने 'हबल-उल-हबला'",'prophetic_prohibition_report','The source-named Abdullah reports the trading practice and Prophet’s prohibition.'),
            comp("नाफ़े' ने 'हबल-उल-हबला'",None,'attributed_transmitter_explanatory_saying','Nafi’s own expressly attributed explanation, not additional words of the Prophet.')],
      'ur':[comp(None,'نافع نے «حبل الحبلة»','prophetic_prohibition_report','The source-named Abdullah reports the trading practice and Prophet’s prohibition.'),
            comp('نافع نے «حبل الحبلة»',None,'attributed_transmitter_explanatory_saying','Nafi’s own expressly attributed explanation, not additional words of the Prophet.')]},
    annotations={'hi':'The final Hindi jaan-le wording is preserved exactly; no birth-verb correction or expanded narrator name is imported from another language.'})
put('2257','prophetic_preemption_report_with_scope_limit','Jabir’s report of the Prophet’s award and its source-stated boundary/road limit',
    'Keep both the undivided-property rule and its limiting consequence; the latter is a reported qualification, not an invented extra direct quotation.')
put('2259','prophetic_gift_priority_dialogue','Aisha asks and the Prophet answers about the neighbor with the nearer door',
    'Keep both printed chains and the full source dialogue. Only the second-chain label is apparatus.',
    exclude_substrings={'hi':['(दूसरी सनद)'],'ur':['(دوسری سند)']})
put('2261','prophetic_appointment_dialogue_with_preserved_transmission_note','Abu Musa reports the visit, his lack of prior knowledge and the Prophet’s response',
    'The main actual dialogue remains. The my-tribe identity gloss and final unnamed lan/la formula-comparison tail remain complete source context, with its unresolved wording explicitly preserved rather than resolved.',
    exclude_substrings={'hi':['(मेरे क़बीला)'],'ur':['( میرے قبیلہ )']},
    stop_before={'hi':'(यहाँ रावी को शक है की)','ur':'( یہاں راوی کو شک ہے کہ )'})
put('2263','historical_hiring_and_migration_report','The own source narrator reports the Prophet and Abu Bakr’s hiring, trust, appointment and journey',
    'Retain the actual migration-time setting and historical predicates. The entire kharrit lexical-definition clause is context. Hindi’s shortened chain and source defects remain unfilled; no guide name or corrected place is inferred.',
    exclude_substrings={'hi':["(हदीथ के लफ्ज़) 'खरीत' के माँ'अणि रहबर में माहिर के हैं."],
                        'ur':['( حدیث کے لفظ ) «خريت» کے معنی راہبری میں ماہر کے ہیں۔']},
    annotations={'hi':'The Hindi narrator-name spelling, shortened chain, ghar-i-taur wording and other source defects remain literal. The full Urdu chain/place wording is not used to repair them.'})
for number in ['2265','2266']:
    put(number,'prophetic_judgment_report_and_separate_companion_judgment',
        'Ya’la reports the Prophetic episode; the grandfather in the Ibn Jurayj/Ibn Abi Mulaykah route reports Abu Bakr’s similar case',
        'Retain Ya’la’s own assessment and complaint purpose. The battle-name label is apparatus. The final route supplies a complete actual Abu Bakr judgment, separately typed without harmonizing judges or asserting that the two cases are identical.',
        exclude_substrings={'hi':['(ग़ज़वा-ए-तबुक)'],'ur':['(غزوہ تبوک)']}, components={
          'hi':[comp(None,'इब्न-ए-जुरैज ने','prophetic_judgment_and_dialogue_report','Ya’la’s supplied servant dispute and the Prophet’s actual judgment/dialogue; unnamed participants remain unnamed.'),
                comp('एक आदमी ने दूसरे का हाथ काटा',None,'companion_judgment_report','The actual similar case through the source’s unnamed grandfather route, with Abu Bakr expressly identified as judge.')],
          'ur':[comp(None,'ابن جریج نے','prophetic_judgment_and_dialogue_report','Ya’la’s supplied servant dispute and the Prophet’s actual judgment/dialogue; unnamed participants remain unnamed.'),
                comp('ایک آدمی نے دوسرے کا ہاتھ کاٹا',None,'companion_judgment_report','The actual similar case through the source’s unnamed grandfather route, with Abu Bakr expressly identified as judge.')]})
put('2274','prophetic_prohibition_and_companion_interpretive_dialogue',
    'Ibn Abbas relays the prohibition and then gives his own answer to the source questioner',
    'The trading-caravan and beyond-market parentheses are essential scope. Keep Ibn Abbas’s actual broker interpretation separately attributed; it is a reported answer, not compiler dictionary text.',
    shared_report_family=True, components={
      'hi':[comp(None,'मैं ने पूछा, ऐ इब्न-ए-अब्बास','prophetic_prohibition_report','Ibn Abbas explicitly relays the Prophet’s scoped prohibition.'),
            comp('मैं ने पूछा, ऐ इब्न-ए-अब्बास',None,'companion_explanatory_dialogue','The source questioner addresses Ibn Abbas, who gives the supplied broker interpretation.')],
      'ur':[comp(None,'میں نے پوچھا، اے ابن عباس','prophetic_prohibition_report','Ibn Abbas explicitly relays the Prophet’s scoped prohibition.'),
            comp('میں نے پوچھا، اے ابن عباس',None,'companion_explanatory_dialogue','The source questioner addresses Ibn Abbas, who gives the supplied broker interpretation.')]})
put('2275','companion_historical_dialogue_with_reported_quran_revelation',
    'Khabbab reports his dispute and As ibn Wa’il’s actual replies, followed by the source-supplied revelation quotation',
    'Keep the actual Quran wording/transliteration and source translation in their reported-revelation role, without adding a verse locator or assigning them as new Prophetic speech. Only the parenthetic identity category is apparatus.',
    exclude_substrings={'hi':['(मुशरिक)'],'ur':['( مشرک )']},
    annotations={'hi':'The supplied Quran transliteration and translation are retained as the actual quoted revelation within Khabbab’s account; no canonical verse number is added.',
                 'ur':'The printed Arabic Quran wording and Urdu rendering remain the report’s actual cited revelation, not a new Prophetic utterance or an appended locator.'})
put('2276','companion_journey_report_with_prophetic_response',
    'Abu Sa’id relates the unnamed Companions’ episode and the Prophet’s eventual answer/laughter',
    'Keep the entire coherent episode, actual recited opening and Fatiha name within the dialogue. The final same-hearing chain tail has no new body and remains context. No healer identity, complete surah or medical recommendation is supplied.',
    stop_before={'hi':'शुअबा ने कहा के अबुल बिश्र','ur':'شعبہ نے کہا کہ ابوالبشر'},
    annotations={'hi':'The source’s actual recitation phrase and Fatiha name belong to the narrated episode; they are not verse-locator apparatus. The healer remains unnamed.',
                 'ur':'The printed recitation and Surah Fatiha dialogue are preserved without filling the rest of the surah or identifying the anonymous healer.'})
put('2277','prophetic_payment_and_intercession_report','Anas reports Abu Taybah’s cupping and the Prophet’s payment/intercession',
    'Keep the actual one-or-two measure uncertainty and the levy-reduction request without resolving or expanding either.')
put('2278','prophetic_practice_with_distinct_reporter_inference',
    'Ibn Abbas’s named reporting frame supplies the action and the following reporter inference; the latter is not Prophetic speech',
    'Preserve the actual cupping/payment actions separately from the source reporter’s finite conditional reasoning, without turning that reasoning into a new direct Prophetic legal statement.',
    shared_report_family=True, components={
      'hi':[comp(None,'अगर पचना लगवाना नाजायज़','prophetic_practice_report','Ibn Abbas reports the Prophet’s cupping and payment.'),
            comp('अगर पचना लगवाना नाजायज़',None,'source_reporter_conditional_saying','The source’s Ibn Abbas reporting voice supplies the conditional inference, not the Prophet as a speaker.')],
      'ur':[comp(None,'اگر پچھنا لگوانا ناجائز','prophetic_practice_report','Ibn Abbas reports the Prophet’s cupping and payment.'),
            comp('اگر پچھنا لگوانا ناجائز',None,'source_reporter_conditional_saying','The source’s Ibn Abbas reporting voice supplies the conditional inference, not the Prophet as a speaker.')]})
put('2279','prophetic_practice_with_distinct_reporter_inference',
    'Ibn Abbas’s named reporting frame supplies the action and rhetorical inference in their separate roles',
    'Keep the reporter’s actual conditional question distinct from the Prophet’s narrated actions; preserve the source’s colloquial wording and do not create an extra Prophetic utterance.',
    shared_report_family=True, components={
      'hi':[comp(None,'अगर इस में कोई कराहत','prophetic_practice_report','Ibn Abbas reports the Prophet’s cupping and payment.'),
            comp('अगर इस में कोई कराहत',None,'source_reporter_conditional_saying','The source’s named reporting voice offers this rhetorical inference, not the Prophet as a direct speaker.')],
      'ur':[comp(None,'اگر اس میں کوئی کراہت','prophetic_practice_report','Ibn Abbas reports the Prophet’s cupping and payment.'),
            comp('اگر اس میں کوئی کراہت',None,'source_reporter_conditional_saying','The source’s named reporting voice offers this rhetorical inference, not the Prophet as a direct speaker.')]})
put('2283','prophetic_prohibition_report','Abu Hurayrah reporting the Prophet’s supplied earnings prohibition',
    'Preserve the complete source chain/body as an attributed historical report, without a new legal recommendation.')
put('2284','prophetic_prohibition_with_unrepaired_source_term','Ibn Umar reporting the Prophet’s printed fee-category prohibition',
    'The finite source report is supplied, while its opaque or damaged term remains literal. No normalized term or explanation is imported from an unread sibling.',
    annotations={'hi':'The exact source term नर-कदानय remains unrepaired and is not replaced with an inferred standard phrase.',
                 'ur':'The source’s compact نرکدانے term remains literal; no external lexical correction is asserted.'})
put('2289','prophetic_funeral_dialogue_with_companion_guarantee',
    'Salamah ibn al-Akwa reports three successive funeral exchanges and Abu Qatadah’s actual undertaking',
    'Keep every separate debt/estate answer and the printed three-dinar amounts within this source occurrence; no anonymous deceased is identified and no case is merged or invented.')
put('2292','companion_quran_explanation_and_historical_report',
    'Ibn Abbas is the explicitly named source explainer; the fraternity event concerns the Prophet’s act, not a newly asserted Prophetic utterance',
    'Keep the actual supplied Quran terms, heirs explanation and historical inheritance account, including the brotherhood-domain qualification of the revoked rule. Separate only the introductory Quran-verse label and its enclosing quotation punctuation while retaining every cited word. The final separate one-third/legal-execution parenthesis is preserved as appended source explanation, not silently lost or newly attributed as Prophetic speech.',
    exclude_substrings={'hi':["(कुरआन मजीद की आयत '","')"], 'ur':['( قرآن مجید کی آیت «','» )']},
    stop_before={'hi':'(जैसी और शख्सों के लिए भी','ur':'( جیسی اور شخصوں کے لیے بھی'},
    annotations={'hi':'The complete source includes a final explanatory one-third-estate qualification, retained verbatim in source context. The selected Ibn Abbas quotation is not represented as the whole surrounding legal discussion; no external ruling is inferred.',
                 'ur':'The appended one-third/legal-execution explanation remains complete visible source context. Actual Quran wording and the brotherhood-domain limitation remain within the attributed explanation, without a new canonical verse locator.'})
put('2293','prophetic_brotherhood_action_report','Anas reports the Prophet establishing the source-named brotherhood',
    'Keep the complete own report and separate identity; no content is merged with2292.')
put('2299','prophetic_instruction_report','Ali reports the Prophet’s command about the sacrificed animals’ coverings and hides',
    'Retain the supplied objects and sacrifice qualification exactly; no unprinted meat or other instruction is added.')
put('2301','companion_historical_report_with_separate_witness_observation',
    'Abd al-Rahman ibn Awf’s autobiographical account is followed by an unnamed later witness voice describing his scar demonstration',
    'Keep the actual history, family-or-property uncertainty, dialogue and arriving-group subject. The parenthetic ideological identity label is context. The final we-saw-scar statement is a finite separate witness observation, not Abd al-Rahman’s first-person speech or a guessed chain narrator.',
    exclude_substrings={'hi':['(काफिर दुश्मन-ए-इस्लाम)'],'ur':['( کافر دشمن اسلام )']}, shared_report_family=True,
    components={
      'hi':[comp(None,'अब्दुर रहमान बिन औफ (रदी अल्लाहु अन्हु) इस का निशान','companion_autobiographical_historical_report','Abd al-Rahman ibn Awf relates his agreement and Badr episode, including the actual quoted participants.'),
            comp('अब्दुर रहमान बिन औफ (रदी अल्लाहु अन्हु) इस का निशान',None,'unnamed_witness_historical_observation','The source’s final unnamed first-person-plural witness voice reports the later scar demonstration; no expanded narrator identity is assigned.')],
      'ur':[comp(None,'عبدالرحمٰن بن عوف رضی اللہ عنہ اس کا نشان','companion_autobiographical_historical_report','Abd al-Rahman ibn Awf relates his agreement and Badr episode, including the actual quoted participants.'),
            comp('عبدالرحمٰن بن عوف رضی اللہ عنہ اس کا نشان',None,'unnamed_witness_historical_observation','The source’s final unnamed first-person-plural witness voice reports the later scar demonstration; no expanded narrator identity is assigned.')]})

BOUNDARY_REFINEMENTS = {
 'bukhari:2244:hi': 'The frozen first-pass note provisionally retained the final damaged sentence as context. Exact boundary review confirms that its opening dispatch-to-the-source-named-Kabzi clause is itself a complete finite historical action. That bounded clause is retained as a qualified fragment; only the broken ka-mamla/unassigned collective continuation remains context. No Urdu words, corrected name or missing answer is imported.',
 'bukhari:2292:hi': 'Exact apparatus review separates the introductory Quran-verse label and its quotation/parenthesis delimiters from the actual cited verse words. Every verse word remains selected in Ibn Abbas’s source explanation; this refinement does not remove the heirs explanation, story bridge or brotherhood-domain qualification.',
 'bukhari:2292:ur': 'Exact apparatus review separates the introductory Quran-verse label and its delimiters while preserving all actually cited Arabic words, including the source’s own formatting mark. The attributed explanation and its substantive qualifications are unchanged.'
}

RETAINED_HONORIFICS = {
 '(रज़ियल्लाहु अन्हा)', '(रज़ियल्लाहु अन्हु)', '(रज़ियल्लाहु अन्हुमा)',
 '(रदी अल्लाहु अन्हु)', '(रदी अल्लाहु अन्हुम)', '(रदी अल्लाहु अन्हुमा)',
 '(रज़ि अल्लाहु अन्हा)', '(रज़ि अल्लाहु अन्हु)', '(रज़ि अल्लाहु अन्हुमा)',
 '(रज़ियल्लाहु अन्हा)', '(रज़ियल्लाहु अन्हु)', '(रज़ियल्लाहु अन्हुमा)',
 '(सल्लल्लाहु अलैहि वसल्लम)',
}
RETAINED_NONHONORIFIC = {}
def keep(number, language, literal, reason):
    RETAINED_NONHONORIFIC[('bukhari:'+number,language,literal)] = reason
for language, place, duration in [('hi','(मदीना के)','(के लिये करते थे)'),('ur','( مدینہ کے )','( کے لیے کرتے تھے )')]:
    keep('2239',language,place,'This source-supplied population domain qualifies the actual historical trade practice.')
    keep('2239',language,duration,'This affirmative duration predicate completes the actually supplied alternative wording; uncertainty remains explicit.')
for language, place, domain in [('hi','(मदीना)','(बै-ए-सलाम)'),('ur','( مدینہ )','( بیع سلم )')]:
    keep('2241',language,place,'The parenthesis supplies the actual narrated arrival destination, without an external location inference.')
    keep('2241',language,domain,'This is the instruction’s missing transaction subject/domain; omission would broaden the printed predicate.')
keep('2253','hi','(बै-ए-सलाम होनी चाहिए)','The parenthesis supplies the actual finite should-be transaction predicate of the transmitted variant.')
keep('2253','ur','( بیع سلم ہونی چاہئیے )','The parenthesis supplies the actual finite should-be transaction predicate of the transmitted variant.')
keep('2263','hi','(हिजरत करते वक़्त)','The source supplies the temporal setting of the actual hiring/journey narrative.')
keep('2263','ur','( ہجرت کرتے وقت )','The source supplies the temporal setting of the actual hiring/journey narrative.')
for number in ['2265','2266']:
    keep(number,'hi','(शिकायत लेकर)','The source supplies the actual complaint purpose of approaching the Prophet for the narrated judgment.')
    keep(number,'ur','(شکایت لے کر)','The source supplies the actual complaint purpose of approaching the Prophet for the narrated judgment.')
for language, trade, place in [('hi','(तिजारती)','(मंडी से आगे जा कर)'),('ur','( تجارتی )','( منڈی سے آگے جا کر )')]:
    keep('2274',language,trade,'This confines the stated prohibition to the printed trade-caravan domain.')
    keep('2274',language,place,'This confines the prohibited encounter to going beyond the market; ordinary encounters are not substituted.')
for language, meaning, bridge, scope in [
    ('hi',"('मवालिया' के माअनी)",'(का किस्सा यह है के)','(जो अंसार-ओ-मुहाजिरीन के दरमियान मुवाखत की वजह से था)'),
    ('ur','( «موالي‏» کے معنی )','( کا قصہ یہ ہے کہ )','( جو انصار و مہاجرین کے درمیان مواخاۃ کی وجہ سے تھا )')]:
    keep('2292',language,meaning,'The quoted term and meaning relation form Ibn Abbas’s actual attributed definition, not an unnamed dictionary insertion.')
    keep('2292',language,bridge,'The source supplies this narrative bridge into the actual historical explanation.')
    keep('2292',language,scope,'The parenthesis limits the revoked inheritance rule to the stated fraternity arrangement; it must not become a blanket inheritance claim.')
keep('2301','hi','(आने वाली जमात)','This supplies the actor of the attempted distraction in the actual narrative, preventing a misleading pronoun assignment.')
keep('2301','ur','( آنے والی جماعت )','This supplies the actor of the attempted distraction in the actual narrative, preventing a misleading pronoun assignment.')
RETAINED_MARKER_WORDS = {
 ('bukhari:2276','hi','सूरह'): 'The Fatiha name is part of the Prophet’s actual reported question, not a verse locator.',
 ('bukhari:2276','ur','سورۃ'): 'The Fatiha name is part of the Prophet’s actual reported question, not a verse locator.',
}
