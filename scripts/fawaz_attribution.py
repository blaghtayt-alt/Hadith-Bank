"""Find explicit report attribution in already bounded provider quotations.

This is an attribution helper, not a publication gate or an authenticity test.
The caller must first verify the provider identity and each language's own source
span, separate compiler material, and apply introduction/ambiguous-subject holds.
No rule uses a book title, grade, array position, or matching reference number.

``explicit_report_evidence(versions)`` accepts the importer's mapping from source
language keys (``ara``, ``eng``, ``urd``, ``ben``) to dictionaries containing a
``quotation`` string. Only that string is searched; raw rows, notes and metadata
are deliberately ignored. It returns one deterministic evidence dictionary or
None. ``span`` is a half-open pair of Unicode character offsets into the exact
input quotation, and ``text`` is exactly quotation[start:end]. Normalization is
for detection only. It never replaces, translates or completes a source text.

Rules cover narrated speech, actions, dhikr, direct encounters and explicit
technical attribution. A bare name, lifetime/possession mention, standalone
Companion saying, or unlinked 'similarly' is insufficient. An expressly
attributed abbreviated transmission remains an excerpt; no counterpart is
inferred and no full matn is synthesized.
"""

from collections.abc import Mapping
import re
import unicodedata


RULE_VERSION = "fawaz-explicit-report-v3"
LANGUAGE_CODES = {"ara": "ar", "eng": "en", "urd": "ur", "ben": "bn"}

# Strip only detection noise, retaining an offset for every surviving character.
# Bengali vowel marks are meaningful and must not be stripped.
ARABIC_MARKS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u0640]")
FORMAT_MARKS = frozenset("\u061c\u200b\u200c\u200d\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069\ufeff")
ARABIC_LETTERS = str.maketrans("أإآىٱ", "ااايا")


def _normalized(text, language):
    characters, offsets = [], []
    for position, original in enumerate(text):
        if ((original in FORMAT_MARKS and not (language == "ben" and original in "\u200c\u200d")) or
                (language in ("ara", "urd") and ARABIC_MARKS.fullmatch(original))):
            continue
        char = original.translate(ARABIC_LETTERS) if language == "ara" else original
        if char.isspace():
            if characters and characters[-1] == " ":
                continue
            char = " "
        characters.append(char)
        offsets.append(position)
    return "".join(characters), offsets


# Terminal word boundaries prevent النبي from matching النبيذ (Nabidh).
AR_NAME = r"(?:رسول\s+الله|النبي|نبي\s+الله)\b(?!\s+(?:موسي|عيسي|ابراهيم|نوح|ادم|يوسف|هود|صالح|لوط|داود|سليمان|يحيي|زكريا)\b)"
AR_START = r"(?<!\w)(?:ف|و)?"
AR_HONOR = (r"(?:\s*[,،()\[\]\-–—]*\s*(?:ﷺ|صلي\s+الله\s+عليه\s+(?:(?:وعلي\s+)?اله\s+)?و\s*سلم|"
            r"عليه\s+(?:الصلاة\s+والسلام|السلام)))?")
AR_JOIN = AR_HONOR + r"\s*[,،()\[\]\-–—]*\s*"

AR_SPEECH = re.compile(
    AR_START + r"(?:حدثنا|حدثني|اخبرنا|اخبرني|انبانا|نبانا|وعظنا|خطبنا|خطبني|خطب|نهانا|نهاني|نهي|امرني|امرنا|"
    r"قضي|حكم|فرض|اذن|بعثني|بعثنا|ارسلني|ارسلنا|تلا|قرا|استغفر)\s+"
    r"(?:(?:لنا|لهم|لي|له|فينا|علينا)\s+)?" + AR_NAME)
AR_ACTION = re.compile(
    AR_START + r"(?:مر|اتي|اتانا|اتاني|اتاه|جاء|جاءنا|جاءني|قدم|بال|شرب|اكل|لبس|مسح|قبل|نام|اضطجع|ركب|سافر|"
    r"صام|افطر|ذبح|ضحي|اعطي|اخذ|ناول|بعث|ارسل|جمع|رمي|طاف|سعي|اشتري|باع|تزوج|طلق|صلي|قام|خرج|دخل|دعا|"
    r"استسقي|استيقظ|رفع|صبح|خطبني|تخلف|وضع|يضع|انصرف|تغيظ|رد|اراد|شبك|اخر|احتجم|حلق|رهن|حرق|عاب|"
    r"حالف|اردفني|صعد|اتخذ|اشتكي|زجر|قنت|رخص|اعتمر|رمل|رجم|ضرب|سمل|تبني)\s+"
    r"(?:(?:بنا|بهم|بي|لي|لنا|علي|علينا|فينا|معنا|عندنا|عنا)\s+)?" + AR_NAME)
AR_ENCOUNTER = re.compile(
    AR_START + r"(?:(?:بايعت|بايعنا|اتيت|اتينا|جئت|جئنا|صحبت|صحبنا|خدمت|خدمنا|سقيت|سقينا|طيبت|التَمست|التمست|اتبعت|اتبعنا)\s+|"
    r"(?:صليت|صلينا|صلي|نصلي|صلوا|صمنا|صمت|خرجنا|خرجت|غزوت|غزونا|حججت|حججنا|اعتمرت|اعتمرنا|"
    r"كنت|كنا|جلست|جلسنا|دخلت|دخلنا|سجدت|سجدنا|اقبلت|اقبلنا)\s+(?:مع|عند|الي|علي|خلف|قدام)\s+|"
    r"(?:كنت|كنا)\s+(?:امشي|نمشي|اسير|نسير|اصلي|نصلي)\s+مع\s+|"
    r"(?:بت|بتنا)\s+(?:(?:ليلة|ليله)\s+)?(?:عند|مع)\s+)" + AR_NAME)
AR_LEARNED_REPORT = re.compile(
    AR_START + r"(?:حفظت|حفظنا|تعلمت|تعلمنا)\s+من\s+" + AR_NAME + AR_JOIN +
    r"(?:[\"«“]\s*[^\s\"»”]+|(?:دع|قل|اتق|احفظ)\b)")
AR_DEMONSTRATED_PRACTICE = re.compile(
    r"(?<!\w)(?:(?:هذا|هكذا)\s+(?:كان\s+)?|(?:اريكم|اريناكم)\s+كيف\s+كان\s+)"
    r"(?:وضوء|طهور|صلاة|صيام)\s+" + AR_NAME)
AR_AFTER = re.compile(
    r"(?<!\w)(?:بينا|بينما|شهدت|شهدنا|لا\s+اعلم|ما\s+علمت|لم\s+تر|لم\s+ار|لم\s+نر|"
    r"سمعت\s+(?:من|صوت)|سمعنا\s+(?:من|صوت))\s+" + AR_NAME + AR_JOIN +
    # An optional honorific must not backtrack and reinterpret its opening
    # صلى as the Prophet performing a prayer: صلى الله عليه وسلم is a blessing.
    r"(?!صلي\s+الله\b)" +
    r"(?:ف?قال|يقول|ف?امر|نهي|صلي|يصلي|صام|يصوم|قرا|يقرا|تلا|دعا|يدعو|ذكر|يذكر|خرج|دخل|مر|قام|جلس|"
    r"جاء|اتانا|اعطاني|اعطانا|بعثني|بعثنا|ارسلني|ارسلنا|ف?اجاب|تبسم|ضحك|بكي)\b")
AR_RESPONSE = re.compile(
    AR_START + r"(?:اتي\s+(?:به|بها|بهم)|اتوا|اتيا|استعدي\s+عليه)\s+" + AR_NAME + AR_JOIN + r"فامر\b")
AR_DHIKR = re.compile(
    r"(?<!\w)(?:(?:ان|كانت?|اكثر)\s+)?(?:تلبية|تلبيه|دعاء|ذكر|استغفار)\s+" + AR_NAME + AR_JOIN +
    r"(?:كانت?|هو|هي)\s*[,،:]*\s*[\"«“]\s*[^\s\"»”]+")
AR_DIALOGUE_START = re.compile(
    AR_START + r"(?:قلت|قلنا|قالت|قالوا|قيل|قال)\b\s*[:،,]*\s*(?:له\s+)?[\"«“]?\s*يا\s+" + AR_NAME)
AR_NEXT_SPEAKER = re.compile(r"(?<!\w)(?:ف?قال|ف?قالت|ف?قالوا)\b")
AR_REPLY = re.compile(r"ف?قال\s*[:،,]*\s*(?:(?:لي|لنا|له|لها|لهم)\s+)?"
                      r"(?:[\"«“]\s*[^\s\"»”]+|(?:نعم|لا|بلي|بل|قل)\b)")
AR_DESCRIPTION_QUESTION = re.compile(
    r"(?<!\w)(?:سالت|سالتها|سئل|سئلت|سالنا|اخبريني|اخبرني)\b[^.؛\n]{0,130}?"
    r"(?:عن\s+|كيف\s+كانت?\s+)(?:صلاة|قراءة|صوم|صيام|دعاء|شعر|شيب|خضاب|خلق|صفة)\s+" + AR_NAME)
AR_DESCRIPTION_REPLY = re.compile(
    r"ف?قالت?\s*[,،:]*\s*(?:[\"«“]\s*)?(?:كانت?|كل|لم|ما|لا|نعم|هو|هي|انه|انها|ثلاث|اربع)\b")
AR_TARGETED_TRANSMISSION = re.compile(
    r"(?<!\w)(?:(?:يرفع|رفع|اسند|يسند|ينمي|نمي)\s+(?:الحديث|هذا\s+الحديث|ذلك)\s+(?:الي\s+)?|"
    r"(?:يرفعه|رفعه|ينميه|نماه)\s+الي\s+|يبلغ\s+به\s+)" + AR_NAME)
AR_TECHNICAL_MARFU = re.compile(
    r"(?<!\w)(?:الحديث|حديث(?:\s+(?:ايوب|الاعمش|سفيان))?|نحو\s+حديث\s+(?:ايوب|الاعمش|سفيان))\s+مرفوعا\b")
AR_VARIANT = re.compile(r"(?<!\w)(?:بمثله|بنحوه|بمعناه|مثله|نحوه|بمثل\s+حديث|نحو\s+حديث|بمعني\s+حديث)\b")
AR_EXPLICIT_ABRIDGEMENT = re.compile(r"(?<!\w)(?:بنحو|بمعني)\s+حديث\s+\S+")

# Finite constructions observed in the retained source queue. These report an
# actual action, instruction or description, including an indirect report. They
# do not use a bare Prophetic name as the evidence and do not assign the whole
# surrounding paragraph to the Prophet as direct speech.
AR_OBJECT_COMMAND = re.compile(
    AR_START + r"(?:امر(?:ه|ها|هم|هن)|نها(?:ه|ها|هم|هن)|علم(?:ني|نا|ه|ها|هم)|"
    r"اوص(?:اني|انا|اه|اها)|حذر(?:ني|نا|ه|ها|هم))\s+" + AR_NAME)
AR_WITNESSED_SERVICE = re.compile(
    AR_START + r"(?:(?:كنت|كنا)\s+(?:اطيب|نطيب|اخدم|نخدم|نبايع|ابايع)\s+|"
    r"(?:رمقت|رمقنا)\s+|(?:كنت|كنا)\s+(?:ارجل|نرجل|اغسل|نغسل)\s+(?:راس|ثوب)\s+|"
    r"ارجل\s+راس\s+)" + AR_NAME)
AR_SHARED_REPORTED_PRACTICE = re.compile(
    AR_START + r"(?:كنت\s+اغتسل\s+انا\s+و\s*|كنا\s+نغزو\s+مع\s+|غزا\s+مع\s+)" + AR_NAME)
AR_WITNESSED_SHARED_WALK = re.compile(
    AR_START + r"رايتني\s+انا\s+و\s*" + AR_NAME + AR_JOIN + r"نتماشي\b")
AR_ADJACENT_PRAYER = re.compile(
    AR_START + r"(?:صليت|صلينا)\s+(?:الي|عن)\s+(?:جنب|يمين|يسار)\s+" + AR_NAME)
AR_QUALIFIED_ENCOUNTER = re.compile(
    r"(?<!\w)(?:انه|انها)\s+كان(?:ت)?\s+مع\s+" + AR_NAME + AR_JOIN +
    r"في\s+(?:سفر|سفرة|غزوة|جنازة)\b")
AR_REPRODUCED_PRACTICE = re.compile(
    AR_START + r"(?:توضا|توضات|توضانا)\s+(?:(?:لهم|لنا)\s+)?وضوء\s+" + AR_NAME)
AR_HEARD_RETROSPECTIVE = re.compile(
    AR_START + r"(?:سمعته|سمعناها|سمعتها|سمعناه|سمعت\s+هذا|سمعت\s+ذلك|سمعت\s+اذناي|سمع\s+اذناي)"
    r"\s+من\s+" + AR_NAME)
AR_PROPHETIC_PLEDGE = re.compile(
    AR_START + r"(?:عهد\s+(?:الي|الينا)\s+" + AR_NAME + r"(?:\s+الامي)?|"
    r"(?:انه\s+)?لعهد\s+" + AR_NAME + r"(?:\s+الامي)?" + AR_JOIN + r"(?:الي|الينا)\b)")
AR_OWNED_PRACTICE = re.compile(
    AR_START + r"كان\s+(?:لرسول\s+الله|للنبي|لنبي\s+الله)\b" + AR_JOIN +
    r"(?:قدح|خاتم|نعلان|فراش|وسادة|حصير|سيف|درع|جبة|قميص)\b")
AR_HABIT_QUESTION = re.compile(
    r"(?<!\w)باي\s+شيء\s+كان\s+يبدا\s+" + AR_NAME + AR_JOIN +
    r"اذا\s+دخل\s+بيته\s*[,،?؟]*\s*ف?قالت?\s*[,،:]*\s*بالسواك\b")
# The same bounded question/answer explicitly establishes the antecedent of
# نهانا; nearby Prophet mentions in an unrelated Companion saying cannot pass.
AR_TAUGHT_AND_PROHIBITED = re.compile(
    r"(?<!\w)(?:قد|لقد)?\s*علمكم\s+نبيكم" + AR_JOIN +
    r"كل\s+شيء\s+حتي\s+الخراءة\s*[.،,]*\s*ف?قال(?:\s+سلمان)?\s*[,،:]*\s*"
    r"اجل\s+(?:لقد\s+)?نهانا\b")
# رفعه قال following a named isnad endpoint is the source's technical raised
# attribution, not a physical act of raising an object. A quote must follow;
# absent wording is never filled from a neighbouring transmission.
AR_ENDPOINT_RAISED = re.compile(
    r"(?<!\w)عن\s+(?:ابي\s+هريرة|ابن\s+عباس|ابن\s+عمر|انس|جابر|عائشة)"
    r"\s*[,،]\s*رفعه\s+قال\s*[\"«“]\s*[^\s\"»”]+")

EN_NAME = (r"\b(?:the\s+(?:Holy\s+)?Prophet(?:\s+of\s+Alla+h)?|(?:the\s+)?(?:Messenger|Apostle)\s+of\s+Alla+h|"
           r"Alla+h['’]s\s+(?:Messenger|Apostle|Prophet))\b"
           r"(?!['’]s\b)"
           r"(?!\s+(?:Moses|Musa|Jesus|Isa|Abraham|Ibrahim|Noah|Adam|David|Solomon)\b)")
EN_SALUTATION = (r"(?:ﷺ|s\.?\s*a\.?\s*w\.?|saws|swas|pbuh|"
                 r"peace\s+(?:and\s+blessings\s+(?:of\s+Alla+h\s+)?)?be\s+upon\s+him|"
                 r"may\s+(?:the\s+)?peace\s+(?:and\s+blessings\s+)?be\s+upon\s+him|"
                 r"sal\s+Alla+hu\s+alayhi\s+wa\s+sallam|"
                 r"may\s+Alla+h\s+bless\s+him\s+and\s+grant\s+him\s+peace)")
EN_HONOR = (r"(?:\s*[,;]?\s*(?:\(\s*" + EN_SALUTATION + r"\s*\)|\[\s*" +
            EN_SALUTATION + r"\s*\]|" + EN_SALUTATION + r"))*")
EN_JOIN = EN_HONOR + r"\s*[,):–—-]?\s*"
EN_PAST = (r"said|says|replied|answered|asked|ordered|forbade|commanded|observed|remarked|told|instructed|enjoined|"
           r"recited|read|prayed|offered|bowed|prostrated|went|came|entered|departed|returned|stood|sat|slept|lay|woke|ate|"
           r"drank|fasted|broke|visited|left|urinated|washed|wiped|performed|took|held|kissed|touched|embraced|married|"
           r"divorced|appointed|decided|ruled|allowed|permitted|forgave|gave|sent|led|delivered|passed|reached|declared|"
           r"proposed|put|taught|laughed|smiled|wept|climbed|mounted|rode|travelled|traveled|invoked|supplicated|"
           r"faced|raised|opened|closed|stopped|started|began|turned|accepted|met|effected\s+separation|"
           r"set\s+out|let\s+(?:her|him|them)\s+(?:choose|chose)")
EN_BASE = (r"say|reply|answer|ask|order|forbid|command|recite|read|pray|offer|bow|prostrate|go|come|enter|return|"
           r"stand|sit|sleep|wake|eat|drink|fast|visit|urinate|wash|wipe|perform|kiss|marry|give|send|lead|teach|"
           r"laugh|smile|weep|invoke|supplicate")
EN_PARTICIPLE = r"saying|praying|reciting|reading|offering|bowing|prostrating|standing|sitting|sleeping|fasting|eating|drinking|weeping|smiling"
EN_PREDICATE = re.compile(
    EN_NAME + EN_JOIN + r"(?:who\s+)?(?:never\s+)?(?:" + EN_PAST + r"|"
    r"(?:had|has)\s+(?:just\s+|already\s+)?(?:" + EN_PAST + r"|forbidden)|"
    r"(?:used\s+to|would|did\s+not)\s+(?:" + EN_BASE + r")|"
    r"(?:was|as)\s+(?:" + EN_PARTICIPLE + r"))\b", re.I)

# These are finite, source-observed action families, not an unrestricted English
# word/verb wildcard.  Adverbs and auxiliaries should not hide an otherwise
# explicit subject.  Nominal/relative-clause objects are rejected separately.
EN_ACTION_ADVERB = (r"(?:(?:then|also|once|always|usually|generally|often|sometimes|"
                    r"only|never|just|still|again|personally|himself|constantly)\s+){0,2}")
EN_ADDITIONAL_PAST = (r"remained|addressed|used(?!\s+to\b)|called|purified|heard|kept|distributed|divided|concluded|"
                      r"conquered|borrowed|lent|bought|sold|stayed|wrote|looked|finished|mentioned|prohibited|"
                      r"separated|disliked|carried|poured|wore|cleaned|removed|paid|informed|granted|"
                      r"proceeded|drew|made|cut|fell|got\s+(?:up|down|off|on)|set\s+(?:out|off|free)")
EN_ADDITIONAL_BASE = (r"put|use|tell|take|pay|leave|pass|keep|deliver|remain|address|purify|do|"
                      r"carry|pour|wear|clean|remove|grant|look|finish|mention|prohibit|distribute|divide|get\s+up")
EN_ADDITIONAL_PARTICIPLE = (r"walking|going|leading|delivering|wearing|performing|using|pouring|"
                            r"washing|wiping|resting|riding|travelling|traveling|fighting|hiding")
EN_REPORTED_ACTION = re.compile(
    EN_NAME + EN_JOIN + EN_ACTION_ADVERB + r"(?:"
    r"(?:" + EN_PAST + r"|" + EN_ADDITIONAL_PAST + r")|"
    r"(?:had|has)\s+" + EN_ACTION_ADVERB + r"(?:" + EN_PAST + r"|" + EN_ADDITIONAL_PAST + r"|seen|forbidden)|"
    r"(?:used\s+to|would|did\s+not|would\s+not)\s+" + EN_ACTION_ADVERB +
    r"(?:" + EN_BASE + r"|" + EN_ADDITIONAL_BASE + r")|"
    r"(?:was|had\s+been)\s+" + EN_ACTION_ADVERB +
    r"(?:" + EN_PARTICIPLE + r"|" + EN_ADDITIONAL_PARTICIPLE + r"|cupped|shrouded|ordered|commanded|informed|given|covered)"
    r")\b", re.I)
EN_ENCOUNTER = re.compile(
    r"\b(?:I|we)\s+(?:had\s+)?(?:(?:heard|saw|accompanied|met|visited|served)\s+|"
    r"(?:prayed|prostrated|fasted|travelled|traveled|went|fought)\s+(?:(?:one|a|that)\s+(?:night|day)\s+|together\s+)?"
    r"(?:with|behind|along\s+with)\s+)" + EN_NAME, re.I)
EN_REPORTED_ENCOUNTER = re.compile(
    r"\b(?:(?:I|we|he|she)\s+(?:had\s+)?(?:saw|heard|accompanied|met|visited|served|followed)\s+|"
    r"(?:I|we)\s+(?:(?:came|went|entered)\s+(?:to|upon)|"
    r"(?:was|were)\s+(?:walking|going|travelling|traveling|praying|sitting|standing|riding)\s+(?:with|behind)|"
    r"spent\s+(?:a|one|the)\s+night\s+with)\s+)" + EN_NAME, re.I)
EN_SHARED_PRACTICE = re.compile(
    r"\b(?:I|we)\s+and\s+" + EN_NAME + EN_JOIN +
    r"were\s+(?:going|walking|travelling|traveling|praying|sitting|standing|riding)\s+together\b", re.I)
EN_LEARNED_REPORT = re.compile(
    r"\b(?:I|we)\s+(?:have\s+|had\s+)?(?:memorised|memorized|learnt|learned|heard)\s+from\s+" + EN_NAME, re.I)
EN_OWNED_PRACTICE = re.compile(
    EN_NAME + EN_JOIN + r"had\s+(?:(?:a|an|the|one|two|three)\s+)?"
    r"(?:cloth|mat|garment|cloak|shirt|sandals|ring|sword|helmet|shield|bed|mattress|cushion|pillow|cup|"
    r"drinking\s+vessel|tooth[ -]stick|supplications)\b", re.I)
EN_PROPERTY_DESCRIPTION = re.compile(
    r"\b(?:the\s+)?(?:hair|beard|complexion|height|face|eyes|teeth|clothing|garment|cloak|shirt|sandals|"
    r"ring|sword|helmet|shield|bed(?:\s+mattress)?|mattress|cushion|pillow|cup|drinking\s+vessel|"
    r"pommel\s+of\s+the\s+sword|inscription\s+on\s+the\s+ring)\s+of\s+" + EN_NAME + EN_JOIN +
    r"(?:was|were|had)\s+(?!not\s+known\b|unknown\b)[\w'‘“]+", re.I)
EN_PREFERENCE = re.compile(
    r"\b(?:the\s+)?(?:drink|food|prayer|fast|day|garment|colour|color)\s+(?:which\s+was\s+)?"
    r"(?:most\s+)?(?:beloved|dearest|pleasing)\s+to\s+" + EN_NAME + EN_JOIN + r"(?:was|were)\s+\w+", re.I)
EN_QUESTION = re.compile(
    r"\b(?:(?:a|an|the)\s+(?:man|woman|person|Bedouin)|I|we)\s+(?:asked|said\s+to)\s+" + EN_NAME + EN_HONOR, re.I)
EN_PERMISSION_REQUEST = re.compile(
    r"\b(?:I|we|he|she)\s+(?:had\s+)?(?:(?:sought|requested|asked\s+for)\s+permission\s+from\s+" +
    EN_NAME + EN_HONOR + r"|asked\s+" + EN_NAME + EN_HONOR + r"\s+for\s+permission\b)", re.I)
EN_PERMISSION_RESPONSE = re.compile(r"\bHe\s+(?:gave|granted)\s+(?:me|us|her|him|them)\s+permission\b", re.I)
EN_DIRECT_MESSAGE = re.compile(
    r"\b(?:mentioned|reported|described)\s+(?:it|this|that|the\s+matter)\s+to\s+" + EN_NAME + EN_HONOR, re.I)
EN_MESSAGE_RESPONSE = re.compile(
    r"\s*[.,;:'’”]*\s*(?:(?:and|so)\s+)?He\s+(?:said|replied|answered|signalled|signaled)\b", re.I)
EN_NEXT_SPEECH = re.compile(r"\b(?:said|replied|answered)\b", re.I)
EN_ATTRIBUTION_QUESTION = re.compile(
    r"\bDid\s+[^?!\n]{1,85}?\s+(?:ascribe|attribute|trace)\s+(?:it|this|(?:the|this)\s+(?:hadith|tradition|report))"
    r"\s+(?:back\s+)?to\s+" + EN_NAME + EN_HONOR + r"\s*\?", re.I)
EN_ATTRIBUTION_YES = re.compile(
    r"\s*[\"'’”.,]*\s*(?:He|She|I)\s+(?:said|replied|answered)\s*[,;:]?\s*[\"'‘“]?\s*Yes\b", re.I)
EN_TRANSMISSION = re.compile(
    r"\b(?:(?:reported|narrated|transmitted|related)\s+(?:it\s+)?(?:directly\s+)?(?:from|on\s+the\s+authority\s+of)|"
    r"attributed\s+(?:it|that|the\s+(?:hadith|tradition|report)|this\s+(?:hadith|tradition|report))\s+to|"
    r"traced\s+(?:it|the\s+(?:hadith|tradition)|this\s+(?:hadith|tradition))\s+(?:back\s+)?to)\s+" + EN_NAME, re.I)
EN_MARFU = re.compile(r"\b(?:this\s+)?hadith\s+(?:has\s+been\s+|was\s+)?(?:narrated|reported|transmitted)\s+as\s+marfu['’]?\b", re.I)
EN_VARIANT = re.compile(r"\b(?:a\s+similar\s+report|the\s+same|similarly|a\s+(?:slight\s+)?variation|mentioned\s+above|as\s+previous)\b", re.I)
EN_ABRIDGED = re.compile(
    r"\b(?:the\s+rest\s+of\s+(?:the\s+|this\s+)?(?:hadith|tradition)|"
    r"(?:mentioned|narrated|transmitted)\s+(?:something\s+similar|a\s+similar\s+report|"
    r"the\s+(?:hadith|tradition)\s+above))\b", re.I)
EN_GENERAL_TRANSMISSION_CLAIM = re.compile(
    r"\bdid\s+not\s+mention\s+(?:it|this|that)\s+in\s+one\s+or\s+two\s+(?:traditions|reports|hadiths)\b", re.I)

UR_NAME = r"(?<!\w)(?:رسول\s+اللہ|نبی\s+(?:کریم|اکرم))"
UR_HONOR = r"\s*(?:صلی\s+اللہ\s+علیہ\s+(?:وآلہ\s+)?و?\s*سلم|ﷺ)?\s*"
UR_ACTION = re.compile(
    UR_NAME + UR_HONOR + r"(?:نے\s+(?:[^۔!?؟\n]{0,90}?\s+)?(?:فرمایا|کہا|ارشاد\s+فرمایا|حکم\s+دیا|منع\s+فرمایا|"
    r"نماز\s+پڑھی|نماز\s+پڑھائی|دعا\s+کی|دعا\s+فرمائی|تلاوت\s+کی|روزہ\s+رکھا|رکوع\s+کیا|سجدہ\s+کیا|وضو\s+کیا|غسل\s+کیا)|"
    r"فرماتے|فرما\s+رہے|تشریف\s+لائے|مسکرائے|(?:ہمارے|ان\s+کے)\s+درمیان\s+کھڑے\s+ہوئے)(?!\w)")

# Evidence pattern audited against the same pinned Bengali editions. Compiler
# note markers must already have been removed by that language's own splitter.
BN_ACTION = re.compile(
    r"(?<![\u0980-\u09ff])(?:রাসূলুল্লাহ্?|রাসুলুল্লাহ্?|নবী|মহানবী|আল্লাহর\s+রাসূল|আল্লাহ্‌র\s+রাসূল)\s*"
    r"(?:(?:সাল্লাল্লাহু\s+[‘’']?আলাইহি\s+(?:ওয়াসাল্লাম|ওয়াসাল্লাম|ওয়া\s+সাল্লাম))|\(সা[ঃ.]?\))?\s*"
    r"(?:বলেছেন|বলেন|বলতেন|বললেন|জিজ্ঞাসা\s+করলেন|উত্তর\s+দিলেন|নিষেধ\s+করেছেন|নিষেধ\s+করলেন|"
    # The source uses Bengali visarga U+0983 as a colon after the predicate
    # (বলেছেনঃ). Permit that punctuation; keep actual word suffixes excluded.
    r"নির্দেশ\s+দিলেন|আদেশ\s+করলেন|করতেন)(?![\u0980-\u0982\u0984-\u09ff])")


def _unsafe_context(text, start, end, language):
    """Reject local counterfactuals and possessive/uncertain subject attribution."""
    before = text[max(0, start - 160):start]
    matched = text[start:end]
    if language == "ara":
        if re.search(r"(?:وددت|وددنا|ليتني|ليتنا|ليت|لو|لان\s+يكون|لا\s+ادري|اراه|احسبه)\b[^.؛\n]{0,150}$", before):
            return True
        # An unanswered question mentioning an action does not assert that the
        # action occurred. Verified question-and-answer rules start earlier and
        # retain the answer inside their own evidence span.
        if re.search(r"(?:هل|اهل|كيف|متي|اين)\s*$", before):
            return True
        # 'Umar, on the Prophet's pulpit, saying ...' has another subject.
        if re.search(r"(?:منبر|عهد|زمن|وقت|قبر|دار|مولى|مولي|صاحب|اصحاب|بنت|زوجة|زوج|ازواج|ابن)\s*$", before):
            return True
        if re.search(r"(?:عن|اعن)\s+(?:النبي|رسول\s+الله)\b.*\bام\s+لا\b", text[max(0, start - 80):end + 120]):
            return True
    elif language == "eng":
        if re.search(r"\b(?:wish(?:ed)?|if|suppose|supposing|perhaps|possibly|whether|would\s+have\s+liked|not\s+sure|do\s+not\s+know|did\s+not\s+know)\b[^.!?\n]{0,140}$", before, re.I):
            return True
        if re.search(r"\b(?:not|never)\s+(?:been\s+)?(?:reported|narrated|attributed|traced)\b", before[-25:] + matched, re.I):
            return True
        if re.search(r"\b(?:grave|pulpit|lifetime|wife|wives|daughter|son|companion)\s+of\s*$", before, re.I):
            return True
        if re.match(EN_NAME, matched, re.I):
            # A nominal owner/object is not the following verb's grammatical
            # subject: 'the herald of the Prophet made an announcement' and
            # 'a man who met the Prophet, wore a ring' are concrete source traps.
            # Explicit encounter/attribution/description rules start before
            # these phrases and can establish their own, differently scoped
            # evidence instead.
            if re.search(r"\b(?:of|to|with|from|by|about|for|near|behind|before|after|beside|"
                         r"towards|toward|alongside|met|saw|heard|visited|served|accompanied|followed)\s*$",
                         before, re.I):
                return True
            if (re.search(r"\b(?:what|how|why)\s*$", before, re.I) and
                    re.search(r"\bwould\b", matched, re.I)):
                return True
    elif language == "urd":
        if re.search(r"(?:کاش|اگر|کیا|معلوم\s+نہیں)\s*(?:کہ\s+)?$", before):
            return True
        # Do not let a later narrator's own verb become the Prophet's predicate.
        first_ne = matched.find("نے")
        if first_ne >= 0 and "نے" in matched[first_ne + 2:]:
            return True
    elif language == "ben":
        if re.search(r"(?:যদি|হয়তো|হয়তো|সম্ভবত|মনে\s+হয়|মনে\s+হয়)\s*$", before):
            return True
    return False


def _evidence(original, normalized, offsets, source_language, start, end, rule, scope="explicit_prophetic_report"):
    if _unsafe_context(normalized, start, end, source_language):
        return None
    begin, finish = offsets[start], offsets[end - 1] + 1
    # Include a final token's trailing original combining marks, without copying
    # text beyond the evidence into an invented normalization.
    while finish < len(original) and unicodedata.combining(original[finish]):
        finish += 1
    return {"rule_version": RULE_VERSION, "rule": rule,
            "language": LANGUAGE_CODES[source_language], "source_language": source_language,
            "span": [begin, finish], "span_unit": "unicode_code_points",
            "text": original[begin:finish], "scope": scope,
            "independent_authenticity_assessment": False}


RULES = {
    "ara": (("arabic_explicit_speech_or_command", AR_SPEECH),
            ("arabic_reported_action", AR_ACTION),
            ("arabic_direct_encounter_or_practice", AR_ENCOUNTER),
            ("arabic_explicit_learned_report", AR_LEARNED_REPORT),
            ("arabic_demonstrated_prophetic_practice", AR_DEMONSTRATED_PRACTICE),
            ("arabic_explicit_named_predicate", AR_AFTER),
            ("arabic_reported_response", AR_RESPONSE),
            ("arabic_attributed_dhikr_formula", AR_DHIKR),
            ("arabic_explicit_transmission_target", AR_TARGETED_TRANSMISSION),
            ("arabic_technical_marfu_report", AR_TECHNICAL_MARFU),
            ("arabic_reported_command_to_person", AR_OBJECT_COMMAND),
            ("arabic_witnessed_service_or_practice", AR_WITNESSED_SERVICE),
            ("arabic_explicit_shared_practice", AR_SHARED_REPORTED_PRACTICE),
            ("arabic_witnessed_shared_walk", AR_WITNESSED_SHARED_WALK),
            ("arabic_reported_adjacent_prayer", AR_ADJACENT_PRAYER),
            ("arabic_qualified_shared_encounter", AR_QUALIFIED_ENCOUNTER),
            ("arabic_reproduced_prophetic_practice", AR_REPRODUCED_PRACTICE),
            ("arabic_retrospective_hearing_attribution", AR_HEARD_RETROSPECTIVE),
            ("arabic_explicit_prophetic_pledge", AR_PROPHETIC_PLEDGE),
            ("arabic_owned_practice_object", AR_OWNED_PRACTICE),
            ("arabic_habit_question_with_reported_answer", AR_HABIT_QUESTION),
            ("arabic_explicit_taught_and_prohibited", AR_TAUGHT_AND_PROHIBITED),
            ("arabic_endpoint_raised_transmission", AR_ENDPOINT_RAISED)),
    "eng": (("english_explicit_named_predicate", EN_PREDICATE),
            ("english_reported_subject_action", EN_REPORTED_ACTION),
            ("english_direct_encounter_or_practice", EN_ENCOUNTER),
            ("english_reported_encounter", EN_REPORTED_ENCOUNTER),
            ("english_explicit_shared_practice", EN_SHARED_PRACTICE),
            ("english_explicit_learned_report", EN_LEARNED_REPORT),
            ("english_owned_practice_object", EN_OWNED_PRACTICE),
            ("english_reported_property_description", EN_PROPERTY_DESCRIPTION),
            ("english_attributed_preference", EN_PREFERENCE),
            ("english_explicit_transmission_target", EN_TRANSMISSION),
            ("english_technical_marfu_report", EN_MARFU)),
    "urd": (("urdu_explicit_named_predicate", UR_ACTION),),
    "ben": (("bengali_explicit_named_predicate", BN_ACTION),),
}


def explicit_report_evidence(versions):
    """Return exact, language-owned evidence from one verified provider group.

    None means these narrow rules did not establish attribution. It does not
    mean 'non-hadith'. Any returned evidence still needs the caller's independent
    quotation-boundary/publication gates. Unknown language keys and absent or
    empty quotation fields contribute no evidence.
    """
    if not isinstance(versions, Mapping):
        return None
    for source_language, rules in RULES.items():
        item = versions.get(source_language)
        original = item.get("quotation") if isinstance(item, Mapping) else None
        if not isinstance(original, str) or not original.strip():
            continue
        normalized, offsets = _normalized(original, source_language)
        for rule, pattern in rules:
            for match in pattern.finditer(normalized):
                if rule == "arabic_retrospective_hearing_attribution":
                    before = normalized[max(0, match.start()-160):match.start()]
                    if (re.search(r"(?:لم|ما|لا|هل|بحديث|حديثا|حديث|شيئا|شيء|كل)\s*$", before) or
                            re.search(r"(?:ل?اظن(?:ه|ها)?|ان\s+كانت?)\b[^.؛\n]{0,145}$", before)):
                        # Abu Dawud1875 explicitly conjectures that the woman
                        # heard it. Nasai1343 first requests a hadith heard by
                        # somebody: its later actual reply needs its own proof.
                        continue
                    original_match = original[offsets[match.start()]:offsets[match.end()-1]+1]
                    if re.search(r"تَ", original_match):
                        # A supplied fatha identifies 'you heard', not 'I
                        # heard'. Muslim7271 is a later conversation about an
                        # unspecified report. Nasai5098's question is followed
                        # by an independently explicit first-person answer.
                        continue
                    if re.search(r"(?:مصحفا|هذه\s+الاية|كيف\s+كان\b[^.؛\n]{0,65}\bيقرا)", normalized[:match.start()]):
                        # The object is Quran/reading-variant material in
                        # Bukhari6278, Malik312 and Tirmidhi2982. Attribution
                        # alone cannot supply the required component boundary.
                        continue
                if (rule == "english_reported_subject_action" and
                        EN_GENERAL_TRANSMISSION_CLAIM.search(normalized[match.start():match.end()+100])):
                    # Abu Dawud4612 is a later writer's general assertion that
                    # reports exist, not a supplied Prophetic quotation/action.
                    continue
                if rule == "english_explicit_learned_report":
                    before = normalized[max(0, match.start()-70):match.start()]
                    # 'I retain anything I heard from him' is a general claim
                    # about transmission, without a specified Prophetic matn.
                    # Other independently explicit acts/responses in the same
                    # bounded source may still qualify through their own rule.
                    if re.search(r"\b(?:anything|everything)\s+(?:(?:that|which)\s+)?$", before, re.I):
                        continue
                scope = "explicit_prophetic_report"
                if rule in ("arabic_demonstrated_prophetic_practice", "english_owned_practice_object",
                            "english_reported_property_description", "arabic_owned_practice_object",
                            "arabic_habit_question_with_reported_answer", "arabic_reproduced_prophetic_practice"):
                    scope = "explicit_prophetic_practice_or_description"
                if source_language == "eng" and EN_ABRIDGED.search(normalized):
                    scope = "source_explicit_abbreviated_report"
                if source_language == "ara" and AR_EXPLICIT_ABRIDGEMENT.search(normalized):
                    scope = "source_explicit_abbreviated_report"
                if "transmission" in rule or "marfu" in rule or "learned_report" in rule:
                    variant = AR_VARIANT if source_language == "ara" else EN_VARIANT
                    if variant.search(normalized) or (rule == "english_technical_marfu_report" and
                            re.fullmatch(r"\s*by\s+another\s+chain\s+of\s+transmitters[.\s]*", normalized[match.end():], re.I)):
                        scope = "source_explicit_abbreviated_report"
                evidence = _evidence(original, normalized, offsets, source_language,
                                     match.start(), match.end(), rule, scope)
                if evidence:
                    return evidence
        if source_language == "ara":
            for addressed in AR_DIALOGUE_START.finditer(normalized):
                # Require the next speaker to be the unnamed direct respondent.
                # '... O Messenger ... Umar said ...' cannot pass this rule.
                following = normalized[addressed.end():addressed.end() + 500]
                first_speaker = AR_NEXT_SPEAKER.search(following)
                if first_speaker:
                    reply = AR_REPLY.match(following, first_speaker.start())
                    if reply:
                        evidence = _evidence(original, normalized, offsets, source_language,
                                             addressed.start(), addressed.end() + reply.end(),
                                             "arabic_address_and_explicit_response")
                        if evidence:
                            return evidence
            for question in AR_DESCRIPTION_QUESTION.finditer(normalized):
                following = normalized[question.end():question.end() + 450]
                first_speaker = AR_NEXT_SPEAKER.search(following)
                if not first_speaker:
                    continue
                reply = AR_DESCRIPTION_REPLY.match(following, first_speaker.start())
                if reply and not re.match(r"ف?قالت?\s*[,،:]*\s*[\"«“]?\s*(?:لا|ما)\s+(?:ادري|اعلم)\b",
                                          following[first_speaker.start():]):
                    evidence = _evidence(original, normalized, offsets, source_language,
                                         question.start(), question.end() + reply.end(),
                                         "arabic_question_and_reported_description",
                                         "explicit_prophetic_practice_or_description")
                    if evidence:
                        return evidence
        if source_language == "eng":
            for message in EN_DIRECT_MESSAGE.finditer(normalized):
                response = EN_MESSAGE_RESPONSE.match(normalized, message.end())
                if response:
                    evidence = _evidence(original, normalized, offsets, source_language,
                                         message.start(), response.end(), "english_direct_message_and_response")
                    if evidence:
                        return evidence
            for request in EN_PERMISSION_REQUEST.finditer(normalized):
                following = normalized[request.end():request.end() + 350]
                response = EN_PERMISSION_RESPONSE.search(following)
                if not response:
                    continue
                # Do not skip an intervening named/other speaker's answer or
                # request to attach a later 'he' to the Prophet.
                if re.search(r"\b(?:said|told|answered|replied|asked|sought|granted|gave|refused)\b",
                             following[:response.start()], re.I):
                    continue
                evidence = _evidence(original, normalized, offsets, source_language,
                                     request.start(), request.end() + response.end(),
                                     "english_permission_request_and_grant")
                if evidence:
                    return evidence
            for question in EN_QUESTION.finditer(normalized):
                following = normalized[question.end():question.end() + 550]
                first_speech = EN_NEXT_SPEECH.search(following)
                if not first_speech:
                    continue
                # The first following response must explicitly be 'He replied'
                # (or said/answered), rather than another named person's speech.
                if not re.search(r"\bHe\s+$", following[:first_speech.start()], re.I):
                    continue
                response = re.match(r"(?:said|replied|answered)\s*[,;:]?\s*[\"'‘“(]?\s*\w+",
                                    following[first_speech.start():], re.I)
                if response:
                    evidence = _evidence(original, normalized, offsets, source_language,
                                         question.start(), question.end() + first_speech.start() + response.end(),
                                         "english_question_and_explicit_response")
                    if evidence:
                        return evidence
            for question in EN_ATTRIBUTION_QUESTION.finditer(normalized):
                if re.search(r"\b(?:not|never|deny|fail)\b", question.group(), re.I):
                    continue
                answer = EN_ATTRIBUTION_YES.match(normalized, question.end())
                if answer:
                    evidence = _evidence(original, normalized, offsets, source_language,
                                         question.start(), answer.end(), "english_explicit_attribution_confirmation")
                    if evidence:
                        return evidence
    return None
