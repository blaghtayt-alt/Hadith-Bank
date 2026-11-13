"""Explicit decisions after reading all42 complete saved Hindi/Urdu fields."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CHECKPOINT='0639af7fd15786284b4c413fced77e38eec8825a'
NOTES={r['key']:r for r in json.loads((ROOT/'source-first-notes.json').read_bytes())}
records=[]

def cut(text,reason,count=1):return {'text':text,'expected_count':count,'reason':reason}
def part(start,end,component,kind,speaker,family):return {'from':start,'to':end,'component_id':component,'report_type':kind,'speaker':speaker,'source_report_family_id':family}
def field(key,lang,speaker,kind='prophetic_report',end=None,cuts=(),parts=None):
    return {'action':'excerpt','reason':NOTES[key]['finding']+' This decision binds only the complete own '+lang+' field.',
            'spans':parts or [part(None,end,'reported-account',kind,speaker,key+':'+lang+':reported-account')],
            'omit_source_context':list(cuts)}
def add(key,hi,ur):records.append({'key':key,'decision':'register','reason':NOTES[key]['finding'],'fields':{'hi':hi,'ur':ur}})

for n in ('2221','2222'):
    k='abudawud:'+n
    add(k,field(k,'hi','Ikrima transmits the unnamed man and the explicitly named Prophet; no omitted intermediary is supplied.'),
          field(k,'ur','Ikrima transmits the unnamed man and the explicitly named Prophet; no omitted intermediary is supplied.'))
k='abudawud:2232'
add(k,field(k,'hi','Ibn Abbas reports Barira, Mughith and the explicitly named Prophet; the printed choice/iddah conditions remain.'),
      field(k,'ur','Ibn Abbas reports Barira, Mughith and the explicitly named Prophet; the printed choice/iddah conditions remain.'))
k='abudawud:2233'
add(k,field(k,'hi','Aisha reports Barira; the initial deciding actor is represented by an honorific without the omitted explicit name, which is not filled.','companion_report_with_source_attribution_defect'),
      field(k,'ur','Aisha reports the explicitly named Messenger and Barira; source temporal and actor qualifications remain.'))
k='abudawud:2234'
add(k,field(k,'hi','Aisha transmits the Messenger granting Barira a choice; Hindi ends here.'),field(k,'ur','Aisha transmits the Messenger granting Barira a choice and the printed statement that her husband was a slave.'))
k='abudawud:2236'
add(k,field(k,'hi','Aisha transmits the Messenger granting Barira a choice and its intercourse condition.'),field(k,'ur','Aisha transmits the Messenger granting Barira a choice and its intercourse condition.'))
k='abudawud:2243'
add(k,field(k,'hi','Firuz asks the explicitly addressed Messenger about his two wives who are sisters; the Messenger replies.'),field(k,'ur','Firuz asks the explicitly addressed Messenger about his two wives who are sisters; the Messenger replies.'))
k='abudawud:2251'
add(k,field(k,'hi','Per individually attributed component.',parts=[
 part(None,'यहाँ मुसद्दद की रिवायत पूरी हो गई','sahl-observation','companion_eyewitness_report','Sahl ibn Sad recounts his presence at age fifteen and the Messenger separating the li-an pair.',k+':hi:li-an-episode'),
 part('दीगर लोगों की रिवायत में है के:','अबू दाऊद कहते हैं के सुफ़यान','other-transmitted-wording','transmitted_narration_variant','The source explicitly gives other transmitted wording of Sahl’s episode, including the husband’s statement; no unnamed transmitter is identified.',k+':hi:li-an-episode')]),
 field(k,'ur','Per individually attributed component.',parts=[
 part(None,'یہاں مسدد کی روایت پوری ہو گئی','sahl-observation','companion_eyewitness_report','Sahl ibn Sad recounts his presence at age fifteen and the Messenger separating the li-an pair.',k+':ur:li-an-episode'),
 part('دیگر لوگوں کی روایت میں ہے کہ:','ابوداؤد کہتے ہیں کہ سفیان','other-transmitted-wording','transmitted_narration_variant','The source explicitly gives other transmitted wording of Sahl’s episode, including the husband’s statement; no unnamed transmitter is identified.',k+':ur:li-an-episode')]))
k='abudawud:2253'
add(k,field(k,'hi','Ibn Masud reports the unnamed Ansari and the Messenger. The Hindi ellipsis and abbreviated event sequence remain unfilled.'),
 field(k,'ur','Ibn Masud reports the unnamed Ansari, the Messenger, the li-an pair and the actually printed recitation/translation.',cuts=[
 cut('( حقیقت حال )','Lexical specification of what is stated, retained as source explanation rather than an additional narrated act.'),
 cut('( تہمت کی حد کے طور پر )','Translator/legal explanation of the punishment category.'),
 cut('( سورۃ النور: ۶ )','Explicit source chapter/verse locator; actual recitation and supplied translation remain selected.')]))
k='abudawud:2258'
add(k,field(k,'hi','Said ibn Jubayr relays Ibn Umar’s report of the Messenger; the unprinted question is not supplied.'),
 field(k,'ur','Said ibn Jubayr relays his printed question and Ibn Umar’s report of the Messenger; the actual circumstance qualifier remains.',cuts=[cut('۱؎','Source footnote label, not report wording.')]))
k='abudawud:2268'
add(k,field(k,'hi','Per individually attributed component.',parts=[
 part('उम्-उल-मोमिनीन ऐषा','अबू दाऊद कहते हैं: \'असरीर वाझीही\' के अल्फ़ाज़','aisha-observation','companion_report_with_honorific_pronoun_attribution','Aisha describes the joyful honorific-referred visitor; the omitted explicit actor name is not filled.',k+':hi:aisha-observation'),
 part('अबू दाऊद कहते हैं: मैं ने अहमद बिन सालेह',None,'ahmad-historical-assertion','named_scholar_historical_statement','Abu Dawud says he heard Ahmad ibn Salih describe the two named persons; Hindi’s defective name is preserved exactly.',k+':hi:ahmad-assertion')]),
 field(k,'ur','Per individually attributed component.',cuts=[cut('۱؎','Source footnote label within the historical assertion.')],parts=[
 part('ام المؤمنین عائشہ','ابوداؤد کہتے ہیں: «أسارير وجهه» کے الفاظ','aisha-observation','companion_report_with_honorific_pronoun_attribution','Aisha describes the joyful honorific-referred visitor; the omitted explicit actor name is not filled.',k+':ur:aisha-observation'),
 part('ابوداؤد کہتے ہیں: میں نے احمد بن صالح',None,'ahmad-historical-assertion','named_scholar_historical_statement','Abu Dawud says he heard Ahmad ibn Salih describe Usama and Zayd; this is the named scholar’s statement.',k+':ur:ahmad-assertion')]))
k='abudawud:2269'
add(k,field(k,'hi','Zayd ibn Arqam hears an unnamed Yemeni recount Ali’s judgment, then observes the Messenger’s laughter; the nested acts keep their stated actors.','companion_eyewitness_report_with_nested_judgment',cuts=[cut('(पाकी)','Lexical definition of tuhr, preserved as context.')]),
 field(k,'ur','Zayd ibn Arqam hears an unnamed Yemeni recount Ali’s judgment, then observes the Messenger’s laughter; the nested acts keep their stated actors.','companion_eyewitness_report_with_nested_judgment',cuts=[cut('( پاکی )','Lexical definition of tuhr, preserved as context.')]))
k='abudawud:2272'
add(k,field(k,'hi','Ibn Shihab through Urwa transmits Aisha’s historical account of the four practices and their abolition; it is not a direct Prophetic speech.','companion_historical_report',cuts=[
 cut('(उम्दा नसब का)','Lexical definition of najib, not an additional narrated action.'),cut('(नुत्फ़ा हासिल करने का निकाह)','Lexical explanation of the named marriage practice.')]),
 field(k,'ur','Ibn Shihab through Urwa transmits Aisha’s historical account of the four practices and their abolition; it is not a direct Prophetic speech.','companion_historical_report',cuts=[
 cut('( عمدہ نسب کا )','Lexical definition of najib, not an additional narrated action.'),cut('( نطفہ حاصل کرنے کا نکاح )','Lexical explanation of the named marriage practice.')]))
k='abudawud:2276'
add(k,field(k,'hi','Abdullah ibn Amr transmits the mother’s plea and the Messenger’s condition concerning another marriage.'),field(k,'ur','Abdullah ibn Amr transmits the mother’s plea and the Messenger’s condition concerning another marriage.'))
k='abudawud:2280'
add(k,field(k,'hi','Per actual narrated portion.',parts=[
 part(None,'रावी ने फिर पूरा क़िस्सा बयान किया','departure-and-reception','companion_eyewitness_report','Ali relates the departure and reception of Hamza’s daughter; Fatimah is identified in the own source.',k+':hi:hamza-daughter'),
 part("जा'अफर (रदी अल्लाहु अन्हु) कहने लगे:",None,'kinship-and-ruling','companion_report_with_prophetic_ruling','The resumed account gives Jaafar’s own kinship claim and the explicitly named Messenger’s ruling; the omitted middle is not supplied.',k+':hi:hamza-daughter')]),
 field(k,'ur','Per actual narrated portion.',parts=[
 part(None,'راوی نے پھر پورا قصہ بیان کیا','departure-and-reception','companion_eyewitness_report','Ali relates the departure and reception of Hamza’s daughter; Fatimah is identified in the own source.',k+':ur:hamza-daughter'),
 part('جعفر رضی اللہ عنہ کہنے لگے:',None,'kinship-and-ruling','companion_report_with_prophetic_ruling','The resumed account gives Jaafar’s own kinship claim and the explicitly named Messenger’s ruling; the omitted middle is not supplied.',k+':ur:hamza-daughter')]))
k='tirmidhi:2225'
add(k,field(k,'hi','Ibn Umar transmits Umar’s own succession reply, including Umar’s claims about Abu Bakr and the Messenger.','companion_statement_with_historical_precedent',end='इमाम तिरमिज़ी कहते हैं:'),
 field(k,'ur','Ibn Umar transmits Umar’s own succession reply, including Umar’s claims about Abu Bakr and the Messenger.','companion_statement_with_historical_precedent',end='امام ترمذی کہتے ہیں:',cuts=[cut('۱؎','Footnote label within Umar’s statement.')]))
k='tirmidhi:2239'
add(k,field(k,'hi','Anas ibn Malik is the explicitly named speaker of this prediction; no Prophet-said link is added.','companion_prediction',end='महमूद बिन गइलन कहते हैं:'),
 field(k,'ur','Anas ibn Malik is the explicitly named speaker of this prediction; no Prophet-said link is added.','companion_prediction',end='محمود بن غیلان کہتے ہیں:'))
k='tirmidhi:2240'
add(k,field(k,'hi','Nawwas ibn Saman transmits the explicitly identified Messenger’s account and the source’s own abbreviated question/answer sequence.',end='इमाम तिरमिज़ी कहते हैं:'),
 field(k,'ur','Nawwas ibn Saman transmits the explicitly identified Messenger’s account, its questions and answers, recitation and supplied translation.',end='امام ترمذی کہتے ہیں:',cuts=[
 cut('( اس کی حقارت اور اس کے فتنے کی سنگینی بیان کرتے ہوئے دوران گفتگو )','Interpretation of what the changing voice signifies, supplied as explanatory apparatus.'),
 cut('( مدینہ کی )','Parenthetic geographical identification of the palms, preserved as context.'),
 cut('( اس کی حقارت اور سنگینی بیان کرتے ہوئے )','Repeated interpretive explanation of the voice change.'),
 cut('( جانشیں )','Lexical synonym of khalifa.'),
 cut('( اور وہ بارش کو نہایت تیزی سے پورے علاقے میں پھیلا دیتی ہے )','Explanatory expansion of the wind/rain simile, distinct from the quoted comparison itself.'),
 cut('( انکار کرنے والوں )','Repeated explanatory identification of the just-mentioned rejecting group; the actual rejection and loss remain selected.'),
 cut('( چراگاہ سے )','Supplied explanation of the grazing animals’ point of return.'),
 cut('( دودھ سے )','Explanatory complement of the already printed full udders.'),
 cut('( الأنبياء: ۹۶ )','Explicit chapter/verse locator; actual Arabic quotation and supplied translation remain.'),
 cut('( شام کی )','Parenthetic geographical identification of the lake.'),
 cut('( نامی جھیل )','Lexical identification of the named lake.'),
 cut('( شدید قحط سالی کی وجہ سے )','Explanatory inference about why the head has the stated value.'),
 cut('( چیزیں اس قدر مہنگی ہوں گی )','Interpretive price explanation after the actual comparison.'),
 cut('۱؎','Footnote label.'),cut('۲؎','Footnote label.'),cut('۳؎','Footnote label.'),cut('۴؎','Footnote label.'),cut('۵؎','Footnote label.')] ))
k='tirmidhi:2246'
add(k,field(k,'hi','Abu Said gives his own journey with Ibn Sayyad and quotes Ibn Sayyad’s claimed Prophetic precedents and later claim to know the Dajjal; these retain their nested speakers.','companion_eyewitness_report_with_nested_claims',end='इमाम तिरमिज़ी कहते हैं:'),
 field(k,'ur','Abu Said gives his own journey with the source-named Ibn Said and quotes that man’s claimed Prophetic precedents and later claim to know the Dajjal; these retain their nested speakers.','companion_eyewitness_report_with_nested_claims',end='امام ترمذی کہتے ہیں:',cuts=[
 cut('( ابن صیاد )','Parenthetic alternate spelling of the source actor, retained as context rather than replacing the printed name.'),
 cut('( یعنی دجال ہے )','Explanatory identification of what people were saying.'),cut('۱؎','Source footnote label.')]))
k='tirmidhi:2289'
add(k,field(k,'hi','Ibn Umar transmits the explicitly identified Prophet’s dream, supplication and comparison.',end='(यानी सब आसूदा हो गए)'),
 field(k,'ur','Ibn Umar transmits the explicitly identified Prophet’s dream, supplication and comparison; the printed well setting remains.',end='( یعنی سب آسودہ ہو گئے ۱؎ )'))
k='tirmidhi:2290'
add(k,field(k,'hi','Ibn Umar transmits the explicitly identified Prophet’s dream and its own supplied fever interpretation.',end='इमाम तिर्मिज़ी कहते हैं:',cuts=[cut('(मुहईआ, जुहफ़ा का दूसरा नाम है)','Geographical alternate-name explanation.')]),
 field(k,'ur','Ibn Umar transmits the explicitly identified Prophet’s dream and its own supplied fever interpretation.',end='امام ترمذی کہتے ہیں:',cuts=[cut('( مهيعه، جحفه کا دوسرا نام ہے )','Geographical alternate-name explanation.')]))

# Three exact source-context refinements agreed after the independent second reading.
# Original v1 remains frozen in the parent directory; no other field decision changes.
by_key={record['key']:record for record in records}
by_key['abudawud:2233']['fields']['hi']['omit_source_context'].append(
    cut('(बारीरा को)','Redundant pronoun expansion repeating the already explicit Barira object; the emancipation condition and full counterfactual remain.'))
by_key['abudawud:2233']['fields']['ur']['omit_source_context'].append(
    cut('( بریرہ کو )','Redundant pronoun expansion repeating the already explicit Barira object; the emancipation condition and full counterfactual remain.'))
by_key['abudawud:2253']['fields']['ur']['omit_source_context'].append(
    cut('آخر تک','Pointer to an unprinted verse continuation; actual recitation, translation and narrated revelation remain selected.'))

def main():
    assert len(records)==len(NOTES)==21 and {r['key'] for r in records}==set(NOTES)
    for book in ('abudawud','tirmidhi'):
        obj={'schema':'hadith-bank-manual-source-reading-instructions-v1','source_checkpoint':CHECKPOINT,
             'actual_complete_field_scope':'All own Hindi and Urdu fields; no other-language reading claimed.',
             'records':[r for r in records if r['key'].startswith(book+':')]}
        (ROOT/('manual-'+book+'.json')).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
