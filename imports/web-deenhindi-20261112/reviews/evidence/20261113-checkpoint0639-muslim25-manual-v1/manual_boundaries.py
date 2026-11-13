"""Exact human-selected boundaries after the frozen 59 complete own-field readings.

Selection is explicitly authored for each field. Helpers only resolve exact anchors;
they never approve an unlisted field or infer a report from a sibling language.
"""
from manual_source_first_readings import NOTES

READINGS = {}


def field(number, language, report_type=None, speaker=None, cuts=(), segments=None,
          exact=None, context_all=False, retained=()):
    key = 'muslim:' + number
    assert ('deenhindi-' + key, language) in NOTES
    assert language not in READINGS.setdefault(key, {})
    READINGS[key][language] = {
        'note': NOTES[('deenhindi-' + key, language)],
        'type': report_type, 'speaker': speaker, 'context': list(cuts),
        'context_all': context_all,
        'source_report_family_id': key + ':source-numbered-report',
        'retained_meaningful_structures': list(retained),
    }
    if segments is not None:
        READINGS[key][language]['segments'] = segments
    if exact is not None:
        READINGS[key][language]['exact_selections'] = exact


def part(start=None, end=None, component='report-1', report_type=None, speaker=None):
    item = {'start': start, 'end': end, 'id': component}
    if report_type: item['type'] = report_type
    if speaker: item['speaker'] = speaker
    return item


field('2237', 'hi', 'qualified_historical_and_prophetic_action_report',
      'The chain names Abdullah ibn Buraydah, but the first-person youth and funeral reporter is unnamed in this defective Hindi field. The supplied funeral-position statements expressly concern the Messenger; missing Samurah identity and eyewitness links are not supplied.',
      cuts=['(बिन ज़कवान)'],
      segments=[part(end='इब्न मुथन्ना की रिवायत में है', component='unnamed-main-testimony'),
                part(start='इब्न मुथन्ना की रिवायत में है', component='finite-funeral-variant',
                     report_type='qualified_transmitted_action_variant',
                     speaker='Ibn Muthanna’s printed variant explicitly frames Husayn and Abdullah ibn Buraydah before a finite funeral-position clause; the ultimate eyewitness is not named in this own Hindi field.')],
      retained=['(अहादीस सुन कर)', '(सामने)', '(हुसैन ने)'])
field('2237', 'ur', 'companion_testimony_with_prophetic_action',
      'Samurah ibn Jundub explicitly supplies his youth, memorization and funeral testimony through Abdullah ibn Buraydah; the report describes the Messenger’s funeral-prayer position.',
      cuts=['( بن ذکوان )'],
      segments=[part(end='ابن مثنیٰ کی روایت میں ہے', component='samurah-main-testimony'),
                part(start='ابن مثنیٰ کی روایت میں ہے', component='finite-funeral-variant',
                     report_type='qualified_transmitted_action_variant',
                     speaker='The printed Ibn Muthanna variant names Husayn and Abdullah ibn Buraydah and repeats the finite funeral-position clause in this same report family; no separate independent occurrence is created.')],
      retained=['( احادیث سن کر )', '( سامنے )', '( حسین نے )'])
field('2238', 'hi', 'prophetic_action_report',
      'Jabir ibn Samurah’s printed report describes the Messenger’s mounting after the funeral and the narrator’s group walking around him; the defective chain/connective wording is preserved.',
      cuts=['(बग़ैर ज़ीन के)'], retained=['(पैदल)'])
field('2238', 'ur', 'prophetic_action_report',
      'Jabir ibn Samurah reports the Messenger’s mounting after the funeral and the companions walking around him, preserving the source’s own malformed chain.',
      cuts=['( بغیرزین کے )'], retained=['( پیدل )'])
field('2240', 'hi', 'companion_deathbed_instruction',
      'Amir ibn Sad reports Sad ibn Abi Waqqas’s own deathbed burial instructions and his comparison with the Messenger’s burial treatment; these orders are Sad’s words.',
      cuts=['(अपने लवाहीक़ीन से)', '(क़ब्र-ए-मुबारक)'])
field('2240', 'ur', 'companion_deathbed_instruction',
      'Amir ibn Sad reports Sad ibn Abi Waqqas’s own deathbed instructions, with the source’s comparison to the Messenger’s burial treatment; no direct Prophetic command is asserted.',
      cuts=['( اپنے لواحقین سے )', ') قبر مبارک )'])
field('2241', 'hi', 'qualified_companion_historical_report',
      'Ibn Abbas, through Abu Jamrah, reports a red thick cloth placed in a grave. This Hindi field does not identify whose grave, and the fuller Urdu identity is not imported.',
      cuts=['(बिछायी)'], segments=[part(end='इमाम मुस्लिम (रहमतुल्लाह अलैह) ने कहा:', component='grave-cloth-report')])
field('2241', 'ur', 'companion_report_of_prophetic_burial',
      'Ibn Abbas through Abu Jamrah explicitly identifies the Messenger’s grave in this Urdu field. The appended Muslim transmitter identifications and biographical explanation are context.',
      cuts=['( بچھائی )'], segments=[part(end='امام مسلم ؒ نے کہا :', component='grave-cloth-report')])

# These are four separately read fields of two distinct provider occurrences.
field('2243', 'hi', 'companion_commission_related_to_prophetic_commission',
      'Abu al-Hayyaj reports Ali’s actual question and commands, which Ali expressly relates to an earlier commission from the Messenger. Ali is the operative speaker; direct Prophetic wording is not invented.',
      cuts=['(मुहिम)', '(वो ये है)'], retained=['(ज़मीन के)'])
field('2243', 'ur', 'companion_commission_related_to_prophetic_commission',
      'Abu al-Hayyaj reports Ali’s actual commission and its express relation to the Messenger’s earlier mission; the image and grave commands here are voiced by Ali.',
      cuts=['( مہم )', '( وہ یہ ہے )'], retained=['( زمین کے )'])
field('2244', 'hi', 'companion_commission_related_to_prophetic_commission',
      'This separate occurrence supplies Abu al-Hayyaj’s report of Ali’s commands and their stated prior Prophetic commission relation. Preserve the separate provider identity and Ali’s actual voice.',
      cuts=['(मुहिम)', '(वो ये है)'], retained=['(ज़मीन के)'])
field('2244', 'ur', 'companion_commission_related_to_prophetic_commission',
      'This independently read Urdu occurrence gives Ali’s commands through Abu al-Hayyaj, expressly related by Ali to the Messenger’s earlier commission. It remains a separate provider occurrence.',
      cuts=['( مہم )', '( وہ یہ ہے )'], retained=['( زمین کے )'])
field('2245', 'hi', 'prophetic_report',
      'Jabir explicitly reports the Messenger’s three grave-related prohibitions, through the printed chain.', cuts=['(इस बात से)'])
field('2245', 'ur', 'prophetic_report',
      'Jabir explicitly reports the Messenger’s three prohibitions through the printed source chain.', cuts=['( اس بات سے )'])
field('2259', 'hi', 'prophetic_action_and_saying_report',
      'Abu Hurayrah reports the Messenger’s visit, crying and statement of the two different permissions and the grave-visit instruction; each printed permission polarity remains exact.')
field('2259', 'ur', 'prophetic_action_and_saying_report',
      'Abu Hurayrah explicitly reports the Messenger’s visit, crying and two-permissions statement. The duplicated conjunction and unclosed source quote are preserved.')
field('2262', 'hi', 'qualified_transmitted_funeral_action',
      'Jabir ibn Samurah reports that the figure designated only by आप plus the Prophetic honorific did not personally pray the deceased man’s funeral. The own Hindi field lacks a separate explicit Prophet-name introduction, and the appended others/debtors explanation is not admitted.',
      segments=[part(end='(दूसरों को पढ़ने का हुकुम दिया', component='personal-nonparticipation')])
field('2262', 'ur', 'prophetic_action_report',
      'Jabir ibn Samurah expressly reports the Prophet’s personal nonparticipation in this funeral prayer. The own-field self qualifier is retained; the explanatory instruction-to-others appendix remains context.',
      segments=[part(end='( دوسروں کو پڑھنے کا حکم دیا', component='personal-nonparticipation')], retained=['( خود )'])
for language in ('ar', 'hi', 'ur', 'ur-Latn', 'en'):
    field('2264', language, context_all=True)
field('2279', 'hi', 'prophetic_report',
      'Ibn Umar explicitly reports the Messenger’s assignment, source food alternatives and one-sa quantity for the printed age/freedom classes.', cuts=['(फ़ित्राना)'])
field('2279', 'ur', 'prophetic_report',
      'Ibn Umar explicitly reports the Messenger’s assignment, exact source unit and food alternatives, with its printed scope.', cuts=['( فطرا نہ )'])
field('2280', 'hi', 'mixed_prophetic_and_community_assessment_report',
      'Ibn Umar reports the Prophetic assignment, followed by a separately voiced assessment by unnamed people; the latter judgment is not Prophetic speech.',
      segments=[part(end='कहा: लोगों ने', component='prophetic-assignment', report_type='prophetic_report',
                     speaker='Ibn Umar reports the Messenger’s assignment and source dates-or-barley quota.'),
                part(start='कहा: लोगों ने', component='people-wheat-assessment', report_type='reported_community_assessment',
                     speaker='The continuation reports unnamed people’s wheat-equivalence assessment, not a statement attributed to the Prophet.')],
      retained=['(जौ)', "(एक सा' के)"])
field('2280', 'ur', 'mixed_prophetic_and_community_assessment_report',
      'Ibn Umar’s report distinguishes the Messenger’s assignment from the subsequent unnamed people’s wheat-equivalence assessment.',
      segments=[part(end='کہا : لو گوں نے', component='prophetic-assignment', report_type='prophetic_report',
                     speaker='Ibn Umar reports the Messenger’s assignment with its printed sex/freedom scope and dates-or-barley quota.'),
                part(start='کہا : لو گوں نے', component='people-wheat-assessment', report_type='reported_community_assessment',
                     speaker='The source reports unnamed people’s subsequent half-sa wheat equivalence; this assessment is not Prophetic speech.')],
      retained=['( جو )', '( ایک صاع کے )'])
field('2283', 'hi', 'companion_collective_practice_report',
      'Abu Said reports what his group used to give. This own Hindi field supplies no explicit Prophetic-era or approval clause; the exact five-item source list and damaged raisin word remain.', cuts=['(गंदुम)'])
field('2283', 'ur', 'companion_collective_practice_report',
      'Abu Said reports his group’s actual five-item giving practice. No explicit Prophetic-era or approval clause is supplied in this Urdu field.', cuts=['( گندم )'])
field('2284', 'hi', 'mixed_companion_practice_and_assessment',
      'Abu Said’s supplied collective practice and Muawiyah’s explicitly voiced opinion remain distinct. The final broken Abu Said resolution is context and is not repaired from Urdu.',
      cuts=['(गंदुम)', '(फ़ितरना)', '(महंगी)', '(निस्फ़ सा’)'],
      segments=[part(end='मुआवियाह बिन आबि सुफ़ियान', component='prophetic-period-practice', report_type='companion_collective_practice_report',
                     speaker='Abu Said reports the printed group practice while the Messenger was among them; no omitted free/slave words are supplied.'),
                part(start='मुआवियाह बिन आबि सुफ़ियान', end='अबू सईद खुदरी (रज़ियल्लाहु अन्हु) ने कहा: लेकिन', component='muawiyah-assessment', report_type='companion_opinion_and_reported_adoption',
                     speaker='Muawiyah’s explicitly reported wheat-equivalence opinion and the people’s adoption, within Abu Said’s historical account; the later broken first-person conclusion is not completed.')])
field('2284', 'ur', 'mixed_companion_practice_and_assessment',
      'Abu Said’s complete practice account, Muawiyah’s opinion and Abu Said’s own continuation resolution remain separately attributed source components.',
      cuts=['( گندم )', '( فطرانہ )', '( امیر المومنین )', '( مہنگی )', '( نصف صاع )'],
      segments=[part(end='یہاں تک کہ ہمارے پاس', component='prophetic-period-practice', report_type='companion_collective_practice_report',
                     speaker='Abu Said reports the collective practice and its free/slave scope in the Messenger’s presence.'),
                part(start='یہاں تک کہ ہمارے پاس', end='ابو سعید خدری رضی اللہ تعالیٰ عنہ نے کہا : لیکن', component='muawiyah-assessment', report_type='companion_opinion_and_reported_adoption',
                     speaker='Muawiyah voices his wheat-equivalence opinion; the same source continuation reports the people’s adoption.'),
                part(start='ابو سعید خدری رضی اللہ تعالیٰ عنہ نے کہا : لیکن', component='abu-said-continuation', report_type='companion_saying',
                     speaker='Abu Said personally resolves to continue his former practice; the parenthetic Prophetic-period comparison completes this own Urdu sentence.')],
      retained=['( عہدنبوی صلی اللہ علیہ وسلم میں نکا لا کرتا تھا ۔)'])
field('2285', 'hi', 'mixed_companion_practice_and_assessment',
      'Abu Said’s practice, Muawiyah’s opinion and Abu Said’s continuation reply are separately voiced in this one numbered report.',
      cuts=['(क़िस्म की)'],
      segments=[part(end='अमीर मुआविया', component='prophetic-period-practice', report_type='companion_collective_practice_report',
                     speaker='Abu Said describes the group’s three-food practice while the Messenger was present, with the printed quantities.'),
                part(start='अमीर मुआविया', end='हज़रत अबू सईद खुदरी (रदी अल्लाहु अन्हु) ने कहा: लेकिन', component='muawiyah-assessment', report_type='companion_opinion',
                     speaker='The report explicitly attributes the later wheat/date equivalence to Muawiyah.'),
                part(start='हज़रत अबू सईद खुदरी (रदी अल्लाहु अन्हु) ने कहा: लेकिन', component='abu-said-continuation', report_type='companion_saying',
                     speaker='Abu Said personally says he will continue the earlier method; the retained qualifier distinguishes it from the new preceding opinion.')],
      retained=['(पहले तरीक़े से)'])
field('2285', 'ur', 'mixed_companion_practice_and_assessment',
      'The own Urdu source gives the practice, Muawiyah’s opinion and the closing reply under its printed shortened Abu Khudri name; no spelling is repaired.',
      cuts=['( قسم کی )'],
      segments=[part(end='امیر معاویہ', component='prophetic-period-practice', report_type='companion_collective_practice_report',
                     speaker='Abu Said reports the group’s three-food practice in the Messenger’s presence.'),
                part(start='امیر معاویہ', end='حضرت ابو خدری رضی اللہ تعالیٰ عنہ نے کہا', component='muawiyah-assessment', report_type='companion_opinion',
                     speaker='The later wheat/date equivalence is explicitly Muawiyah’s opinion.'),
                part(start='حضرت ابو خدری رضی اللہ تعالیٰ عنہ نے کہا', component='abu-said-continuation', report_type='companion_saying',
                     speaker='The closing source names Abu Khudri after the earlier Abu Said framing; preserve the shortened printed attribution and the actual earlier-method continuation qualification.')],
      retained=['( پہلے طریقے سے )'])
field('2286', 'hi', 'companion_collective_practice_report',
      'Abu Said reports the group’s three-food practice; this field has no quantity or explicit Prophetic-era statement. The foodstuffs explanation is separate context.',
      segments=[part(end='(यही इनकी बुनियादी', component='three-food-practice')])
field('2286', 'ur', 'companion_collective_practice_report',
      'Abu Said reports the group’s three-food practice without a source quantity or explicit Prophetic-era clause. The final foodstuffs explanation remains context.',
      segments=[part(end='( یہی ان کی بنیا دی', component='three-food-practice')])
field('2287', 'hi', 'mixed_companion_assessment_and_reply',
      'The source distinguishes Muawiyah’s equivalence from Abu Said’s refusal to adopt it and his own former-practice commitment.',
      cuts=['(और वो है)'],
      segments=[part(end='तो अबू सईद', component='muawiyah-assessment', report_type='companion_opinion',
                     speaker='The source attributes the wheat/date equivalence to Muawiyah.'),
                part(start='तो अबू सईद', component='abu-said-refusal', report_type='companion_saying_and_practice',
                     speaker='Abu Said refuses to accept that assessment and describes his own practice in the Messenger’s time; no new Prophetic command is inferred.')], retained=['(को मानने)'])
field('2287', 'ur', 'mixed_companion_assessment_and_reply',
      'Muawiyah’s assessment and Abu Said’s actual refusal and four-item practice are distinct source voices.',
      cuts=['( اور وہ ہے )'],
      segments=[part(end='تو ابو سعید', component='muawiyah-assessment', report_type='companion_opinion',
                     speaker='The source attributes the wheat/date assessment to Muawiyah.'),
                part(start='تو ابو سعید', component='abu-said-refusal', report_type='companion_saying_and_practice',
                     speaker='Abu Said refuses acceptance and reports his former practice; this is his own saying rather than a fresh Prophetic command.')], retained=['( کو ماننے )'])
field('2291', 'hi', 'qualified_transmitted_report_fragments',
      'The field supplies finite variant fragments within chain/comparison apparatus. The ultimate report speaker and local pronoun referents are unnamed; no Prophetic identity or omitted main report is supplied.',
      exact=[{'text':"'वो इन में से दूध छुड़ाए हुए एक बच्चे को भी गुम न पाएगा'",'id':'weaned-calf-fragment'},
             {'text':"'यिक़्वी बिहा जंबहु व जबहतहु व ज़हरहु' (उस के दोनों पहलू, उस की पेशानी और कमर को दागा जाएगा)",'id':'branding-fragment'}],
      retained=['(उस के दोनों पहलू, उस की पेशानी और कमर को दागा जाएगा)'])
field('2291', 'ur', 'qualified_transmitted_report_fragments',
      'Only the two supplied finite variants and the source’s own Arabic/Urdu branding rendering are admitted. The ultimate speaker and pronoun referents remain unspecified locally; surrounding substitutions do not supply a missing report.',
      exact=[{'text':'" وہ ان میں سے دودھ چھڑائے ہوئے ای بچے کوبھی گم نہ پائے گا "','id':'weaned-calf-fragment'},
             {'text':'يكوي بها جنباه وجبهته وظهره ( اس کے دونوں پہلو ، اس کی پیشانی اور کمر کو داغا جائے گا )','id':'branding-fragment'}],
      retained=['( اس کے دونوں پہلو ، اس کی پیشانی اور کمر کو داغا جائے گا )'])
field('2293', 'ar', 'qualified_transmitted_report_fragment',
      'The saved Arabic transmits this finite passive branding clause within variant apparatus. The ultimate speaker and pronoun referents are not supplied in this field; no Prophetic attribution, complete report or identity is inferred.',
      exact=[{'text':'فَيُكْوَى بِهَا جَنْبُهُ وَظَهْرُهُ','id':'branding-fragment'}])
for language in ('hi', 'ur', 'ur-Latn', 'en'):
    field('2293', language, context_all=True)
for language in ('ar', 'hi', 'ur', 'ur-Latn', 'en'):
    field('2299', language, context_all=True)
field('2300', 'hi', 'companion_testimony_with_prophetic_dialogue',
      'Abu Dharr supplies the encounter, his question and the Messenger’s answer, including the rich-person giving exception and animal-zakat consequence. Donor example words remain within the stated example, not a separate Prophetic command.',
      retained=['(ही था)', '(ले लो, ले लो)', '(के सर)'])
field('2300', 'ur', 'companion_testimony_with_prophetic_dialogue',
      'Abu Dharr’s actual encounter and the Messenger’s oath/answer retain all source spelling, giving exception and conditional animal consequence. The quoted donor expression remains an example within the answer.',
      retained=['( ہی تھا )', '( لے لو ، لے لو )', '( کے سر )'])
field('2301', 'hi', 'qualified_abbreviated_prophetic_report',
      'Abu Dharr’s arrival/Kaaba-shade scene and the explicitly attributed Prophetic oath are actual supplied finite passages. The final unpaid-animals condition lacks its consequence and remains context without borrowing2300.',
      segments=[part(end='आगे वाक़ी की रिवायत', component='arrival-scene', report_type='companion_testimony',
                     speaker='Abu Dharr reports his actual arrival and the Messenger seated in the Kaaba shade.'),
                part(start='आप (सल्लल्लाहु अलैहि वसल्लम) ने फरमाया: "उस ज़ात', end='ज़मीन पर जो भी आदमी', component='prophetic-oath', report_type='prophetic_saying_fragment',
                     speaker='The own field expressly attributes this finite oath to the Messenger; its missing following consequence is not reconstructed.')])
field('2301', 'ur', 'qualified_abbreviated_prophetic_report',
      'Abu Dharr’s finite arrival scene and the explicitly attributed oath remain selected; the Waki pointer and result-less animal condition remain source context.',
      segments=[part(end='آگے وکیع کی روایت', component='arrival-scene', report_type='companion_testimony',
                     speaker='Abu Dharr reports arrival at the Messenger’s Kaaba-shade setting.'),
                part(start='آپ صلی اللہ علیہ وسلم نے فرمایا : " اس ذات', end='زمین پر جو بھی آدمی', component='prophetic-oath', report_type='prophetic_saying_fragment',
                     speaker='The field expressly supplies the Messenger’s oath, but not the consequence of the following condition.')])
field('2305', 'hi', 'qualified_damaged_companion_testimony_with_nested_report',
      'Abu Dharr’s Hindi account has missing speaker links and a missing wealth-exception clause. Actual supplied scene, speech and retold Gabriel dialogue are preserved with those defects; no complete Urdu wording or speaker link is transferred.',
      cuts=['डाला और इस में नेकी के काम किये.&quot;', {'text':'(हररह)', 'count':2}],
      segments=[part(end='अन्हु) आ जाओ.&quot;', component='abu-dharr-opening',
                     report_type='qualified_damaged_companion_testimony',
                     speaker='Abu Dharr’s source testimony supplies the departure, question and reply. Its missing connective words remain unrepaired.'),
                part(start='आ जाओ.&quot;', end=' कहा: मैं कुछ देर', component='unattributed-invitation-fragment',
                     report_type='qualified_unattributed_saying_fragment',
                     speaker='This source supplies an actual come-here imperative but drops its speaker link. Preserve the finite invitation under an unnamed speaker; do not borrow Urdu’s explicit Prophetic attribution. The preceding stranded honorific fragment remains context.'),
                part(start=' कहा: मैं कुछ देर', end='आप (सल्लल्लाहु अलैहि वसल्लम) ने फ़रमाया: &quot;वह जिब्रील', component='abu-dharr-encounter',
                     report_type='qualified_damaged_companion_testimony',
                     speaker='Abu Dharr’s source testimony includes the journey and expressly printed Prophetic questions/instructions. The wealthy statement is a visibly abridged fragment with its exception linkage absent; no missing Urdu words are supplied.'),
                part(start='आप (सल्लल्लाहु अलैहि वसल्लम) ने फ़रमाया: &quot;वह जिब्रील', component='retold-gabriel-dialogue',
                     report_type='prophetic_retelling_of_gabriel_dialogue',
                     speaker='The Messenger is expressly the retelling speaker; within that retelling Gabriel supplies the message and answers, while the Messenger asks. The Hindi ending stops at its printed third yes and is not completed from Urdu.')],
      retained=['(घर से)', '(तीसरी बार)'])
READINGS['muslim:2305']['hi']['boundary_refinement'] = 'The frozen source-first note required preserving actual supplied wording without assigning the damaged invitation link a speaker. Exact segmentation therefore retains the finite आ जाओ imperative as an explicitly unattributed fragment, and keeps only the stranded preceding honorific in context. No missing attribution is supplied.'
field('2305', 'ur', 'companion_testimony_with_nested_prophetic_report',
      'Abu Dharr’s own testimony retains the complete journey and wealth exception; the Messenger’s later retelling keeps Gabriel’s message/answers distinct from the Messenger’s questions.',
      cuts=['( حرے )', '( حرہ )'],
      segments=[part(end='آپ صلی اللہ علیہ وسلم نے فرمایا : " وہ جبرئیل', component='abu-dharr-encounter', report_type='companion_testimony_with_prophetic_dialogue',
                     speaker='Abu Dharr reports his actual night encounter, explicitly attributed Prophetic instructions and the source’s complete wealthy-with-giving-exception statement.'),
                part(start='آپ صلی اللہ علیہ وسلم نے فرمایا : " وہ جبرئیل', component='retold-gabriel-dialogue', report_type='prophetic_retelling_of_gabriel_dialogue',
                     speaker='The Messenger retells his exchange with Gabriel: Gabriel voices the message and replies, the Messenger the questions. The third-question count and final alcohol qualification remain exactly supplied.')],
      retained=['( گھرسے )', '( مایہ )', '( تیسری بار )', '( بھی )'])
field('2306', 'hi', 'historical_dialogue_with_embedded_prophetic_report',
      'Ahnaf describes an unnamed man, his warning and his retold Abul Qasim dialogue, followed by the same man’s own refusal/oath. This field does not name Abu Dharr;2307 is not used to identify him.',
      cuts=['(पहाड़)', '(सोने)'],
      segments=[part(end='मेरे खलील अबुल क़ासिम', component='ahnaf-and-unnamed-man', report_type='historical_testimony_and_unnamed_saying',
                     speaker='Ahnaf reports the gathering and an unnamed man’s warning and initial reply; no ultimate Prophetic attribution is supplied for that initial warning here.'),
                part(start='मेरे खलील अबुल क़ासिम', end='फिर ये लोग हैं दुनिया', component='unnamed-man-abul-qasim-report', report_type='prophetic_report_via_unnamed_narrator',
                     speaker='The unnamed man expressly recounts Abul Qasim’s questions and gold/spending statement and his own replies. Preserve the source’s unusual negative construction without canonical correction.'),
                part(start='फिर ये लोग हैं दुनिया', component='unnamed-man-own-conclusion', report_type='historical_dialogue_and_unnamed_saying',
                     speaker='The narrative returns to the unnamed man’s judgment, Ahnaf’s question and the man’s own oath/refusal. These are not voiced by the Prophet.')],
      retained=['(अहनाफ़ ने)', '(टैक लगा कर)', '(भी)', '(हुक्मरान)'])
field('2306', 'ur', 'historical_dialogue_with_embedded_prophetic_report',
      'Ahnaf reports an unnamed man and the man’s expressly framed Abul Qasim dialogue, then his own concluding refusal. No identity is inferred from a neighboring occurrence.',
      cuts=['( پہاڑ )', '( سونے )'],
      segments=[part(end='میرے خلیل ابو القاسم', component='ahnaf-and-unnamed-man', report_type='historical_testimony_and_unnamed_saying',
                     speaker='Ahnaf reports the gathering, the unnamed man’s warning and the initial exchange; the warning has no explicit ultimate Prophetic link in this own field.'),
                part(start='میرے خلیل ابو القاسم', end='پھر یہ لو گ ہیں دنیا', component='unnamed-man-abul-qasim-report', report_type='prophetic_report_via_unnamed_narrator',
                     speaker='The unnamed man expressly retells Abul Qasim’s words and his own replies. The unusual negative gold/spending wording remains exact.'),
                part(start='پھر یہ لو گ ہیں دنیا', component='unnamed-man-own-conclusion', report_type='historical_dialogue_and_unnamed_saying',
                     speaker='The source returns to the unnamed man’s statement, Ahnaf’s question and that man’s oath/refusal; these statements are not attributed to the Prophet.')],
      retained=['( احنف نے )', '( ٹیک لگا کر )', '( بھی )', '( حکمران )'])
field('2307', 'hi', 'companion_testimony_and_companion_saying',
      'Ahnaf’s own field explicitly names Abu Dharr. His warning carries his later printed heard-from-their-Prophet attribution; the later financial reply is Abu Dharr’s own saying. Source defects are retained.',
      cuts=['(वज़ीफ़े)'],
      segments=[part(end='कहा मैंने पुछा: (हुकूमत', component='abu-dharr-warning-and-attribution', report_type='prophetic_report_by_companion_testimony',
                     speaker='Ahnaf reports Abu Dharr’s warning and Abu Dharr’s express claim that he said only what he heard from their Prophet. The field’s damaged anatomy and missing initial gathering words remain exact.'),
                part(start='कहा मैंने पुछा: (हुकूमत', component='abu-dharr-financial-reply', report_type='companion_saying_in_dialogue',
                     speaker='Ahnaf asks about government grants and Abu Dharr gives his own conditional answer; it is not relabelled Prophetic speech, and the damaged printed mount/help predicate is not repaired.')],
      retained=['(आग के)', '(हुकूमत से मिलने वाले)', '(मदद)'])
field('2307', 'ur', 'companion_testimony_and_companion_saying',
      'Ahnaf explicitly identifies Abu Dharr, whose warning has his own later heard-from-the-Prophet framing. The separate financial answer remains his own saying, with all source defects preserved.',
      cuts=['( وظیفے )'],
      segments=[part(end='کہا میں نے پو چھا ( حکومت', component='abu-dharr-warning-and-attribution', report_type='prophetic_report_by_companion_testimony',
                     speaker='Ahnaf reports Abu Dharr’s warning and his express claim to have heard it from their Prophet; the printed anatomical anomaly is preserved.'),
                part(start='کہا میں نے پو چھا ( حکومت', component='abu-dharr-financial-reply', report_type='companion_saying_in_dialogue',
                     speaker='Ahnaf’s grants question and Abu Dharr’s own conditional answer are retained separately from the Prophetic warning; the source’s incomplete help-predicate grammar is preserved.')],
      retained=['( آگ کے )', '( حکومت سے ملنے والے )', '( مدد )'])

assert len(READINGS) == 25
assert sum(len(x) for x in READINGS.values()) == 59
assert {(oid, lang) for oid, lang in NOTES} == {
    ('deenhindi-' + key, lang) for key, values in READINGS.items() for lang in values
}
