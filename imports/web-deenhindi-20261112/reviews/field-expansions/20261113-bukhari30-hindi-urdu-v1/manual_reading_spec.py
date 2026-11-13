"""Explicit decisions after full Hindi and Urdu readings of these exact 30 fields each.

Literal markers encode the manually chosen boundaries; this is a serializer,
not an attribution classifier. Original spelling and all excluded text survive.
"""

SPECS = {
 '1254': dict(kind='prophetic_report', speaker='Umm Atiyya reporting Prophet Muhammad', note='Own field narrates the washing instructions, notification and supplied waistcloth. Hindi has a shortened chain; do not add Hafsa or other links from Urdu/English.'),
 '1258': dict(kind='prophetic_report', speaker='Umm Atiyya reporting Prophet Muhammad', note='Main washing account, explicitly introduced alternate three/five/seven washing wording, and Hafsa transmitting Umm Atiyya\'s braiding observation remain three separately attributed components; no neighboring ID is merged.'),
 '1259': dict(kind='prophetic_report', speaker='Umm Atiyya reporting Prophet Muhammad', note='This separate provider ID repeats the washing account, alternate three/five/seven wording and braiding report. Each own field was read; keep this occurrence and its own hash distinct from1258.'),
 '1260': dict(kind='companion_report', speaker='Umm Atiyya describing the washing and braiding of the Prophet\'s daughter', note='An attributed act by the washing women, not words or an order of the Prophet. Complete own-field description includes unbraiding, washing and three braids.'),
 '1261': dict(kind='prophetic_report', speaker='The woman narrating the washing of the Prophet\'s daughter; Prophet Muhammad gives the quoted instructions', note='The finite washing account is explicit. The Hindi opening is damaged/contracted; do not reconstruct its chain or identify its pronouns from another field. Urdu\'s visit-to-Umm-Atiyya framing is retained as printed without equating every female pronoun. Ayub\'s uncertainty, the ish\u0027ar gloss and Ibn Sirin\'s garment explanation remain context.'),
 '1262': dict(kind='companion_report', speaker='Umm Atiyya describing the braiding', note='The women\'s three-braid report and Waki\u0027 through Sufyan\u0027s explicit front/two-side wording are separated as finite variant components. No Prophetic order is supplied.'),
 '1268': dict(kind='prophetic_report', speaker='Ibn Abbas reporting Prophet Muhammad, with explicitly marked Ayyub and Amr wording variants', note='The fall/death and washing/shroud instructions are explicit; the named Ayyub/Amr variants remain in their own source framing. The final explanatory meaning of mulbi/mulbiyan is context, not an additional utterance.'),
 '1270': dict(kind='prophetic_practice_report', speaker='Jabir describing Prophet Muhammad', note='Complete account of retrieving Abdullah ibn Ubay\u0027s body, saliva and shirt. Keep only details actually printed in this own field.'),
 '1271': dict(kind='prophetic_description_report', speaker='Aisha describing the Prophet\u0027s shroud', note='Own field explicitly gives three washed cotton garments and absence of shirt/turban; no missing details are completed.'),
 '1274': dict(kind='companion_report', speaker='Abd al-Rahman ibn Awf', note='His meal-time reflection about Musab, Hamza or another uncertain Companion, worldly ease and weeping is a Companion report. Preserve the uncertainty; do not turn it into Prophetic speech. The parenthetic Uhud battle identification remains source context.'),
 '1275': dict(kind='companion_report', speaker='Abd al-Rahman ibn Awf', note='His fasting meal, insufficient shroud, uncertain recollection of Hamza, later abundance and refusal to eat are an attributed Companion report. Preserve every transmitted alternative.'),
 '1277': dict(kind='prophetic_report', speaker='Sahl describing Prophet Muhammad, the donor and the requester', note='Gift, wearing, request, rebuke and eventual shroud are the narration. Sahl\u0027s exchange with his later audience about the garment word is a lexical aside retained as context. These fields themselves name the requester Abd al-Rahman ibn Awf; retain that source claim without transferring it to other languages or canonical identity.'),
 '1278': dict(kind='companion_report', speaker='Umm Atiyya', note='Own field reports a non-emphatic prohibition of women following funerals. The issuer is passive/unnamed here; retain a Companion report without adding an explicit Prophetic quotation.'),
 '1279': dict(kind='companion_report', speaker='Umm Atiyya as reported by Ibn Sirin', note='The son\u0027s death, third-day perfume and reported mourning restriction are finite source wording. Perfume definition is context. Hindi\u0027s shortened chain and unusual sajag/man spelling remain untouched; do not repair them from Urdu.'),
 '1283': dict(kind='prophetic_report', speaker='Anas reporting Prophet Muhammad and the bereaved woman', note='The graveside encounter, later recognition and patience-at-first-shock teaching are the report. Explicit parenthetic emotional/apology/terminal explanatory additions remain source context.'),
 '1284': dict(kind='prophetic_report', speaker='Usama ibn Zayd reporting Prophet Muhammad, with Abu Uthman\u0027s stated recollection', note='The summoned visit, dying child, weeping and mercy dialogue are explicit. Abu Uthman\u0027s uncertainty remains with the comparison. The long waterskin explanation and parenthetic righteous qualifier are context. Printed Zaynab/Companion names remain source-specific claims, not inferred metadata.'),
 '1293': dict(kind='prophetic_report', speaker='Jabir reporting Prophet Muhammad', note='The father\u0027s body, attempts to uncover it, weeping and angelic shading are explicit. Daughter/sister and spoke/forbade variants stay unresolved as printed; the parenthetic actor gloss and identification of Sufyan\u0027s doubt remain source/transmitter context.'),
 '1299': dict(kind='prophetic_report', speaker='Aisha reporting Prophet Muhammad', note='Separate the Prophetic instructions/Amra\u0027s transmission framing from Aisha\u0027s final own reply. The parenthetic battle identification is source explanation, not an added narration clause. Source spellings and certainty/variant framing are preserved.'),
 '1304': dict(kind='mixed_reports', speaker='Ibn Umar reporting Prophet Muhammad; separately, Umar\u0027s described practice', note='Keep the illness visit, weeping and tongue teaching apart from the separate Umar practice. Parenthetic illness/tongue explanations remain context. Hindi ends after the abbreviated stick-beating statement; do not append Urdu\u0027s stones/dust clauses.'),
 '1306': dict(kind='companion_report', speaker='Umm Atiyya', note='Separate the reported Prophetic pledge against wailing from Umm Atiyya\u0027s later compliance count/list. Preserve both alternative name/groupings; do not label her observation as the Prophet\u0027s words.'),
 '1311': dict(kind='prophetic_report', speaker='Jabir reporting Prophet Muhammad', note='Own field explicitly narrates standing for the funeral, its Jewish identity and the Prophetic instruction. Complete source text is supported.'),
 '1318': dict(kind='prophetic_practice_report', speaker='Abu Hurayra describing Prophet Muhammad', note='Own field explicitly narrates the Najashi death announcement, rows and four takbirs. No absent prayer wording is supplied.'),
 '1319': dict(kind='prophetic_practice_report', speaker='Ibn Abbas, identified in this field\u0027s retained transmitter exchange', note='Select the isolated-grave prayer account and four takbirs. The concluding question identifying the Companion as Ibn Abbas is retained as chain context; it supports attribution without becoming Prophetic speech.'),
 '1322': dict(kind='prophetic_practice_report', speaker='Abdullah ibn Abbas, identified in this field\u0027s retained transmitter exchange', note='Select the complete graveside leadership/rows account. Preserve the concluding identity question and Abu Amr kunya explanation as context. Hindi\u0027s contracted chain is not filled from Urdu.'),
 '1326': dict(kind='prophetic_practice_report', speaker='Ibn Abbas describing Prophet Muhammad', note='The prior-night burial and funeral prayer are explicit. The parenthetic male/female uncertainty is retained in source context; no sex or name is decided.'),
 '1329': dict(kind='prophetic_practice_report', speaker='Ibn Umar describing Prophet Muhammad', note='Own field supplies the Jewish couple\u0027s case, ordered stoning and location beside the funeral-prayer place. Preserve the historical report without legal/authenticity endorsement or added identity.'),
 '1331': dict(kind='prophetic_practice_report', speaker='Samura, as named in this own field', note='The woman\u0027s postpartum death and the Prophet\u0027s standing opposite her middle are explicit. Parenthetic Umm Kab identification is retained as source annotation; do not borrow a fuller narrator name or merge with1332.'),
 '1332': dict(kind='prophetic_practice_report', speaker='Samura ibn Jundab', note='Own field names Samura ibn Jundab and gives the childbirth-death funeral position. The woman remains unnamed; do not import the adjacent field\u0027s parenthetic name.'),
 '1335': dict(kind='companion_report', speaker='Talha reporting Ibn Abbas\u0027s prayer and explanation', note='Keep the first abbreviated chain/account and the second detailed chain/account as separate components. Ibn Abbas says this is the Prophetic way; this is his practice/attribution, not a directly quoted Prophetic utterance. Transmitter alias and loud-reading explanation remain context.'),
 '1336': dict(kind='prophetic_practice_report', speaker='Ibn Abbas, identified in this field\u0027s retained transmitter exchange', note='Select the isolated-grave account and followers\u0027 prayer. The closing Shaybani/al-Shabi question identifying Ibn Abbas is chain context. No neighboring source number supplies text.'),
}

# Each delimiter was selected from the complete own-language field just read.
# Nothing is matched by a generic keyword or inferred from a sibling language.
SPECIAL = {
 '1258': {'hi': {'split': ['और एक दूसरी रिवायत', 'हफ़्सा ने कहा']}, 'ur': {'split': ['اور ایک دوسری روایت', 'حفصہ نے کہا']}},
 '1259': {'hi': {'split': ['और एक दूसरी रिवायत', 'हफ़्सा ने कहा']}, 'ur': {'split': ['اور ایک دوسری روایت', 'حفصہ نے کہا']}},
 '1261': {'hi': {'stop': 'मुझे यह नहीं मालूम'}, 'ur': {'stop': 'مجھے یہ نہیں معلوم'}},
 '1262': {'hi': {'split': ['और वाक़ी ने सुफ़यान']}, 'ur': {'split': ['اور وکیع نے سفیان']}},
 '1268': {'hi': {'stop': '(यानी लब्बैक कहता हुआ उठेगा)'}, 'ur': {'stop': '( یعنی لبیک کہتا ہوا اٹھے گا )'}},
 '1274': {'hi': {'omit': ['(ग़ज़वा-ए-उहुद में)']}, 'ur': {'omit': ['( غزوہ احد میں )']}},
 '1277': {'hi': {'omit_between': [('सहल बिन सअद', 'ख़ैर उस औरत ने कहा')]}, 'ur': {'omit_between': [('سہل بن سعد', 'خیر اس عورت نے کہا')]}},
 '1279': {'hi': {'omit': ['(एक क़िस्म की ज़र्द खुशबु)']}, 'ur': {'omit': ['( ایک قسم کی زرد خوشبو )']}},
 '1283': {'hi': {'omit': ['(ग़बरा कर)', '(माअफ़ फ़रमाइये)', '(अब क्या होता है)']}, 'ur': {'omit': ['( گھبرا کر )', '( معاف فرمائیے )', '( اب کیا ہوتا ہے )']}},
 '1284': {'hi': {'omit': ['(और पानी के टकराने की अंदर से आवाज़ होती है, इसी तरह जानकनी के वक़्त बच्चे के हल्क़ से आवाज़ आ रही थी)', '(नेक)']}, 'ur': {'omit': ['( اور پانی کے ٹکرانے کی اندر سے آواز ہوتی ہے۔ اسی طرح جانکنی کے وقت بچہ کے حلق سے آواز آ رہی تھی )', '( نیک )']}},
 '1293': {'hi': {'omit': ['(मुशरिकों ने)', '(नाम में सुफ़यान को शक हुआ था)']}, 'ur': {'omit': ['( مشرکوں نے )', '( نام میں سفیان کو شک ہوا تھا )']}},
 '1299': {'hi': {'omit': ['(ग़ज़वा-ए-मोटा में)'], 'split': ['इस पर मैं ने कहा']}, 'ur': {'omit': ['( غزوہ موتہ میں )'], 'split': ['اس پر میں نے کہا']}},
 '1304': {'hi': {'omit': ['(उन के मर्ज़ की शिद्दत को देख कर)', '(और अगर इस ज़बान से अछि बात निकले तो)'], 'split': ['उम्र (रज़ियल्लाहु अन्हु) मय्यत पर']}, 'ur': {'omit': ['( ان کے مرض کی شدت کو دیکھ کر )', '( اور اگر اس زبان سے اچھی بات نکلے تو )'], 'split': ['عمر رضی اللہ عنہ میت پر']}},
 '1306': {'hi': {'split': ['लेकिन इस इक़रार']}, 'ur': {'split': ['لیکن اس اقرار']}},
 '1319': {'hi': {'stop': 'मैंने पूछा कि ये हदीस'}, 'ur': {'stop': 'میں نے پوچھا کہ یہ حدیث'}},
 '1322': {'hi': {'stop': 'हम ने पुछा कि'}, 'ur': {'stop': 'ہم نے پوچھا کہ'}},
 '1326': {'hi': {'omit': ['(साहिब-ए-क़ब्र मर्द था या औरत थी)']}, 'ur': {'omit': ['( صاحب قبر مرد تھا یا عورت تھی )']}},
 '1331': {'hi': {'omit': ['(उम्मे काअब)']}, 'ur': {'omit': ['( ام کعب )']}},
 '1335': {'hi': {'omit': ['(मुहम्मद बिन जाफ़र)', '(ज़रा पुकार कर)'], 'split': ['(दूसरी सनद)']}, 'ur': {'omit': ['(محمد بن جعفر)', '( ذرا پکار کر )'], 'split': ['( دوسری سند )']}},
 '1336': {'hi': {'stop': 'शैबानी ने कहा के'}, 'ur': {'stop': 'شیبانی نے کہا کہ'}},
}

COMPONENT_TYPES = {
 '1258': [('prophetic_report', 'Umm Atiyya reporting Prophet Muhammad'), ('prophetic_report', 'Explicit alternate Prophetic washing wording'), ('companion_report', 'Hafsa transmitting Umm Atiyya\u0027s braiding observation')],
 '1259': [('prophetic_report', 'Umm Atiyya reporting Prophet Muhammad'), ('prophetic_report', 'Explicit alternate Prophetic washing wording'), ('companion_report', 'Hafsa transmitting Umm Atiyya\u0027s braiding observation')],
 '1262': [('companion_report', 'Umm Atiyya'), ('companion_report', 'Waki through Sufyan, transmitting the explicit braid-position variant')],
 '1299': [('prophetic_report', 'Aisha reporting Prophet Muhammad, with Amra\u0027s stated transmission framing'), ('companion_report', 'Aisha\u0027s own reply to the messenger')],
 '1304': [('prophetic_report', 'Ibn Umar reporting Prophet Muhammad'), ('companion_report', 'Umar\u0027s separately described practice; Hindi preserves only its supplied abbreviated clause')],
 '1306': [('prophetic_report', 'Umm Atiyya transmitting the Prophetic pledge'), ('companion_report', 'Umm Atiyya\u0027s compliance observation and alternative women\u0027s lists')],
 '1335': [('companion_report', 'Talha\u0027s first abbreviated account of praying behind Ibn Abbas'), ('companion_report', 'Talha\u0027s second account of Ibn Abbas\u0027s recitation and his attribution of the practice to the Prophetic way')],
}
