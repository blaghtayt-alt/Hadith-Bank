"""Display-only collection titles; never rewrite source names or record keys.

Prefer an attested title in the selected language, followed by the existing
English label. Use the original Arabic name when no local title is attested.
Evidence and the distinction between collections and attribution groups are
documented in docs/BOOK-TITLES.md.
"""

ENGLISH_TITLES = {
    'hadeethenc': 'HadeethEnc',
    'bukhari': 'Sahih al-Bukhari',
    'muslim': 'Sahih Muslim',
    'abu-dawud': 'Sunan Abi Dawud',
    'tirmidhi': 'Jami al-Tirmidhi',
    'nasai': 'Sunan al-Nasai',
    'ibn-majah': 'Sunan Ibn Majah',
    'ahmad': 'Musnad Ahmad',
    'malik': 'Muwatta Malik',
    'darimi': 'Sunan al-Darimi',
    'ibn-hibban': 'Sahih Ibn Hibban',
    'adab-al-mufrad': 'Al-Adab al-Mufrad',
    'hisn-al-muslim': 'Hisn al-Muslim',
    'mishkat-al-masabih': 'Mishkat al-Masabih',
    'tabarani': 'Al-Tabarani',
    'hakim': 'Al-Hakim',
    '200-golden-hadith': '200 Golden Hadith',
    'targhib-wa-tarhib': 'Al-Targhib wa-l-Tarhib (Sahih and Daif)',
    'riyadh-al-salihin': 'Riyadh al-Salihin',
    'shengxunjing': 'Shengxunjing',
    'unclassified': 'Collection not established',
}

BOOK_ALIASES = {'al-nasai': 'nasai', 'riyad-as-salihin': 'riyadh-al-salihin'}
LANGUAGE_ALIASES = {'zh': 'zh-CN', 'zh-Hans': 'zh-CN', 'fa-IR': 'fa',
                    'tl': 'fil', 'uz-Cyrl': 'uz'}

ORIGINAL_TITLES = {
    'bukhari': 'صحيح البخاري', 'muslim': 'صحيح مسلم',
    'abu-dawud': 'سنن أبي داود', 'tirmidhi': 'جامع الترمذي',
    'nasai': 'سنن النسائي', 'ibn-majah': 'سنن ابن ماجه',
    'ahmad': 'مسند أحمد', 'malik': 'موطأ مالك', 'darimi': 'سنن الدارمي',
    'adab-al-mufrad': 'الأدب المفرد', 'hisn-al-muslim': 'حصن المسلم',
    'mishkat-al-masabih': 'مشكاة المصابيح',
    'targhib-wa-tarhib': 'الترغيب والترهيب',
    'riyadh-al-salihin': 'رياض الصالحين',
    # These keys also contain source attribution groups. Do not infer a more
    # specific Arabic work from a compiler's name.
    'ibn-hibban': 'ابن حبان', 'tabarani': 'الطبراني', 'hakim': 'الحاكم',
}

LOCAL_TITLES = {'zh-CN': {'bukhari': '布哈里圣训实录',
           'muslim': '穆斯林圣训实录',
           'abu-dawud': '艾布·达吾德圣训集',
           'tirmidhi': '提尔米兹圣训集',
           'nasai': '奈萨仪圣训集',
           'ibn-majah': '伊本·马哲圣训集',
           'ahmad': '艾哈迈德圣训集',
           'malik': '穆宛塔圣训集',
           'adab-al-mufrad': '道德箴言集',
           'hisn-al-muslim': '穆斯林的堡垒',
           'hadeethenc': '圣训翻译百科全书',
           'unclassified': '未确定典籍'},
 'ja': {'bukhari': 'サヒーフ・アル＝ブハーリー',
        'muslim': 'サヒーフ・ムスリム',
        'ahmad': 'ムスナド・アフマド',
        'hisn-al-muslim': 'ムスリムの砦',
        'unclassified': '出典未特定',
        'abu-dawud': 'スナン・アブー・ダーウード',
        'tirmidhi': 'スナン・アッ＝ティルミズィー',
        'ibn-majah': 'スナン・イブン・マージャ',
        'adab-al-mufrad': 'アル＝アダブ・アル＝ムフラド',
        'mishkat-al-masabih': 'ミシカート アルマサビーハ'},
 'fa': {'bukhari': 'صحیح البخاری',
        'muslim': 'صحیح مسلم',
        'riyadh-al-salihin': 'ریاض الصالحین',
        'targhib-wa-tarhib': 'ترغیب و ترهیب',
        'unclassified': 'مجموعه مشخص نشده',
        'abu-dawud': 'سنن ابی\u200cداوود',
        'ibn-majah': 'سنن ابن\u200cماجه',
        'ahmad': 'مُسنَد احمد',
        'tirmidhi': 'سنن ترمذی',
        'adab-al-mufrad': 'الأدب المفرد'},
 'hi': {'muslim': 'सहीह मुस्लिम',
        'unclassified': 'संग्रह की पहचान नहीं हुई',
        'bukhari': 'सह़ीह़ बुख़ारी',
        'abu-dawud': 'सुनन अबू दावूद',
        'tirmidhi': 'सुनन तिर्मिज़ी',
        'ibn-majah': 'सुनन इब्ने माजह',
        'ahmad': 'मुसनद अह़मद',
        'adab-al-mufrad': 'अल-अदब अल-मुफ़रद',
        'hisn-al-muslim': 'हिस्नुल्-मुस्लिम'},
 'uz': {'bukhari': 'Саҳиҳ ал-Бухорий',
        'muslim': 'Саҳиҳ Муслим',
        'tirmidhi': 'Жомеъ ат-Термизий',
        'riyadh-al-salihin': 'Риёзус-солиҳийн',
        'unclassified': 'Тўплам аниқланмаган',
        'abu-dawud': 'Сунани Абу Довуд',
        'ibn-majah': 'Сунани Ибн Можа',
        'ahmad': 'Муснади Аҳмад',
        'adab-al-mufrad': 'Ал-Адаб ал-Муфрад'},
 'vi': {'200-golden-hadith': 'HAI TRĂM HADITH VÀNG CỦA NABI MUHAMMAD',
        'unclassified': 'Chưa xác định bộ sưu tập',
        'riyadh-al-salihin': 'Những Ngôi Vườn Của Những Người Ngoan Đạo',
        'hisn-al-muslim': 'حصن المسلم'},
 'fil': {'unclassified': 'Hindi natukoy ang koleksiyon', 'hisn-al-muslim': 'KUTANG-TANGGULAN NG MUSLIM'}}


# Exact publisher catalogue display labels; these do not merge book identities.
SOURCE_COLLECTION_TITLES = {
    "abdurrazzoq": "Musannaf Abdurrazzoq",
    "abu-dovud": "Sunan Abu Dovud",
    "adab": "Al-Adab al-mufrad",
    "bayhaqiy": "As-Sunan al-Kubro (Bayhaqiy)",
    "bulugh": "Bulugʻ ul-marom",
    "buxoriy": "Sahih al-Buxoriy",
    "doraqutniy": "Sunan ad-Doraqutniy",
    "dorimiy": "Sunan ad-Dorimiy",
    "fazilatlar": "Qurʼon suralarining fazilatlari",
    "hisn": "Hisn ul-muslim",
    "hokim": "Mustadrak al-Hokim",
    "ibn-abu-shayba": "Musannaf Ibn Abu Shayba",
    "ibn-hibbon": "Sahih Ibn Hibbon",
    "ibn-moja": "Sunan Ibn Moja",
    "ibn-xuzayma": "Sahih Ibn Xuzayma",
    "mishkot": "Mishkot ul-masobih",
    "muvatto": "Muvatto Molik",
    "nasoiy": "Sunan an-Nasoiy",
    "nasoiy-kubro": "As-Sunan al-Kubro (Nasoiy)",
    "qirq": "Qirq hadis toʻplamlari",
    "riyoz": "Riyoz us-solihin",
    "shamoil": "Shamoili Muhammadiya",
    "sulosiyot": "Sulosiyot",
    "termiziy": "Jomeʼ at-Termiziy",
    "book-17": "Ал-Азкор",
    "book-22": "101 ҳадис",
    "book-23": "2002 ҳадис",
    "book-24": "Арбаъин",
    "book-25": "Шамоилул-Муҳаммадия",
    "book-26": "Саҳиҳул Бухорийнинг мухтасари",
    "book-27": "Имомлари иттифоқ қилган ҳадислар",
    "book-28": "Риёзус солиҳийн",
    "book-29": "Риёзус солиҳийн (болалар учун)",
    "book-30": "Забидий",
    "book-32": "Риёзус солиҳийн шарҳи"
}


def book_label(key, language='', english=None):
    """Return a plain-text label without changing a collection's identity."""
    canonical = BOOK_ALIASES.get(key, key)
    label = english if english is not None else ENGLISH_TITLES.get(canonical, SOURCE_COLLECTION_TITLES.get(key, key))
    language = LANGUAGE_ALIASES.get(language, language)
    if not language or language.split('-', 1)[0] == 'en':
        return label
    native = LOCAL_TITLES.get(language, {}).get(canonical) or ORIGINAL_TITLES.get(canonical)
    return native + ' — ' + label if native and native.casefold() != label.casefold() else label


def title_metadata():
    """Embed the same resolved labels in the online and offline readers."""
    keys = sorted(set(ENGLISH_TITLES) | set(BOOK_ALIASES) | set(SOURCE_COLLECTION_TITLES))
    languages = ['', 'en', 'ar', *LOCAL_TITLES, *LANGUAGE_ALIASES]
    return {language: {key: book_label(key, language) for key in keys}
            for language in languages}
