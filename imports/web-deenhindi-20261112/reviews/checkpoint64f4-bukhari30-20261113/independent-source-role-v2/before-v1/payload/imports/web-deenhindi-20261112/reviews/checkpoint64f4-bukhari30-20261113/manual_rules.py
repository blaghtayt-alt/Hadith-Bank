"""Explicit own-field boundaries authored after the frozen complete66-field pass."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RECEIPT=json.loads((ROOT/'source-first-complete-reading.json').read_bytes())
assert RECEIPT['complete_read_fields']==66 and not RECEIPT['candidate_created_or_inspected']
READINGS={}
for row in RECEIPT['fields']:
    READINGS.setdefault(row['occurrence_id'].removeprefix('deenhindi-'),{})[row['language']]=row['source_first_note']
SPECS={}
BOUNDARY_REFINEMENTS=[]
def put(number,kind,speaker,reason,**rules):
    key='bukhari:'+str(number)
    assert key not in SPECS
    SPECS[key]={'id':key,'decision':'register','languages':['hi','ur'],'read_languages':list(READINGS[key]),'field_notes':dict(READINGS[key]),'report_type':kind,'speaker':speaker,'reason':reason,**rules}
def comp(start,end,kind,speaker):
    return {'start_at':start,'stop_before':end,'report_type':kind,'speaker':speaker}

put('2709','companion_debt_payment_report_with_distinct_transmitted_variants',
    'Jabir gives the debt-payment encounter; Abu Bakr and Umar give the supplied joint reply; the appended finite details remain qualified transmitted variants.',
    'Keep the this-year fruit domain, notify-me command, unresolved seven/six alternatives and all actual replies. The lexical drying-place definition, pure routes, omission comparison and bare final Dhuhr mention remain complete context. The Asr-attendance and thirty-wasq additions are separate same-family source fragments, without harmonizing times or inventing an eyewitness link.',
    exclude_substrings={'hi':['(वो जगह जहाँ खजूर ख़ुश्क करते थे)'],'ur':['( وہ جگہ جہاں کھجور خشک کرتے تھے )']},shared_report_family=True,
    components={
      'hi':[comp('और उन से जाबिर बिन अब्दुल्लाह','तो उन्होंने कहा के रसूल अल्लाह','companion_debt_payment_and_dialogue_report','Jabir reports his father debt, the fruit/payment events and the actual dialogue, with the printed quantity alternatives.'),
            comp('तो उन्होंने कहा के रसूल अल्लाह','हिशाम ने वह्ब से','two_companions_joint_reply_within_report','The source reports Abu Bakr and Umar joint response; these are their supplied words, not additional Prophet speech.'),
            comp('अस्र के वक़्त (जाबिर',' और उन्होंने न अबू बक्र','qualified_transmitted_attendance_time_variant','The appended Hisham/Wahb/Jabir version supplies an Asr attendance detail. It is not asserted as an independent eyewitness account or reconciled with Maghrib.'),
            comp('ये भी बयान किया के (जाबिर',' और इब्न इसहाक़','qualified_transmitted_debt_amount_addition','The source explicitly supplies Jabir first-person thirty-wasq debt addition in the appended version.')],
      'ur':[comp('اور ان سے جابر بن عبداللہ','تو انہوں نے کہا کہ رسول اللہ','companion_debt_payment_and_dialogue_report','Jabir reports his father debt, the fruit/payment events and the actual dialogue, with the printed quantity alternatives.'),
            comp('تو انہوں نے کہا کہ رسول اللہ','ہشام نے وہب سے','two_companions_joint_reply_within_report','The source reports Abu Bakr and Umar joint response; these are their supplied words, not additional Prophet speech.'),
            comp('عصر کے وقت ( جابر',' اور انہوں نے نہ ابوبکر','qualified_transmitted_attendance_time_variant','The appended Hisham/Wahb/Jabir version supplies an Asr attendance detail. It is not asserted as an independent eyewitness account or reconciled with Maghrib.'),
            comp('یہ بھی بیان کیا کہ ( جابر',' اور ابن اسحاق','qualified_transmitted_debt_amount_addition','The source explicitly supplies Jabir first-person thirty-wasq debt addition in the appended version.')]},
    annotations={lang:'The source gives Maghrib in the main account, an explicit Asr-attendance variant, and a bare Dhuhr-prayer mention retained as context. None is repaired into a single settled time; all original words and the six/seven alternatives remain.' for lang in ('hi','ur')})

put('2714','companion_pledge_report','Ziyad reports hearing Jarir own pledge account.',
    'Preserve the complete supplied goodwill-to-every-Muslim pledge. The preceding multistep route is context; no prayer or zakat condition is inserted from another source occurrence.',
    start_at={'hi':'उन से ज़ियाद बिन अलाक़ा ने बयान किया','ur':'ان سے زیاد بن علاقہ نے بیان کیا'})
put('2715','companion_pledge_report','Jarir ibn Abdullah gives his own pledge with the three supplied conditions.',
    'Keep prayer, zakat and goodwill exactly as this own source prints them. The prefatory route is context and this source ID remains separate from2714.',
    start_at={'hi':'और उन से जरीर बिन अब्दुल्लाह','ur':'اور ان سے جریر بن عبداللہ'})

put('2718','companion_camel_sale_report_and_multiple_qualified_transmitted_variants',
    'Jabir reports the main encounter; each later finite version is attributed only through its own printed transmission framing. The four-uqiya uncertainty has an unnamed first-person voice.',
    'Preserve all supplied conditions, prices, temporal scopes, speech predicates, the retained price and the explicit quantity uncertainty. Keep each affirmative appended version separately in the same report family. Pure multistep routes, corroboration-only pointers, currency conversion, omitted-price comparison and the final compiler preference remain complete context. No price is harmonized and no compiler authenticity opinion becomes a narration.',
    shared_report_family=True,
    components={
      'hi':[
        comp('उन्होंने बयान किया के मुझ से जाबिर','शु\'बा ने मुग़ीरा','companion_camel_encounter_and_conditional_sale_report','Amir frames Jabir own camel encounter, condition, payment and return; the source non-returned-price clause remains.'),
        comp('और उन से जाबिर (रदी अल्लाहू अन्हु) ने बयान किया के रसूल','इसहाक़ ने जरीर','qualified_transmitted_riding_permission_variant','The source supplies Jabir riding-permission variant, without a newly asserted eyewitness event.'),
        comp('(जाबिर (रदी अल्लाहू अन्हु) ने फ़रमाया था)','अता वग़ैरह ने बयान किया','qualified_transmitted_sale_condition_variant','The source explicitly assigns the conditional first-person sale statement to Jabir.'),
        comp('अता वग़ैरह ने बयान किया','मुहम्मद बिन मुनकिदिर','qualified_transmitted_prophetic_riding_statement','Ata and others relay the expressly attributed riding-to-Medina statement; no missing intermediate identity is supplied.'),
        comp('मुहम्मद बिन मुनकिदिर','ज़ैद बिन असलम ने जाबिर (रदी अल्लाहू अन्हु) के वासिते','qualified_transmitted_sale_condition_variant','Muhammad ibn Munkadir relays the supplied Jabir riding condition.'),
        comp('ज़ैद बिन असलम ने जाबिर (रदी अल्लाहू अन्हु) के वासिते','अबुल ज़ुबैर ने जाबिर (रदी अल्लाहू अन्हु) से बयान किया','qualified_transmitted_prophetic_riding_statement','Zaid ibn Aslam relays the supplied Jabir version with the actual riding instruction.'),
        comp('अबुल ज़ुबैर ने जाबिर (रदी अल्लाहू अन्हु) से बयान किया','अ\'माश ने सालिम से बयान किया','qualified_transmitted_riding_permission_variant','Abu al-Zubair relays the supplied Jabir permission wording.'),
        comp('और उन से जाबिर (रदी अल्लाहू अन्हु) ने के (रसूल','उबैदुल्लाह और इब्न-ए-इसहाक़','qualified_transmitted_prophetic_riding_statement','The final Jabir frame supplies the ride-home version; earlier Amas/Salim route stays context.'),
        comp('और उन से जाबिर (रदी अल्लाहू अन्हु) ने के ऊँट','इस रिवायत की मुताबा','qualified_transmitted_one_uqiya_purchase_variant','The final Jabir frame supplies a one-uqiya purchase version without asserting a separate sale.'),
        comp('और उन से जाबिर (रदी अल्लाहू अन्हु) ने (के नबी','इस हिसाब से','qualified_transmitted_four_dinar_purchase_statement','The printed Ibn Jurair/Ata route leads to this Jabir four-dinar quotation; its source spelling is not repaired.'),
        comp('और उन्होंने जाबिर (रदी अल्लाहू अन्हु) से अपनी रिवायत में एक औक़िया','अबू इसहाक़ ने सालिम','qualified_transmitted_one_uqiya_gold_variant','The source supplies one uqiya of gold as an affirmative version detail, without choosing it over the other amounts.'),
        comp('और उन्होंने जाबिर (रदी अल्लाहू अन्हु) से अपनी रिवायत में दो सौ','और दाऊद बिन क़ैस','qualified_transmitted_two_hundred_dirham_variant','The source supplies a two-hundred-dirham version with its printed Jabir attribution.'),
        comp('और उन से जाबिर (रदी अल्लाहू अन्हु) ने के आप','मेरा ख़याल है','qualified_transmitted_tabuk_return_purchase_variant','The source supplies the Tabuk-return purchase circumstance; the parenthetic return from expedition is material scope.'),
        comp('मेरा ख़याल है','अबू नज़रा ने जाबिर','unnamed_transmitter_material_price_uncertainty','The first-person transmitter is not named by this clause; retain the full uncertainty over the four-uqiya amount and the purchase predicate.'),
        comp('अबू नज़रा ने जाबिर','श\'बी के बयान के मुताबिक़','qualified_transmitted_twenty_dinar_purchase_variant','Abu Nadra relays the Jabir twenty-dinar purchase wording; the later compiler preference remains separate context.')],
      'ur':[
        comp('انہوں نے بیان کیا کہ مجھ سے جابر','شعبہ نے مغیرہ','companion_camel_encounter_and_conditional_sale_report','Amir frames Jabir own camel encounter, condition, payment and return; the source non-returned-price clause remains.'),
        comp('اور ان سے جابر رضی اللہ عنہ نے بیان کیا کہ رسول','اسحاق نے جریر','qualified_transmitted_riding_permission_variant','The source supplies Jabir riding-permission variant, without a newly asserted eyewitness event.'),
        comp('( جابر رضی اللہ عنہ نے فرمایا تھا )','عطاء وغیرہ نے بیان کیا','qualified_transmitted_sale_condition_variant','The source explicitly assigns the conditional first-person sale statement to Jabir.'),
        comp('عطاء وغیرہ نے بیان کیا','محمد بن منکدر','qualified_transmitted_prophetic_riding_statement','Ata and others relay the expressly attributed riding-to-Medina statement; no missing intermediate identity is supplied.'),
        comp('محمد بن منکدر','زید بن اسلم نے جابر رضی اللہ عنہ کے واسطہ','qualified_transmitted_sale_condition_variant','Muhammad ibn Munkadir relays the supplied Jabir riding condition.'),
        comp('زید بن اسلم نے جابر رضی اللہ عنہ کے واسطہ','ابوالزبیر نے جابر رضی اللہ عنہ سے بیان کیا','qualified_transmitted_prophetic_riding_statement','Zaid ibn Aslam relays the supplied Jabir version with the actual riding instruction.'),
        comp('ابوالزبیر نے جابر رضی اللہ عنہ سے بیان کیا','اعمش نے سالم سے بیان کیا','qualified_transmitted_riding_permission_variant','Abu al-Zubair relays the supplied Jabir permission wording.'),
        comp('اور ان سے جابر رضی اللہ عنہ نے کہ ( رسول','عبیداللہ اور ابن اسحاق','qualified_transmitted_prophetic_riding_statement','The final Jabir frame supplies the ride-home version; earlier Amas/Salim route stays context.'),
        comp('اور ان سے جابر رضی اللہ عنہ نے کہ اونٹ','اس روایت کی متابعت','qualified_transmitted_one_uqiya_purchase_variant','The final Jabir frame supplies a one-uqiya purchase version without asserting a separate sale.'),
        comp('اور ان سے جابر رضی اللہ عنہ نے ( کہ نبی','اس حساب سے','qualified_transmitted_four_dinar_purchase_statement','The printed Ibn Jurayj/Ata route leads to this Jabir four-dinar quotation; the differing Hindi route spelling is not harmonized.'),
        comp('اور انہوں نے جابر رضی اللہ عنہ سے اپنی روایت میں ایک اوقیہ','ابواسحاق نے سالم','qualified_transmitted_one_uqiya_gold_variant','The source supplies one uqiya of gold as an affirmative version detail, without choosing it over the other amounts.'),
        comp('اور انہوں نے جابر رضی اللہ عنہ سے اپنی روایت میں دو سو','اور داود بن قیس','qualified_transmitted_two_hundred_dirham_variant','The source supplies a two-hundred-dirham version with its printed Jabir attribution.'),
        comp('اور ان سے جابر رضی اللہ عنہ نے کہ آپ','میرا خیال ہے','qualified_transmitted_tabuk_return_purchase_variant','The source supplies the Tabuk-return purchase circumstance; the parenthetic return from expedition is material scope.'),
        comp('میرا خیال ہے','ابونضرہ نے جابر','unnamed_transmitter_material_price_uncertainty','The first-person transmitter is not named by this clause; retain the full uncertainty over the four-uqiya amount and the purchase predicate.'),
        comp('ابونضرہ نے جابر','شعبی کے بیان کے مطابق','qualified_transmitted_twenty_dinar_purchase_variant','Abu Nadra relays the Jabir twenty-dinar purchase wording; the later compiler preference remains separate context.')]},
    annotations={lang:'These are the exact source-supplied variants of one camel report family, including differing one-uqiya, four-dinar, gold, two-hundred-dirham, uncertain four-uqiya and twenty-dinar amounts. No amount or route is harmonized, no separate transaction is invented and the final compiler preference remains visible source context.' for lang in ('hi','ur')})

put('2719','companion_report_of_proposal_refusal_and_work_share_agreement',
    'Abu Hurayra reports the Ansar proposal, the supplied negative reply and the Ansar/Muhajirun exchange.',
    'Preserve the after-brotherhood circumstance and all work/fruit-sharing conditions and responses. The redundant recipient apposition and earlier pure route remain context; no completed transfer is invented.',
    start_at={'hi':'और उन से अबू हुरैरा','ur':'اور ان سے ابوہریرہ'},
    exclude_substrings={'hi':['(मुहाजिरीन)'],'ur':['( مہاجرین )']})
put('2720','companion_report_of_conditional_khaybar_cultivation_arrangement',
    'The source names the final reporter only Abdullah; he reports the actual arrangement.',
    'Keep the Jewish recipients, work/sowing conditions and half-yield share. The earlier route is context; no expanded Abdullah identity is inferred from Nafi or familiar content.',
    start_at={'hi':'और उन से अब्दुल्लाह','ur':'اور ان سے عبداللہ'},
    annotations={lang:'The own field names its reporter only Abdullah. The original source-local wording and name remain, without expanding it through another language or a remembered route.' for lang in ('hi','ur')})
put('2722','companion_cultivation_practice_and_reported_prohibition',
    'The final hearer reports Rafi ibn Khadij account; the prohibiting actor is not named in this field.',
    'Preserve both crop-result alternatives, their causal connection, the prohibition and the explicit non-prohibition of silver rent. The earlier multistep route and rupee example are context; no unprinted prohibiting speaker is assigned.',
    start_at={'hi':'उन्होंने कहा के मैंने राफ़े','ur':'انہوں نے کہا کہ میں نے رافع'},
    exclude_substrings={'hi':['(रुपये वग़ैरह)'],'ur':['( روپے وغیرہ )']},
    annotations={lang:'The source says that they were forbidden but does not name the agent of that prohibition. The report retains this attribution limit and the separate negative silver-rent clause.' for lang in ('hi','ur')})
put('2727','companion_report_of_qualified_prophetic_prohibitions',
    'Abu Hurayra relays the supplied prohibitions; the damaged Hindi join remains literal.',
    'Preserve every actual prohibition, the trade-caravan object and the religious-or-kin sister relation. The prefatory route and final corroboration/grammatical-form comparison remain complete context; no absent route, name or body is inserted into Hindi.',
    start_at={'hi':'अबू हुरैरह (रज़ियल्लाहु अन्हु) ने','ur':'اور ان سے ابوہریرہ'},
    stop_before={'hi':'मुहम्मद बिन आर\'आरः के साथ','ur':'محمد بن عرعرہ کے ساتھ'},
    annotations={'hi':'The Hindi has a shortened opening route and the stranded अलैहि वसल्लम) before the final prohibitions. Those exact source words remain without copying the fuller Urdu connection.',
                 'ur':'The final source paragraph compares transmission and grammatical formulas without supplying another substantive prohibition body; it remains complete source context.'})
put('2737','companion_endowment_report_and_separately_attributed_successor_reply',
    'Ibn Umar reports Umar consultation and endowment; Ibn Awn separately reports Ibn Sirin actual reply about intention.',
    'Keep the conditional advice, Umar actual stipulations, all beneficiaries and trustee limits, plus the finite named Ibn Sirin saying. Distinguish the three same-family components. The prefatory route and waqf word apposition are context; the final scholar statement is not Prophet speech.',
    exclude_substrings={'hi':['(वक़्फ़)'],'ur':['( وقف )']},shared_report_family=True,
    components={
      'hi':[comp('उन्हें इब्न-ए-उमर','इब्न-ए-उमर (रज़ियल्लाहु अन्हुमा) ने बयान किया','companion_report_of_consultation_and_conditional_reply','Ibn Umar reports Umar consultation and the actual conditional reply.'),
            comp('इब्न-ए-उमर (रज़ियल्लाहु अन्हुमा) ने बयान किया','इब्न-ए-औन ने बयान किया','companion_actual_endowment_stipulations','Ibn Umar reports Umar endowment, beneficiaries and trustee conditions.'),
            comp('इब्न-ए-औन ने बयान किया',None,'named_successor_reply_in_actual_encounter','Ibn Awn reports his own mention to Ibn Sirin and Ibn Sirin actual no-accumulation-intention reply, with the trustee subject retained.')],
      'ur':[comp('انہیں ابن عمر','ابن عمر رضی اللہ عنہما نے بیان کیا','companion_report_of_consultation_and_conditional_reply','Ibn Umar reports Umar consultation and the actual conditional reply.'),
            comp('ابن عمر رضی اللہ عنہما نے بیان کیا','ابن عون نے بیان کیا','companion_actual_endowment_stipulations','Ibn Umar reports Umar endowment, beneficiaries and trustee conditions.'),
            comp('ابن عون نے بیان کیا',None,'named_successor_reply_in_actual_encounter','Ibn Awn reports his own mention to Ibn Sirin and Ibn Sirin actual no-accumulation-intention reply, with the trustee subject retained.')]})

put('2739','companion_report_of_remaining_property',
    'Amr ibn Harith reports the supplied death/property account.',
    'Preserve the actual exceptions, every negation and the dedicated-land statement. Earlier transmission and appended static kinship biography remain complete context; no other asset or externally verified biography is added.',
    start_at={'hi':'अम्र बिन हारिस (रज़ियल्लाहु अन्हु) ने','ur':'عمرو بن حارث رضی اللہ عنہ نے'},
    exclude_between={'hi':[('जो जुवैरियह बिंत हारिस','बयान किया के रसूल')],
                     'ur':[('جو جویریہ بنت حارث','بیان کیا کہ رسول')]})
put('2741','companion_report_of_aisha_reply_with_visible_wording_uncertainty',
    'Aswad reports the unnamed people claim and Aisha actual challenge/account; the chest-or-lap alternative is retained as source transmission uncertainty.',
    'Keep the disputed claim as attributed speech, Aisha response, both chest/lap alternatives and the explicit or-she-said qualification. The Prophet relation, water object and head subject are necessary source scope. Only the prefatory route and redundant instead-of-chest word-comparison explanation are context; no doctrinal conclusion is asserted.',
    start_at={'hi':'उन से असवद बिन यज़ीद','ur':'ان سے اسود بن یزید'},
    exclude_substrings={'hi':['(बजाये सीने के)'],'ur':['( بجائے سینے کے )']},
    annotations={lang:'The source visibly leaves chest/lap wording uncertain. Both alternatives and the explicit transmission qualification remain; no settled wording or verified appointment claim is supplied.' for lang in ('hi','ur')})
put('2742','companion_illness_will_dialogue_and_separate_family_circumstance',
    'Saad ibn Abi Waqqas gives the encounter and reply; the terminal one-daughter fact has an unspecified source narrative voice.',
    'Preserve the Hajj/Mecca setting, all proposed shares and negatives, actual conditions and source-supplied expenditure/temporal/recipient qualifiers. The alternative-name apposition and prior route are context. The final daughter clause is a separate same-family narrative fragment, not further Prophet speech; this classification does not certify a legal conclusion.',
    start_at={'hi':'और उन से साद बिन अबी वक़्क़ास','ur':'اور ان سے سعد بن ابی وقاص'},
    exclude_substrings={'hi':['(साद बिन ख़वला रज़ियल्लाहु अन्हु)'],'ur':['( سعد بن خولہ رضی اللہ عنہ )']},shared_report_family=True,
    components={
      'hi':[comp(None,'उस वक़्त साद','companion_illness_and_conditional_prophetic_dialogue','Saad reports the actual visit, will questions and source-rendered replies with all printed qualifications.'),
            comp('उस वक़्त साद',None,'source_narrative_family_circumstance','The terminal source sentence states that Saad then had one daughter; its transmitting voice is not independently named.')],
      'ur':[comp(None,'اس وقت سعد','companion_illness_and_conditional_prophetic_dialogue','Saad reports the actual visit, will questions and source-rendered replies with all printed qualifications.'),
            comp('اس وقت سعد',None,'source_narrative_family_circumstance','The terminal source sentence states that Saad then had one daughter; its transmitting voice is not independently named.')]},
    annotations={lang:'The source places meaningful parenthetic predicates and temporal/recipient qualifications within its rendered reply. They remain source wording, without independently certifying reconstructed verbatim speech. The final one-daughter clause is kept separately from that reply.' for lang in ('hi','ur')})
put('2744','qualified_illness_dialogue_and_reported_later_will_practice',
    'The Hindi first-person patient is not named by its damaged route; Urdu explicitly names Saad. The final practice clause has an unspecified source voice.',
    'Retain the complete own illness/will dialogue, offspring domain, much-or-large alternative and finite later-practice account. The death-in-Mecca interpretation, equivalent-formula parenthesis and amount noun gloss remain context. No missing Hindi patient name or body is copied from Urdu.',
    exclude_substrings={'hi':['(यानि मक्काः में मेरी मौत न हो)','(ये फ़रमाया की)','(रक़म)'],
                        'ur':['( یعنی مکہ میں میری موت نہ ہو )','( یہ فرمایا کہ )','( رقم )']},shared_report_family=True,
    components={
      'hi':[comp('मैं मक्काः में बीमार','चुनांचे लोग भी','qualified_first_person_illness_and_prophetic_reply','The Hindi supplies an actual first-person illness account but omits the patient attribution link; do not assign Hashim or borrow Saad from Urdu.'),
            comp('चुनांचे लोग भी',None,'source_report_of_later_will_practice','The source separately states the later one-third will practice and its claimed permission; the transmitting speaker is not named.')],
      'ur':[comp('اور ان سے ان کے باپ سعد بن ابی وقاص','چنانچہ لوگ بھی','companion_first_person_illness_and_prophetic_reply','The Urdu explicitly attributes the first-person illness and will dialogue to Saad ibn Abi Waqqas.'),
            comp('چنانچہ لوگ بھی',None,'source_report_of_later_will_practice','The source separately states the later one-third will practice and its claimed permission; the transmitting speaker is not named.')]},
    annotations={'hi':'The Hindi route ends with Hashim ibn Hashim and omits the link naming the first-person patient. The patient remains explicitly unidentified; the original damaged spelling and one-third wording are not repaired.',
                 'ur':'The Urdu independently supplies the named patient and fuller route. It establishes only its own field and is not used to complete the Hindi.'})
put('2746','qualified_historical_injury_complaint_and_order_report',
    'Urdu names Anas as reporter; the shortened Hindi route leaves its final reporting link unresolved.',
    'Keep the Ansari participant scope, all actual naming/questions, the relative clause identifying the attacker, signal, confession and reported order. Earlier pure routes remain context. The Hindi final reporter is not invented from the Urdu, and no external fact or legal rule is asserted.',
    start_at={'hi':'एक यहूदी ने एक','ur':'اور ان سے انس رضی اللہ عنہ'},
    annotations={'hi':'The source begins with Hassan ibn Abi Ibad but its final transmission link is missing. Hassan is not labelled an eyewitness and no Anas identity is copied from the Urdu; the supplied finite report remains qualified.',
                 'ur':'The Urdu has its own explicit Anas reporter frame. Its named attribution is retained without repairing the shorter Hindi sibling.'})
put('2747','qualified_historical_inheritance_statement',
    'Urdu explicitly attributes the statement to Ibn Abbas; the damaged Hindi final attribution remains unidentified.',
    'Preserve the actual historical/interpretive statement, the inheritance-property domain, all printed fractions and every child-presence/absence condition. The Hindi missing male-share clause and damaged husband word remain unfilled; no source words or legal conclusion are supplied from another language.',
    start_at={'hi':'शुरू इस्लाम में','ur':'اور ان سے ابن عباس'},
    annotations={'hi':'The saved Hindi omits the final Ibn Abbas attribution and part of the male/two-female clause, and prints शहर in the later fraction clause. All these defects remain literal; no speaker or missing text is reconstructed.',
                 'ur':'This own Urdu field names Ibn Abbas and includes the fuller male/female share clause. These words are retained only in Urdu, not used to reconstruct the Hindi.'})
put('2748','companion_report_of_charity_question_and_qualified_reply',
    'Abu Hurayra reports the unnamed Companion question and the supplied reply.',
    'Keep the actual wealth-retention motive, spending-related fear condition, health/death contrast and final death predicate. These parentheses supply narrative scope or finite content, not removable word synonyms. The earlier route is context; no questioner identity or modern legal instruction is added.',
    start_at={'hi':'और उन से अबू हुरैराह','ur':'اور ان سے ابوہریرہ'})

put('2756','companion_report_of_charity_question_and_named_garden_declaration',
    'Ibn Abbas reports Saad ibn Ubada question, the actual reply and Saad declaration.',
    'Preserve the absence-at-death circumstance, the own mother/garden names, conditional question, affirmative reply and witnessed declaration. The preceding multistep route is context; no external identity or later completion is inferred.',
    start_at={'hi':'वो बयान करते थे के हमें इब्न अब्बास','ur':'وہ بیان کرتے تھے کہ ہمیں ابن عباس'})
put('2757','companion_repentance_proposal_and_qualified_reply',
    'Abdullah ibn Kaab reports hearing Kaab ibn Malik own proposal and replies.',
    'Keep the actual Tabuk nonattendance circumstance, keep-some condition and Khaybar-share decision. This is a supplied dialogue, not proof that every proposed transfer occurred. The earlier route is context.',
    start_at={'hi':'और उन से अब्दुल्लाह बिन काअब','ur':'اور ان سے عبداللہ بن کعب'})
put('2759','companion_attributed_exegesis_and_illustrative_saying',
    'Ibn Abbas gives the no-abrogation oath, two-category account and illustrative gentle answer.',
    'Preserve the entire actual attributed interpretation and its quoted example. The pointer to the heading and earlier route remain context; no missing verse text/number or direct Prophet attribution is supplied.',
    start_at={'hi':'और उन से इब्न अब्बास','ur':'اور ان سے ابن عباس'},
    exclude_substrings={'hi':['(जिसका ज़िक्र उनवान में हुआ)'],'ur':['( جس ذکر عنوان میں ہوا )']})
put('2760','companion_report_of_speculative_charity_question_and_reply',
    'Aisha reports the participant whom this source parenthesis names Saad ibn Ubada, his qualified question and the actual reply.',
    'Preserve the otherwise unnamed participant identifier as source wording, the sudden-death setting and the full I-think/if-she-could-speak uncertainty. The earlier route is context; no completed charity or adjacent garden detail is inserted.',
    start_at={'hi':'और उन से आयशा','ur':'اور ان سے عائشہ'},
    annotations={lang:'The source parenthesis names the otherwise unnamed questioner. That source identification is preserved without external verification; the speculative statement about what his mother would have done remains explicitly qualified.' for lang in ('hi','ur')})
put('2763','companion_exegesis_revelation_report_and_distinct_narrator_interpretation',
    'Urwah reports his question and Aisha interpretation; Aisha separately reports the further question/revelation; a final expressly designated but unnamed narrator gives the last interpretive statement.',
    'Keep both supplied verse excerpts and renderings as subjects of interpretation, the actual attributed historical statement and every conditional/actor/family scope. Four same-family components distinguish Aisha from the final unnamed narrator. The pure earlier route is context; no recitation event, verse completion or modern legal ruling is invented.',
    start_at={'hi':'के उरवह बिन ज़ुबैर','ur':'کہ عروہ بن زبیر'},shared_report_family=True,
    components={
      'hi':[comp(None,'आयशा (रज़ियल्लाहु अन्हा) ने बयान किया के फिर लोगों','companion_question_and_attributed_exegesis','Urwah asks Aisha about the printed verse and she supplies the first interpretation.'),
            comp('आयशा (रज़ियल्लाहु अन्हा) ने बयान किया के फिर लोगों','आयशा (रज़ियल्लाहु अन्हा) ने कहा के फिर अल्लाह','companion_report_of_further_question_and_revelation','Aisha reports the further question and the source-supplied revelation excerpt; no recitation event is asserted.'),
            comp('आयशा (रज़ियल्लाहु अन्हा) ने कहा के फिर अल्लाह','रावी ने कहा','companion_further_attributed_exegesis','Aisha gives the supplied guardian/wealth/beauty and full-dower interpretation with its conditions.'),
            comp('रावी ने कहा',None,'explicitly_attributed_unnamed_narrator_interpretation','The source expressly says the narrator said this final comparison; that narrator is unnamed and is not relabelled as Aisha or the Prophet.')],
      'ur':[comp(None,'عائشہ رضی اللہ عنہا نے بیان کیا کہ پھر لوگوں','companion_question_and_attributed_exegesis','Urwah asks Aisha about the printed verse and she supplies the first interpretation.'),
            comp('عائشہ رضی اللہ عنہا نے بیان کیا کہ پھر لوگوں','عائشہ رضی اللہ عنہا نے کہا کہ پھر اللہ','companion_report_of_further_question_and_revelation','Aisha reports the further question and the source-supplied revelation excerpt; no recitation event is asserted.'),
            comp('عائشہ رضی اللہ عنہا نے کہا کہ پھر اللہ','راوی نے کہا','companion_further_attributed_exegesis','Aisha gives the supplied guardian/wealth/beauty and full-dower interpretation with its conditions.'),
            comp('راوی نے کہا',None,'explicitly_attributed_unnamed_narrator_interpretation','The source expressly says the narrator said this final comparison; that narrator is unnamed and is not relabelled as Aisha or the Prophet.')]},
    annotations={lang:'The final narrator-said comparison is retained as an expressly attributed anonymous interpretive statement, separate from Aisha and from Prophet speech. The source does not identify that narrator. Actual verse words/renderings and necessary conditional predicates remain literal.' for lang in ('hi','ur')})
put('2765','companion_attributed_interpretation_of_supplied_verse',
    'Aisha supplies the interpretation of the exact printed verse and rendering.',
    'Preserve the actual quotation/rendering as the interpretation subject and every wealth/poverty/customary-use condition. The generic verse-introduction parenthesis and prior route are context. No recitation event, repaired Arabic word or legal conclusion is added.',
    start_at={'hi':'और उनसे आयशा','ur':'اور ان سے عائشہ'},
    exclude_substrings={'hi':['(क़ुरआन मजीद की इस आयत)'],'ur':['( قرآن مجید کی اس آیت )']},
    annotations={'ur':'The supplied Arabic excerpt ends بالمعرو without its expected final letter. The source is retained literally and is not completed from another field or memory.',
                 'hi':'The whole actual Hindi verse rendering and the source transliteration remain; no Arabic or verse locator is inserted.'})
put('2767','distinct_historical_practice_reports_recitation_and_attributed_saying',
    'Nafi reports Ibn Umar practice; the source separately describes Ibn Sirin practice and Tawus recitation; Ata supplies his own saying.',
    'Keep four distinct supplied report families under their actual subjects and qualified voices. The prefatory compiler/transmission route is context. The actual Tawus recitation and rendering remain, and the final status-qualified expenditure advice is Ata saying, not direct Prophet speech or a newly established legal ruling.',
    components={
      'hi':[comp('उनसे नाफ़े ने बयान किया','इब्न सीरीन ताबेई','named_transmitter_report_of_companion_practice','Nafi reports Ibn Umar not refusing executorship.'),
            comp('इब्न सीरीन ताबेई','ताऊस ताबेई','source_historical_report_of_named_scholar_practice','The source describes Ibn Sirin consultation practice; no unprinted transmitting identity is invented.'),
            comp('ताऊस ताबेई','अता (रहिमहुल्लाह) ने','source_report_of_named_scholar_actual_recitation','The source explicitly describes Tawus reciting the printed verse when asked; the recitation event and full rendering are retained.'),
            comp('अता (रहिमहुल्लाह) ने',None,'named_successor_qualified_saying','Ata gives the supplied status-qualified orphan-expenditure saying.')],
      'ur':[comp('ان سے نافع نے بیان کیا','ابن سیرین تابعی','named_transmitter_report_of_companion_practice','Nafi reports Ibn Umar not refusing executorship.'),
            comp('ابن سیرین تابعی','طاؤس تابعی','source_historical_report_of_named_scholar_practice','The source describes Ibn Sirin consultation practice; no unprinted transmitting identity is invented.'),
            comp('طاؤس تابعی','عطاء رحمہ اللہ نے','source_report_of_named_scholar_actual_recitation','The source explicitly describes Tawus reciting the printed verse when asked; the recitation event and full rendering are retained.'),
            comp('عطاء رحمہ اللہ نے',None,'named_successor_qualified_saying','Ata gives the supplied status-qualified orphan-expenditure saying.')]},
    annotations={lang:'Four supplied pieces remain four separate report families. The middle historical-practice reporters are not independently named; the named subjects are not relabelled as eyewitness narrators or Prophet speakers.' for lang in ('hi','ur')})
put('2770','companion_report_of_charity_question_and_unnamed_garden_declaration',
    'Ibn Abbas reports the supplied question, affirmative reply and garden declaration.',
    'Keep the own source participant spelling and all actual declarations. This field names no garden, so no name is imported from2756. The shortened/duplicated Hindi route remains literal context.',
    start_at={'hi':'और उन्हों ने इब्न अब्बास','ur':'اور انہوں نے ابن عباس'},
    annotations={'hi':'The Hindi source prints सा\'डी/उबड़ाह and a damaged prefatory route. These original words remain unnormalized; the garden remains unnamed.',
                 'ur':'The own Urdu supplies Saad ibn Ubada but no garden name. Its fuller route does not repair the Hindi sibling.'})
put('2771','companion_report_of_mosque_command_and_garden_exchange',
    'Anas reports the mosque command, the Banu Najjar valuation request and their sworn reply.',
    'Keep the Medina location, actual request and negative oath/reply. Earlier multistep route remains context; no completed sale or endowment beyond the supplied dialogue is invented.',
    start_at={'hi':'और उनसे अनस','ur':'اور ان سے انس'})

put('2773','companion_report_of_umar_conditional_charity_and_actual_gift',
    'Ibn Umar reports Umar Khaybar property, the conditional reply and Umar charity.',
    'Arabic and English independently supply finite reports; all three other fields are duplicated chains with no body and remain reviewed source context. Preserve the condition, four beneficiary groups and yield clause, excluding only the earlier Arabic route and English endowment definition. No missing translation is supplied.',
    languages=['ar','en'],
    start_at={'ar':'عَنِ ابْنِ عُمَرَ'},
    exclude_substrings={'en':['(i.e. as an endowment)']},
    annotations={lang:'The Hindi, Urdu and Roman Urdu siblings each repeat a transmission chain and stop before the report body. The Arabic and English reports establish only their own languages; no content is copied into the incomplete siblings.' for lang in ('ar','hi','ur','ur-Latn','en')})
put('2774','companion_report_of_medina_mosque_command_and_garden_exchange',
    'Anas ibn Malik reports the Medina arrival, mosque command and Banu Najjar exchange.',
    'Only the independently read Arabic and English contain a supplied report. Hindi, Urdu and Roman Urdu have duplicated bare routes and remain reviewed context. Keep the arrival, request and sworn reply without inventing a completed conveyance or missing closing quotation.',
    languages=['ar','en'],
    start_at={'ar':'قَالَ حَدَّثَنِي أَنَسُ بْنُ مَالِكٍ'},
    annotations={lang:'The three incomplete Hindi/Urdu/Roman fields remain exact duplicated chains. The English ends without a closing quote; no punctuation or body is repaired. This source ID stays separate from2771.' for lang in ('ar','hi','ur','ur-Latn','en')})
put('2777','companion_report_of_umar_endowment_stipulation',
    'Ibn Umar reports Umar actual trustee-use condition; Umar is the stipulator, not the reporting Ibn Umar.',
    'Preserve both permitted uses and the no-accumulation limit as the supplied Companion stipulation. The pure earlier route is context; this is not direct Prophet speech.',
    start_at={'hi':'और उन से अब्दुल्लाह बिन उमर','ur':'اور ان سے عبداللہ بن عمر'})
put('2780','companion_historical_dispute_report_and_attributed_revelation_interpretation',
    'Ibn Abbas reports the journey/property/testimony dispute and separately states the supplied revelation connection.',
    'Preserve the finite swearing clause, original participant identifiers, competing testimony and actually printed verse excerpt. The earlier compiler/multistep route and terminal end-of-verse pointer are context. Do not treat malformed Urdu parentheses as a reason to omit the entire resumed story, invent a completed verse or externally certify the source identities.',
    start_at={'hi':'कहा हम से अब्दुल्लाह बिन अब्बास','ur':'کہا ہم سے عبداللہ بن عباس'},
    stop_before={'hi':'आख़िर आयत तक','ur':'آخر آیت تک'},shared_report_family=True,
    components={
      'hi':[comp(None,'अब्दुल्लाह बिन अब्बास (रदी अल्लाहु अन्हुमा) ने कहा इन ही','companion_report_of_historical_property_and_testimony_dispute','Ibn Abbas reports the supplied events and competing sworn claims; these remain attributed assertions.'),
            comp('अब्दुल्लाह बिन अब्बास (रदी अल्लाहु अन्हुमा) ने कहा इन ही',None,'companion_attributed_revelation_interpretation','Ibn Abbas expressly connects the printed verse excerpt with these parties; no separate recitation event or missing verse text is inserted.')],
      'ur':[comp(None,'عبداللہ بن عباس رضی اللہ عنہما نے کہا ان ہی','companion_report_of_historical_property_and_testimony_dispute','Ibn Abbas reports the supplied events and competing sworn claims; these remain attributed assertions.'),
            comp('عبداللہ بن عباس رضی اللہ عنہما نے کہا ان ہی',None,'companion_attributed_revelation_interpretation','Ibn Abbas expressly connects the printed verse excerpt with these parties; no separate recitation event or missing verse text is inserted.')]},
    annotations={'hi':'The two relatives are named only by the supplied parenthesis. Those names remain source-qualified identifiers, without external verification. The actual they-swore clause and the quoted verse subject remain.',
                 'ur':'The source opens a parenthesis at the two relatives names and closes it only after the terminal verse pointer. The finite acts, claims and Ibn Abbas interpretation inside it are retained; the malformed original punctuation remains visible in the complete partition.'})
put('2784','companion_womens_question_and_qualified_prophetic_reply',
    'Aisha asks the source question on behalf of the expressly specified women; the supplied reply concerns accepted Hajj.',
    'Keep the women participant domain and every actual qualification of the reply. The earlier route and appended mother-of-believers title remain context; no broader question or independent legal ruling is inferred.',
    start_at={'hi':'और उन से आयशा (रदी अल्लाहु अन्हा)','ur':'اور ان سے عائشہ رضی اللہ عنہا'},
    exclude_substrings={'hi':['(उम्म-उल-मोमिनीन)'],'ur':['( ام المؤمنین )']})

# These are filled by the separate literal inventory pass after checking every
# already-read selected parenthesis; they never approve an unread field.
RETAINED_HONORIFICS={
 '(peace and blessings of Allah be upon him)',
 '(रज़ियल्लाहु अन्हा)','(रज़ियल्लाहु अन्हु)','(रज़ियल्लाहु अन्हुमा)',
 '(रदी अल्लाहु अन्हा)','(रदी अल्लाहु अन्हु)','(रदी अल्लाहु अन्हुमा)',
 '(रदी अल्लाहू अन्हु)','(रदी अल्लाहू अन्हुमा)','(रहिमहुल्लाह)',
 '(रिदवानुल्लाहि अलैहिम)','(सल्लल्लाहु अलैहि वसल्लम)',
}
RETAINED_NONHONORIFIC={}
RETAINED_MARKER_WORDS={}
def retain(number,hi,ur,reason):
    for language,literal in (('hi',hi),('ur',ur)):
        if literal:RETAINED_NONHONORIFIC[('bukhari:'+str(number),language,literal)]=reason
retain('2709','(इस साल की खजूर के)','( اس سال کی کھجور کے )','This is the actual year/crop domain of the offered repayment fruit.')
retain('2709','(तो मुझे ख़बर दो)','( تو مجھے خبر دو )','The supplied imperative tells Jabir to notify the speaker; removing it deletes a finite command.')
retain('2709','(जाबिर (रदी अल्लाहू अन्हु) की हाज़री का)','( جابر رضی اللہ عنہ کی حاضری کا )','This supplies the actual attendance event to which the abbreviated Asr variant refers.')
retain('2709','(जाबिर (रदी अल्लाहू अन्हु) ने कहा)','( جابر رضی اللہ عنہ نے کہا )','The source supplies the speaker and said predicate of the first-person debt-amount addition.')
retain('2718','(एक ग़ज़वा के मौक़े पर)','( ایک غزوہ کے موقع پر )','The expedition occasion is a supplied historical setting of the ride.')
retain('2718','(मदीना)','( مدینہ )','This is the location reached in the actual arrival clause.')
retain('2718','(मैं हाज़िर हुआ तो)','( میں حاضر ہوا تو )','This is a finite first-person attendance condition linking the call to the ensuing reply.')
retain('2718','(और क़ीमत वापस नहीं ली)','( اور قیمت واپس نہیں لی )','The explicit price-not-reclaimed fact prevents the camel-return passage from implying rescission.')
retain('2718','(जाबिर (रदी अल्लाहू अन्हु) ने फ़रमाया था)','( جابر رضی اللہ عنہ نے فرمایا تھا )','This supplies the actual first-person variant speaker and attribution predicate.')
retain('2718','(रसूल अल्लाह (सल्लल्लाहु अलैहि वसल्लम) ने फ़रमाया था)','( رسول اللہ صلی اللہ علیہ وسلم نے فرمایا تھا )','This is the source attribution and finite speech predicate of the appended riding statement.')
retain('2718','(रसूल अल्लाह (सल्लल्लाहु अलैहि वसल्लम) ने फ़रमाया)','( رسول اللہ صلی اللہ علیہ وسلم نے فرمایا )','This supplies the speaker/predicate of the ride-home quotation.')
retain('2718','(के नबी करीम (सल्लल्लाहु अलैहि वसल्लम) ने फ़रमाया था)','( کہ نبی کریم صلی اللہ علیہ وسلم نے فرمایا تھا )','This supplies the actual attribution of the four-dinar purchase quotation.')
retain('2718','(ग़ज़वा से वापस होते हुए)','( غزوہ سے واپس ہوتے ہوئے )','The return-from-expedition circumstance limits the Tabuk purchase version.')
retain('2718','(ख़रीदा था)','( خریدا تھا )','This is the actual purchase predicate of the uncertain four-uqiya statement.')
retain('2719','(मुआख़ात के बाद)','( مؤاخات کے بعد )','The after-brotherhood time relation is the supplied occasion of the proposal.')
retain('2727','(तिजारती काफिलों की)','( تجارتی قافلوں کی )','The trade-caravan object limits the otherwise unspecified meeting/interception prohibition.')
retain('2727','(दीनी या नसबी)','( دینی یا نسبی )','The religious-or-kin relation supplies the actual scope of sister.')
retain('2737','(मुतवल्ली)','( متولی )','This identifies the subject of Ibn Sirin no-accumulation-intention saying.')
retain('2741','(नबी करीम (सल्लल्लाहु अलैहि वसल्लम) के)','( نبی کریم صلی اللہ علیہ وسلم کے )','This supplies whose executor is meant in the attributed disputed claim.')
retain('2741','(पानी का)','( پانی کا )','The water object is part of the supplied basin request.')
retain('2741','(सर-ए-मुबारक)','( سر مبارک )','This supplies the actual subject that inclined into the lap.')
retain('2742','(हज्जतुल विदा में)','( حجۃ الوداع میں )','This names the actual historical visit occasion, not a source locator.')
retain('2742','(अल्लाह के लिए ख़र्च करोगे)','( اللہ کے لیے خرچ کرو گے )','This is the spending condition and predicate in the source-rendered reply.')
retain('2742','(वो भी ख़ैरात है)','( وہ بھی خیرات ہے )','This is the finite supplied consequence about the morsel, not a dictionary synonym.')
retain('2742','(अभी वसीयत करने की कोई ज़रूरत भी नहीं)','( ابھی وصیت کرنے کی کوئی ضرورت بھی نہیں )','The source supplies this time-qualified clause within its rendered reply; preserving it does not independently certify reconstructed verbatim speech.')
retain('2742','(इस्लाम के मुखालिफ़)','( اسلام کے مخالف )','This limits the source recipients of the predicted harm.')
retain('2744','(औलाद)','( اولاد )','This supplies the offspring domain of the otherwise absolute no-other-person claim.')
retain('2746','(अंसारी)','( انصاری )','This is the actual participant affiliation supplied for the girl.')
retain('2746','(जिस ने इस का सर कुचल दिया था)','( جس نے اس کا سر کچل دیا تھا )','This finite relative clause identifies the proposed person as the actor in the reported injury.')
retain('2747','(मीरास का)','( میراث کا )','The inheritance domain limits the property discussed.')
retain('2747','(औलाद की मौजूदगी में)','( اولاد کی موجودگی میں )','The presence-of-children condition limits the stated fraction.')
retain('2747','(औलाद के न होने की सूरत में)','( اولاد کے نہ ہونے کی صورت میں )','The absence-of-children condition limits the stated fraction.')
retain('2747','(औलाद न होने की सूरत में)','( اولاد نہ ہونے کی صورت میں )','This separate absence-of-children condition limits the later half share.')
retain('2747','(औलाद होने की सूरत में)','( اولاد ہونے کی صورت میں )','This presence-of-children condition limits the later quarter share.')
retain('2748','(तुझ को इस माल को बाक़ी रखने की)','( تجھ کو اس مال کو باقی رکھنے کی )','This specifies the object/motive of the stated desire.')
retain('2748','(उसे ख़र्च करने की सूरत में)','( اسے خرچ کرنے کی صورت میں )','The spending condition limits the anticipated poverty fear.')
retain('2748','(तो तू दुनिया से चला)','( تو تو دنیا سے چلا )','This is the source finite death-stage predicate.')
retain('2757','(ग़ज़वा-ए-तबूक में न जाने की)','( غزوہ تبوک میں نہ جانے کی )','This specifies the actual nonattendance circumstance of the repentance, not a chapter locator.')
retain('2760','(साद बिन उबादह)','( سعد بن عبادہ )','The source supplies an otherwise unnamed questioner identity; it remains explicitly source-qualified, not externally verified.')
retain('2763','(और अगर तुम डरो के यतीमों के हक़ में इंसाफ़ नहीं करोगे तो औरतों में से जो तुम्हें पसंद हों उनसे निकाह करलो)',None,'This is the actual full supplied verse rendering that forms the interpretation subject.')
retain('2763','(तो निकाह कर सकते हैं)','( تو نکاح کر سکتے ہیں )','This is the conditional consequence in the attributed interpretation.')
retain('2763','(आप से लोग औरतों के मुताल्लिक़ पूछते हैं, आप कह दें के अल्लाह तुम्हें उनके बारे में हिदायत करता है)',None,'This is the actual full rendering of the second supplied verse excerpt.')
retain('2763','(उनके वली)','( ان کے ولی )','This identifies the actual guardians as the actors in the stated proposal.')
retain('2763','(खानदान के)','( خاندان کے )','The family norm domain limits the dower comparison.')
retain('2763','(वो उनसे निकाह मत करें)','( وہ ان سے نکاح مت کریں )','This is the actual negative consequence of the source conditional interpretation.')
retain('2763',None,'( اور )','The Urdu rendering specifies other women, preserving the source contrast without importing it into Hindi.')
retain('2765','(और जो शख़्स मालदार हो वो अपने को यतीम के माल से बिल्कुल रोके रखे, अलबत्ता जो शख़्स नादार हो तो वो दस्तूर के मुताबिक़ खा सकता है)',None,'This is the complete source rendering of the actually quoted verse, not a reference label.')
retain('2767','(और अल्लाह फ़साद पैदा करने वाले और संवारने वाले को ख़ूब जानता है)',None,'This is the supplied translation of the verse explicitly reported as recited by Tawus.')
retain('2771','(मदीना में)','( مدینہ میں )','This is the only supplied location of the commanded mosque building.')
retain('2780','(उन्होंने क़सम खा ली)','( انہوں نے قسم کھا لی )','This is the finite supplied swearing act following the order, not an explanatory word gloss.')
retain('2780','(अम्र बिन अल-आस और मतलब)',None,'These are the source identifiers of the otherwise unnamed two relatives; they are retained as supplied, without external identity verification.')
retain('2784','(औरतें)','( عورتیں )','This limits the collective question to the women explicitly designated in the source.')
for number in ('2709','2747','2748','2763','2767'):
    RETAINED_MARKER_WORDS[('bukhari:'+number,'hi','सूरत')]='This actually read word means proposal, circumstance or situation in its sentence. It is not a Surah or verse locator, and the actual source clause is retained.'
