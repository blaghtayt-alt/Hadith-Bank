"""Pinned source regressions and synthetic fixtures; TEST text is not a religious quotation."""
import argparse
import copy
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import import_fawaz_bulk as importer
from material_registry import load_public_materials
from language_display import language_readings


# Exact source quotations from the pinned provider revision. Their complete
# source field hashes and original offsets identify these real regression cases.
# Only fixtures explicitly prefixed TEST elsewhere are synthetic.
ACTUAL_SUBJECT_REGRESSIONS = [{'book': 'abudawud',
  'id': '3669',
  'expected': 'held',
  'quotations': {'ara': 'حَدَّثَنَا أَحْمَدُ بْنُ حَنْبَلٍ، حَدَّثَنَا إِسْمَاعِيلُ بْنُ إِبْرَاهِيمَ، حَدَّثَنَا '
                        'أَبُو حَيَّانَ، حَدَّثَنِي الشَّعْبِيُّ، عَنِ ابْنِ عُمَرَ، عَنْ عُمَرَ، قَالَ نَزَلَ '
                        'تَحْرِيمُ الْخَمْرِ يَوْمَ نَزَلَ وَهِيَ مِنْ خَمْسَةِ أَشْيَاءَ مِنَ الْعِنَبِ وَالتَّمْرِ '
                        'وَالْعَسَلِ وَالْحِنْطَةِ وَالشَّعِيرِ وَالْخَمْرُ مَا خَامَرَ الْعَقْلَ وَثَلاَثٌ وَدِدْتُ '
                        'أَنَّ رَسُولَ اللَّهِ صلى الله عليه وسلم لَمْ يُفَارِقْنَا حَتَّى يَعْهَدَ إِلَيْنَا فِيهِنَّ '
                        'عَهْدًا نَنْتَهِي إِلَيْهِ الْجَدُّ وَالْكَلاَلَةُ وَأَبْوَابٌ مِنْ أَبْوَابِ الرِّبَا '
                        '\u200f.\u200f',
                 'ben': '। উমার (রাঃ) সূত্রে বর্ণিত। তিনি বলেন, মদ হারাম হওয়ার বিধান যেদিন অবতীর্ণ হলো তখন তা পাঁচটি '
                        'জিনিস থেকে তৈরী করা হতো; আঙ্গুর, খেজুর, মধু, গম ও বার্লি। মদ সেই পানীয় যা মানুষকে জ্ঞানশূন্য '
                        'করে দেয়। তিনটি বিষয় সম্পর্কে আমি আশা করেছিলাম, তা সুস্পষ্টভাবে আমাদের নিকট বর্ণনা না করা '
                        'পর্যন্ত যদি নবী সাল্লাল্লাহু আলাইহি ওয়াসাল্লাম আমাদের থেকে বিদায় না নিতেন! সেগুলো হলো, দাদার '
                        'মীরাস, কালালার ব্যাখ্যা ও সুদের কিছু বিষয়।[1] সহীহ।',
                 'eng': '’Umar said :The prohibition of wine came down when (the Quranic verse ) came down. It was '
                        'made from five thing namely, grapes, dates, honey, wheat ,barley. Wine is what infects '
                        '(khamara) the mind. There are three things I wished that the prophet (ﷺ) would not leave us '
                        'until he explained them fully to our satisfaction: (share of) grandfather, one who leaves no '
                        'descendants or ascendants as hairs, and the details of usury',
                 'urd': 'عمر رضی اللہ عنہ کہتے ہیں کہ شراب کی حرمت نازل ہوئی تو اس وقت شراب پانچ چیزوں: انگور، کھجور، '
                        'شہد، گیہوں اور جو سے بنتی تھی، اور شراب وہ ہے جو عقل کو ڈھانپ لے، اور تین باتیں ایسی ہیں کہ '
                        'میری خواہش تھی کہ رسول اللہ صلی اللہ علیہ وسلم ہم سے جدا نہ ہوں جب تک کہ آپ انہیں ہم سے اچھی '
                        'طرح بیان نہ کر دیں: ایک دادا کا حصہ، دوسرے کلالہ کا معاملہ اور تیسرے سود کے کچھ مسائل۔'},
  'source_evidence': {'ara': {'json_pointer': '/hadiths/3668/text',
                              'original_text_sha256': '2cdaba27f42e2339df14dc15b115410ae37e0b462de2a725b6d8ac6190dbfc48',
                              'quotation_spans': [[0, 543]]},
                      'ben': {'json_pointer': '/hadiths/3668/text',
                              'original_text_sha256': '83481141d3b9919485aa8bafac4d1b76ec8914893cca7be0bef5b59a7fcd9b10',
                              'quotation_spans': [[0, 418]]},
                      'eng': {'json_pointer': '/hadiths/3668/text',
                              'original_text_sha256': 'c31e4d763d297e3d4a64cec7ce3ee53ac2200f41938863b455cb2dcbb754e1ec',
                              'quotation_spans': [[0, 422]]},
                      'urd': {'json_pointer': '/hadiths/3668/text',
                              'original_text_sha256': 'bce5568f4bd377bcdd29b817c44658b143efdc2ed9ba43c479c7b5a04217a826',
                              'quotation_spans': [[0, 364]]}}},
 {'book': 'abudawud',
  'id': '4985',
  'expected': 'hadith',
  'quotations': {'ara': 'حَدَّثَنَا مُسَدَّدٌ، حَدَّثَنَا عِيسَى بْنُ يُونُسَ، حَدَّثَنَا مِسْعَرُ بْنُ كِدَامٍ، عَنْ '
                        'عَمْرِو بْنِ مُرَّةَ، عَنْ سَالِمِ بْنِ أَبِي الْجَعْدِ، قَالَ قَالَ رَجُلٌ - قَالَ مِسْعَرٌ '
                        'أُرَاهُ مِنْ خُزَاعَةَ - لَيْتَنِي صَلَّيْتُ فَاسْتَرَحْتُ فَكَأَنَّهُمْ عَابُوا عَلَيْهِ '
                        'ذَلِكَ فَقَالَ سَمِعْتُ رَسُولَ اللَّهِ صلى الله عليه وسلم يَقُولُ \u200f "\u200f يَا بِلاَلُ '
                        'أَقِمِ الصَّلاَةَ أَرِحْنَا بِهَا \u200f"\u200f \u200f.\u200f',
                 'eng': "Narrated A man: Salim ibn AbulJa'dah said: A man said: (Mis'ar said: I think he was from the "
                        "tribe of Khuza'ah): would that I had prayed, and got comfort. The people objected to him for "
                        'it. Thereupon he said: I heard the Messenger of Allah (ﷺ) as saying: O Bilal, call iqamah for '
                        'prayer: give us comfort by it'},
  'source_evidence': {'ara': {'json_pointer': '/hadiths/4984/text',
                              'original_text_sha256': '3424414a31dc9b221b24e7f8ab9061bf32ae43c57432798caf822805752720fd',
                              'quotation_spans': [[0, 401]]},
                      'eng': {'json_pointer': '/hadiths/4984/text',
                              'original_text_sha256': 'ed026ac08064178e645e6605fec95f37ea1c3d5e643bd6d0922efdd54e98ced4',
                              'quotation_spans': [[0, 309]]}}},
 {'book': 'bukhari',
  'id': '3',
  'expected': 'hadith',
  'quotations': {'ara': 'حَدَّثَنَا يَحْيَى بْنُ بُكَيْرٍ، قَالَ حَدَّثَنَا اللَّيْثُ، عَنْ عُقَيْلٍ، عَنِ ابْنِ '
                        'شِهَابٍ، عَنْ عُرْوَةَ بْنِ الزُّبَيْرِ، عَنْ عَائِشَةَ أُمِّ الْمُؤْمِنِينَ، أَنَّهَا '
                        'قَالَتْ أَوَّلُ مَا بُدِئَ بِهِ رَسُولُ اللَّهِ صلى الله عليه وسلم مِنَ الْوَحْىِ الرُّؤْيَا '
                        'الصَّالِحَةُ فِي النَّوْمِ، فَكَانَ لاَ يَرَى رُؤْيَا إِلاَّ جَاءَتْ مِثْلَ فَلَقِ الصُّبْحِ، '
                        'ثُمَّ حُبِّبَ إِلَيْهِ الْخَلاَءُ، وَكَانَ يَخْلُو بِغَارِ حِرَاءٍ فَيَتَحَنَّثُ فِيهِ ـ '
                        'وَهُوَ التَّعَبُّدُ ـ اللَّيَالِيَ ذَوَاتِ الْعَدَدِ قَبْلَ أَنْ يَنْزِعَ إِلَى أَهْلِهِ، '
                        'وَيَتَزَوَّدُ لِذَلِكَ، ثُمَّ يَرْجِعُ إِلَى خَدِيجَةَ، فَيَتَزَوَّدُ لِمِثْلِهَا، حَتَّى '
                        'جَاءَهُ الْحَقُّ وَهُوَ فِي غَارِ حِرَاءٍ، فَجَاءَهُ الْمَلَكُ فَقَالَ اقْرَأْ\u200f.\u200f '
                        'قَالَ \u200f"\u200f مَا أَنَا بِقَارِئٍ \u200f"\u200f\u200f.\u200f قَالَ \u200f"\u200f '
                        'فَأَخَذَنِي فَغَطَّنِي حَتَّى بَلَغَ مِنِّي الْجَهْدَ، ثُمَّ أَرْسَلَنِي فَقَالَ '
                        'اقْرَأْ\u200f.\u200f قُلْتُ مَا أَنَا بِقَارِئٍ\u200f.\u200f فَأَخَذَنِي فَغَطَّنِي '
                        'الثَّانِيَةَ حَتَّى بَلَغَ مِنِّي الْجَهْدَ، ثُمَّ أَرْسَلَنِي فَقَالَ اقْرَأْ\u200f.\u200f '
                        'فَقُلْتُ مَا أَنَا بِقَارِئٍ\u200f.\u200f فَأَخَذَنِي فَغَطَّنِي الثَّالِثَةَ، ثُمَّ '
                        'أَرْسَلَنِي فَقَالَ \u200f{\u200fاقْرَأْ بِاسْمِ رَبِّكَ الَّذِي خَلَقَ * خَلَقَ الإِنْسَانَ '
                        'مِنْ عَلَقٍ * اقْرَأْ وَرَبُّكَ الأَكْرَمُ\u200f}\u200f \u200f"\u200f\u200f.\u200f فَرَجَعَ '
                        'بِهَا رَسُولُ اللَّهِ صلى الله عليه وسلم يَرْجُفُ فُؤَادُهُ، فَدَخَلَ عَلَى خَدِيجَةَ بِنْتِ '
                        'خُوَيْلِدٍ رضى الله عنها فَقَالَ \u200f"\u200f زَمِّلُونِي زَمِّلُونِي '
                        '\u200f"\u200f\u200f.\u200f فَزَمَّلُوهُ حَتَّى ذَهَبَ عَنْهُ الرَّوْعُ، فَقَالَ لِخَدِيجَةَ '
                        'وَأَخْبَرَهَا الْخَبَرَ \u200f"\u200f لَقَدْ خَشِيتُ عَلَى نَفْسِي \u200f"\u200f\u200f.\u200f '
                        'فَقَالَتْ خَدِيجَةُ كَلاَّ وَاللَّهِ مَا يُخْزِيكَ اللَّهُ أَبَدًا، إِنَّكَ لَتَصِلُ '
                        'الرَّحِمَ، وَتَحْمِلُ الْكَلَّ، وَتَكْسِبُ الْمَعْدُومَ، وَتَقْرِي الضَّيْفَ، وَتُعِينُ عَلَى '
                        'نَوَائِبِ الْحَقِّ\u200f.\u200f فَانْطَلَقَتْ بِهِ خَدِيجَةُ حَتَّى أَتَتْ بِهِ وَرَقَةَ بْنَ '
                        'نَوْفَلِ بْنِ أَسَدِ بْنِ عَبْدِ الْعُزَّى ابْنَ عَمِّ خَدِيجَةَ ـ وَكَانَ امْرَأً تَنَصَّرَ '
                        'فِي الْجَاهِلِيَّةِ، وَكَانَ يَكْتُبُ الْكِتَابَ الْعِبْرَانِيَّ، فَيَكْتُبُ مِنَ الإِنْجِيلِ '
                        'بِالْعِبْرَانِيَّةِ مَا شَاءَ اللَّهُ أَنْ يَكْتُبَ، وَكَانَ شَيْخًا كَبِيرًا قَدْ عَمِيَ ـ '
                        'فَقَالَتْ لَهُ خَدِيجَةُ يَا ابْنَ عَمِّ اسْمَعْ مِنَ ابْنِ أَخِيكَ\u200f.\u200f فَقَالَ لَهُ '
                        'وَرَقَةُ يَا ابْنَ أَخِي مَاذَا تَرَى فَأَخْبَرَهُ رَسُولُ اللَّهِ صلى الله عليه وسلم خَبَرَ '
                        'مَا رَأَى\u200f.\u200f فَقَالَ لَهُ وَرَقَةُ هَذَا النَّامُوسُ الَّذِي نَزَّلَ اللَّهُ عَلَى '
                        'مُوسَى صلى الله عليه وسلم يَا لَيْتَنِي فِيهَا جَذَعًا، لَيْتَنِي أَكُونُ حَيًّا إِذْ '
                        'يُخْرِجُكَ قَوْمُكَ\u200f.\u200f فَقَالَ رَسُولُ اللَّهِ صلى الله عليه وسلم \u200f"\u200f '
                        'أَوَمُخْرِجِيَّ هُمْ \u200f"\u200f\u200f.\u200f قَالَ نَعَمْ، لَمْ يَأْتِ رَجُلٌ قَطُّ '
                        'بِمِثْلِ مَا جِئْتَ بِهِ إِلاَّ عُودِيَ، وَإِنْ يُدْرِكْنِي يَوْمُكَ أَنْصُرْكَ نَصْرًا '
                        'مُؤَزَّرًا\u200f.\u200f ثُمَّ لَمْ يَنْشَبْ وَرَقَةُ أَنْ تُوُفِّيَ وَفَتَرَ '
                        'الْوَحْىُ\u200f.\u200f',
                 'eng': "Narrated 'Aisha (the mother of the faithful believers):The commencement of the Divine "
                        "Inspiration to Allah's Messenger (ﷺ) was in the form of good dreams which came true like "
                        'bright daylight, and then the love of seclusion was bestowed upon him. He used to go in '
                        'seclusion in the cave of Hira where he used to worship (Allah alone) continuously for many '
                        'days before his desire to see his family. He used to take with him the journey food for the '
                        'stay and then come back to (his wife) Khadija to take his food likewise again till suddenly '
                        'the Truth descended upon him while he was in the cave of Hira. The angel came to him and '
                        'asked him to read. The Prophet (ﷺ) replied, "I do not know how to read." The Prophet (ﷺ) '
                        'added, "The angel caught me (forcefully) and pressed me so hard that I could not bear it any '
                        "more. He then released me and again asked me to read and I replied, 'I do not know how to "
                        "read.' Thereupon he caught me again and pressed me a second time till I could not bear it any "
                        "more. He then released me and again asked me to read but again I replied, 'I do not know how "
                        "to read (or what shall I read)?' Thereupon he caught me for the third time and pressed me, "
                        "and then released me and said, 'Read in the name of your Lord, who has created (all that "
                        'exists), created man from a clot. Read! And your Lord is the Most Generous." (96.1, 96.2, '
                        "96.3) Then Allah's Messenger (ﷺ) returned with the Inspiration and with his heart beating "
                        'severely. Then he went to Khadija bint Khuwailid and said, "Cover me! Cover me!" They covered '
                        'him till his fear was over and after that he told her everything that had happened and said, '
                        '"I fear that something may happen to me." Khadija replied, "Never! By Allah, Allah will never '
                        'disgrace you. You keep good relations with your kith and kin, help the poor and the '
                        'destitute, serve your guests generously and assist the deserving calamity-afflicted ones." '
                        "Khadija then accompanied him to her cousin Waraqa bin Naufal bin Asad bin 'Abdul 'Uzza, who, "
                        'during the pre-Islamic Period became a Christian and used to write the writing with Hebrew '
                        'letters. He would write from the Gospel in Hebrew as much as Allah wished him to write. He '
                        'was an old man and had lost his eyesight. Khadija said to Waraqa, "Listen to the story of '
                        'your nephew, O my cousin!" Waraqa asked, "O my nephew! What have you seen?" Allah\'s '
                        'Messenger (ﷺ) described whatever he had seen. Waraqa said, "This is the same one who keeps '
                        'the secrets (angel Gabriel) whom Allah had sent to Moses. I wish I were young and could live '
                        'up to the time when your people would turn you out." Allah\'s Messenger (ﷺ) asked, "Will they '
                        'drive me out?" Waraqa replied in the affirmative and said, "Anyone (man) who came with '
                        'something similar to what you have brought was treated with hostility; and if I should remain '
                        'alive till the day when you will be turned out then I would support you strongly." But after '
                        'a few days Waraqa died and the Divine Inspiration was also paused for a while'},
  'source_evidence': {'ara': {'json_pointer': '/hadiths/2/text',
                              'original_text_sha256': 'b20de2142c81ea0ec3984cd0ad768f64ec6e6bc9798127b1ca4d841fc6120c4d',
                              'quotation_spans': [[0, 2689]]},
                      'eng': {'json_pointer': '/hadiths/2/text',
                              'original_text_sha256': 'a11d1645b7838c4b6a14030f7ca0005101ddb2d61e0f567e0a1848f11d44779e',
                              'quotation_spans': [[0, 2979]]}}},
 {'book': 'bukhari',
  'id': '425',
  'expected': 'hadith',
  'quotations': {'ara': 'حَدَّثَنَا سَعِيدُ بْنُ عُفَيْرٍ، قَالَ حَدَّثَنِي اللَّيْثُ، قَالَ حَدَّثَنِي عُقَيْلٌ، عَنِ '
                        'ابْنِ شِهَابٍ، قَالَ أَخْبَرَنِي مَحْمُودُ بْنُ الرَّبِيعِ الأَنْصَارِيُّ، أَنَّ عِتْبَانَ '
                        'بْنَ مَالِكٍ ـ وَهُوَ مِنْ أَصْحَابِ رَسُولِ اللَّهِ صلى الله عليه وسلم مِمَّنْ شَهِدَ '
                        'بَدْرًا مِنَ الأَنْصَارِ ـ أَنَّهُ أَتَى رَسُولَ اللَّهِ صلى الله عليه وسلم فَقَالَ يَا '
                        'رَسُولَ اللَّهِ، قَدْ أَنْكَرْتُ بَصَرِي، وَأَنَا أُصَلِّي لِقَوْمِي، فَإِذَا كَانَتِ '
                        'الأَمْطَارُ سَالَ الْوَادِي الَّذِي بَيْنِي وَبَيْنَهُمْ، لَمْ أَسْتَطِعْ أَنْ آتِيَ '
                        'مَسْجِدَهُمْ فَأُصَلِّيَ بِهِمْ، وَوَدِدْتُ يَا رَسُولَ اللَّهِ أَنَّكَ تَأْتِينِي '
                        'فَتُصَلِّيَ فِي بَيْتِي، فَأَتَّخِذَهُ مُصَلًّى\u200f.\u200f قَالَ فَقَالَ لَهُ رَسُولُ '
                        'اللَّهِ صلى الله عليه وسلم \u200f"\u200f سَأَفْعَلُ إِنْ شَاءَ اللَّهُ '
                        '\u200f"\u200f\u200f.\u200f قَالَ عِتْبَانُ فَغَدَا رَسُولُ اللَّهِ صلى الله عليه وسلم وَأَبُو '
                        'بَكْرٍ حِينَ ارْتَفَعَ النَّهَارُ، فَاسْتَأْذَنَ رَسُولُ اللَّهِ صلى الله عليه وسلم '
                        'فَأَذِنْتُ لَهُ، فَلَمْ يَجْلِسْ حَتَّى دَخَلَ الْبَيْتَ ثُمَّ قَالَ \u200f"\u200f أَيْنَ '
                        'تُحِبُّ أَنْ أُصَلِّيَ مِنْ بَيْتِكَ \u200f"\u200f\u200f.\u200f قَالَ فَأَشَرْتُ لَهُ إِلَى '
                        'نَاحِيَةٍ مِنَ الْبَيْتِ، فَقَامَ رَسُولُ اللَّهِ صلى الله عليه وسلم فَكَبَّرَ، فَقُمْنَا '
                        'فَصَفَّنَا، فَصَلَّى رَكْعَتَيْنِ ثُمَّ سَلَّمَ، قَالَ وَحَبَسْنَاهُ عَلَى خَزِيرَةٍ '
                        'صَنَعْنَاهَا لَهُ\u200f.\u200f قَالَ فَثَابَ فِي الْبَيْتِ رِجَالٌ مِنْ أَهْلِ الدَّارِ ذَوُو '
                        'عَدَدٍ فَاجْتَمَعُوا، فَقَالَ قَائِلٌ مِنْهُمْ أَيْنَ مَالِكُ بْنُ الدُّخَيْشِنِ أَوِ ابْنُ '
                        'الدُّخْشُنِ فَقَالَ بَعْضُهُمْ ذَلِكَ مُنَافِقٌ لاَ يُحِبُّ اللَّهَ وَرَسُولَهُ\u200f.\u200f '
                        'فَقَالَ رَسُولُ اللَّهِ صلى الله عليه وسلم \u200f"\u200f لاَ تَقُلْ ذَلِكَ، أَلاَ تَرَاهُ '
                        'قَدْ قَالَ لاَ إِلَهَ إِلاَّ اللَّهُ\u200f.\u200f يُرِيدُ بِذَلِكَ وَجْهَ اللَّهِ '
                        '\u200f"\u200f\u200f.\u200f قَالَ اللَّهُ وَرَسُولُهُ أَعْلَمُ\u200f.\u200f قَالَ فَإِنَّا '
                        'نَرَى وَجْهَهُ وَنَصِيحَتَهُ إِلَى الْمُنَافِقِينَ\u200f.\u200f قَالَ رَسُولُ اللَّهِ صلى '
                        'الله عليه وسلم \u200f"\u200f فَإِنَّ اللَّهَ قَدْ حَرَّمَ عَلَى النَّارِ مَنْ قَالَ لاَ '
                        'إِلَهَ إِلاَّ اللَّهُ\u200f.\u200f يَبْتَغِي بِذَلِكَ وَجْهَ اللَّهِ '
                        '\u200f"\u200f\u200f.\u200f قَالَ ابْنُ شِهَابٍ ثُمَّ سَأَلْتُ الْحُصَيْنَ بْنَ مُحَمَّدٍ '
                        'الأَنْصَارِيَّ ـ وَهْوَ أَحَدُ بَنِي سَالِمٍ وَهُوَ مِنْ سَرَاتِهِمْ ـ عَنْ حَدِيثِ مَحْمُودِ '
                        'بْنِ الرَّبِيعِ، فَصَدَّقَهُ بِذَلِكَ\u200f.\u200f',
                 'eng': "Narrated `Itban bin Malik:who was one of the companions of Allah's Messenger (ﷺ) and one of "
                        'the Ansars who took part in the battle of Badr: I came to Allah\'s Messenger (ﷺ) and said, "O '
                        "Allah's Messenger (ﷺ) I have weak eyesight and I lead my people in prayers. When it rains the "
                        'water flows in the valley between me and my people so I cannot go to their mosque to lead '
                        "them in prayer. O Allah's Messenger (ﷺ)! I wish you would come to my house and pray in it so "
                        'that I could take that place as a Musalla. Allah\'s Messenger (ﷺ) said. "Allah willing, I '
                        'will do so." Next day after the sun rose high, Allah\'s Messenger (ﷺ) and Abu Bakr came and '
                        "Allah's Messenger (ﷺ) asked for permission to enter. I gave him permission and he did not sit "
                        'on entering the house but said to me, "Where do you like me to pray?" I pointed to a place in '
                        "my house. So Allah's Messenger (ﷺ) stood there and said, 'Allahu Akbar', and we all got up "
                        'and aligned behind him and offered a two-rak`at prayer and ended it with Taslim. We requested '
                        'him to stay for a meal called "Khazira" which we had prepared for him. Many members of our '
                        'family gathered in the house and one of them said, "Where is Malik bin Al-Dukhaishin or Ibn '
                        'Al-Dukhshun?" One of them replied, "He is a hypocrite and does not love Allah and His '
                        'Apostle." Hearing that, Allah\'s Messenger (ﷺ) said, "Do not say so. Haven\'t you seen that '
                        'he said, \'None has the right to be worshipped but Allah\' for Allah\'s sake only?" He said, '
                        '"Allah and His Apostle know better. We have seen him helping and advising hypocrites." '
                        'Allah\'s Messenger (ﷺ) said, "Allah has forbidden the (Hell) fire for those who say, \'None '
                        "has the right to be worshipped but Allah' for Allah's sake only"},
  'source_evidence': {'ara': {'json_pointer': '/hadiths/425/text',
                              'original_text_sha256': 'e03fea33bbb0c8adbe76025ec695ff9f8c36596a688a6cbed562ecaeb7099035',
                              'quotation_spans': [[0, 2129]]},
                      'eng': {'json_pointer': '/hadiths/425/text',
                              'original_text_sha256': '8de4fcf21675da8384db4a7604fea48f75b743d826bc83e224f46630f9b886c1',
                              'quotation_spans': [[0, 1704]]}}},
 {'book': 'bukhari',
  'id': '4619',
  'expected': 'held',
  'quotations': {'ara': 'حَدَّثَنَا إِسْحَاقُ بْنُ إِبْرَاهِيمَ الْحَنْظَلِيُّ، أَخْبَرَنَا عِيسَى، وَابْنُ، إِدْرِيسَ '
                        'عَنْ أَبِي حَيَّانَ، عَنِ الشَّعْبِيِّ، عَنِ ابْنِ عُمَرَ، قَالَ سَمِعْتُ عُمَرَ ـ رضى الله '
                        'عنه ـ عَلَى مِنْبَرِ النَّبِيِّ صلى الله عليه وسلم يَقُولُ أَمَّا بَعْدُ أَيُّهَا النَّاسُ '
                        'إِنَّهُ نَزَلَ تَحْرِيمُ الْخَمْرِ وَهْىَ مِنْ خَمْسَةٍ، مِنَ الْعِنَبِ وَالتَّمْرِ '
                        'وَالْعَسَلِ وَالْحِنْطَةِ وَالشَّعِيرِ، وَالْخَمْرُ مَا خَامَرَ الْعَقْلَ\u200f.\u200f',
                 'ben': 'ইবনু ‘উমার (রাঃ) হতে বর্ণিত। তিনি বলেছেন যে, আমি উমার (রাঃ)-কে নবী সাল্লাল্লাহু ‘আলাইহি '
                        'ওয়াসাল্লাম-এর মিম্বরে বসে বলতে শুনেছি যে, এরপর হে লোক সকল! মদপানের নিষেধাজ্ঞা অবতীর্ণ হয়েছে '
                        'আর তা হচ্ছে পাঁচ প্রকার, খুরমা থেকে, আঙ্গুর থেকে, মধু থেকে, গম থেকে এবং যব থেকে আর মদ হচ্ছে '
                        'যা সুস্থ বিবেককে আচ্ছন্ন করে ফেলে। [৫৫৮১, ৫৫৮৮, ৫৫৮৯, ৭৩৩৭] (আধুনিক প্রকাশনীঃ ৪২৫৮, ইসলামিক '
                        'ফাউন্ডেশনঃ)',
                 'eng': 'Narrated Ibn `Umar:I heard `Umar while he was on the pulpit of the Prophet (ﷺ) saying, "Now '
                        'then O people! The revelation about the prohibition of alcoholic drinks was revealed; and '
                        'alcoholic drinks are extracted from five things: Grapes, dates, honey, wheat and barley. And '
                        'the alcoholic drink is that which confuses and stupefies the mind',
                 'urd': 'ہم سے اسحاق بن ابراہیم حنظلی نے بیان کیا، انہوں نے کہا ہم کو عیسیٰ اور ابن ادریس نے خبر دی، '
                        'انہیں ابوحیان نے، انہیں شعبی نے اور ان سے عبداللہ بن عمر رضی اللہ عنہما نے بیان کیا کہ میں نے '
                        'عمر رضی اللہ عنہ سے سنا، وہ نبی کریم صلی اللہ علیہ وسلم کے منبر پر کھڑے فرما رہے تھے۔ امابعد! '
                        'اے لوگو! جب شراب کی حرمت نازل ہوئی تو وہ پانچ چیزوں سے تیار کی جاتی تھی۔ انگور، کھجور، شہد، '
                        'گیہوں اور جَو سے اور شراب ہر وہ پینے کی چیز ہے جو عقل کو زائل کر دے۔'},
  'source_evidence': {'ara': {'json_pointer': '/hadiths/4634/text',
                              'original_text_sha256': '4b0b473c24f9d51cfd0cba2c13a7c092b32574db1688e2379dfe475c99bc230d',
                              'quotation_spans': [[0, 437]]},
                      'ben': {'json_pointer': '/hadiths/4634/text',
                              'original_text_sha256': 'a0aec81308a06898fdd41075f8ece52dbad7d2804ec0282f04e8a9c0b48d8578',
                              'quotation_spans': [[0, 375]]},
                      'eng': {'json_pointer': '/hadiths/4634/text',
                              'original_text_sha256': 'f686f03afeb301c59510a9d9a34b5439967c3d2df011d394ceb625f355ea50f3',
                              'quotation_spans': [[0, 340]]},
                      'urd': {'json_pointer': '/hadiths/4634/text',
                              'original_text_sha256': 'b188d59b7792d9263f260102e51fabe20ec661c804720a91b91be9592100dc21',
                              'quotation_spans': [[0, 440]]}}},
 {'book': 'bukhari',
  'id': '5588',
  'expected': 'held',
  'quotations': {'ara': 'حَدَّثَنَا أَحْمَدُ بْنُ أَبِي رَجَاءٍ، حَدَّثَنَا يَحْيَى، عَنْ أَبِي حَيَّانَ التَّيْمِيِّ، '
                        'عَنِ الشَّعْبِيِّ، عَنِ ابْنِ عُمَرَ ـ رضى الله عنهما ـ قَالَ خَطَبَ عُمَرُ عَلَى مِنْبَرِ '
                        'رَسُولِ اللَّهِ صلى الله عليه وسلم فَقَالَ إِنَّهُ قَدْ نَزَلَ تَحْرِيمُ الْخَمْرِ، وَهْىَ '
                        'مِنْ خَمْسَةِ أَشْيَاءَ الْعِنَبِ وَالتَّمْرِ وَالْحِنْطَةِ وَالشَّعِيرِ وَالْعَسَلِ، '
                        'وَالْخَمْرُ مَا خَامَرَ الْعَقْلَ، وَثَلاَثٌ وَدِدْتُ أَنَّ رَسُولَ اللَّهِ صلى الله عليه '
                        'وسلم لَمْ يُفَارِقْنَا حَتَّى يَعْهَدَ إِلَيْنَا عَهْدًا الْجَدُّ وَالْكَلاَلَةُ وَأَبْوَابٌ '
                        'مِنْ أَبْوَابِ الرِّبَا\u200f.\u200f قَالَ قُلْتُ يَا أَبَا عَمْرٍو فَشَىْءٌ يُصْنَعُ '
                        'بِالسِّنْدِ مِنَ الرُّزِّ\u200f.\u200f قَالَ ذَاكَ لَمْ يَكُنْ عَلَى عَهْدِ النَّبِيِّ صلى '
                        'الله عليه وسلم أَوْ قَالَ عَلَى عَهْدِ عُمَرَ\u200f.\u200f وَقَالَ حَجَّاجُ عَنْ حَمَّادٍ '
                        'عَنْ أَبِي حَيَّانَ مَكَانَ الْعِنَبِ الزَّبِيبَ\u200f.\u200f',
                 'ben': 'ইবনু ‘উমার (রাঃ) হতে বর্ণিত। তিনি বলেনঃ ‘উমার (রাঃ) মিম্বরের উপর দাঁড়িয়ে খুতবা দিতে গিয়ে '
                        'বললেন, নিশ্চয় মদ হারাম সম্পর্কীয় আয়াত অবতীর্ণ হয়েছে। আর তা প্রস্তুত হয় পাঁচটি জিনিস থেকেঃ '
                        'আঙ্গুর, খেজুর, গম, যব ও মধু। আর খামর মদ) হল তা, যা বিবেক লোপ করে দেয়। আর তিনটি এমন বিষয় আছে '
                        'যে, আমি চাচ্ছিলাম যেন রাসূলুল্লাহ সাল্লাল্লাহু আলাইহি ওয়াসাল্লাম আমাদের কাছে সেগুলো '
                        'স্পষ্টভাবে বর্ণনা না করা পর্যন্ত তিনি যেন আমাদের নিকট হতে বিচ্ছিন্ন না হয়ে যান। বিষয়গুলো হল, '
                        'দাদার মীরাস, কালালার ব্যাখ্যা এবং সুদের প্রকারসমূহ। রাবী আবূ হাইয়্যান বলেন, আমি বললামঃ হে আবূ '
                        'আমর! এক প্রকারের পানীয় জিনিস যা সিন্ধু অঞ্চলে চাউল দিয়ে তৈরী করা হয়, তার হুকুম কী? তিনি '
                        'বললেনঃ সেটি নবী সাল্লাল্লাহু আলাইহি ওয়াসাল্লাম -এর আমলে ছিল না। কিংবা তিনি বলেছেনঃ সেটি ‘উমার '
                        '-এর আমলে ছিল না। হাম্মাদ সূত্রে আবূ হাইয়্যান থেকে হাজ্জাজ الْعِنَبِ আঙ্গুর) এর জায়গায় '
                        'الزَّبِيب কিসমিস) বলেছেন। [৪৬১৯; মুসলিম ৫৪০/৬, হাঃ ৩৩২] আধুনিক প্রকাশনী- ৫১৭৮, ইসলামিক '
                        'ফাউন্ডেশন',
                 'eng': "Narrated Ibn `Umar:`Umar delivered a sermon on the pulpit of Allah's Messenger (ﷺ), saying, "
                        '"Alcoholic drinks were prohibited by Divine Order, and these drinks used to be prepared from '
                        'five things, i.e., grapes, dates, wheat, barley and honey. Alcoholic drink is that, that '
                        'disturbs the mind." `Umar added, "I wish Allah\'s Apostle had not left us before he had given '
                        'us definite verdicts concerning three matters, i.e., how much a grandfather may inherit (of '
                        'his grandson), the inheritance of Al-Kalala (the deceased person among whose heirs there is '
                        'no father or son), and various types of Riba(1 ) (usury)',
                 'urd': 'ہم سے احمد بن ابی رجاء نے بیان کیا، انہوں نے کہا ہم سے یحییٰ بن سعید قطان نے بیان کیا، ان سے '
                        'ابوحیان تمیمی نے، ان سے شعبی نے اور ان سے عبداللہ بن عمر رضی اللہ عنہما نے بیان کیا کہ عمر '
                        'رضی اللہ عنہ نے رسول اللہ صلی اللہ علیہ وسلم کے منبر پر خطبہ دیتے ہوئے کہا جب شراب کی حرمت کا '
                        'حکم ہوا تو وہ پانچ چیزوں سے بنتی تھی۔ انگور سے، کھجور سے، گیہوں سے، جَو اور شہد سے اور «خمر» '
                        '( شراب ) وہ ہے جو عقل کو مخمور کر دے اور تین مسائل ایسے ہیں کہ میری تمنا تھی کہ رسول اللہ صلی '
                        'اللہ علیہ وسلم ہم سے جدا ہونے سے پہلے ہمیں ان کا حکم بتا جاتے، دادا کا مسئلہ، کلالہ کا مسئلہ '
                        'اور سود کے چند مسائل۔ ابوحیان نے بیان کیا کہ میں نے شعبی سے پوچھا: اے ابوعمرو! ایک ایسا شربت '
                        'ہے جو سندھ میں چاول سے بنایا جاتا ہے۔ انہوں نے کہا کہ یہ چیز رسول اللہ صلی اللہ علیہ وسلم کے '
                        'زمانے میں نہیں پائی جاتی تھی یا کہا کہ عمر رضی اللہ عنہ کے زمانے میں نہ تھی اور فرج ابن منہال '
                        'نے بھی اس حدیث کو حماد بن سلمہ سے بیان کیا اور ان سے ابوحیان نے اس میں انگور کے بجائے کشمش '
                        'ہے۔'},
  'source_evidence': {'ara': {'json_pointer': '/hadiths/5610/text',
                              'original_text_sha256': '8dfcab2f3bae84532e0bdc757748ef2b3447e2ee79ab9508ca41e003393810e3',
                              'quotation_spans': [[0, 833]]},
                      'ben': {'json_pointer': '/hadiths/5610/text',
                              'original_text_sha256': 'ea594434b6c74d6fbbc926eacc7656b1de87cac49b55761ee368e1224780c8f7',
                              'quotation_spans': [[0, 906]]},
                      'eng': {'json_pointer': '/hadiths/5610/text',
                              'original_text_sha256': 'ef9cc284ff1666a04913707113263a2faa62b919f0d90729ddccb3b3940e16bc',
                              'quotation_spans': [[0, 607]]},
                      'urd': {'json_pointer': '/hadiths/5610/text',
                              'original_text_sha256': '1e3e565e8fccdc2f83ccc915295ec3d39d6ab92a58c5b94c0a2f0c9ae8e47612',
                              'quotation_spans': [[0, 932]]}}},
 {'book': 'ibnmajah',
  'id': '113',
  'expected': 'hadith',
  'quotations': {'ara': 'حَدَّثَنَا مُحَمَّدُ بْنُ عَبْدِ اللَّهِ بْنِ نُمَيْرٍ، وَعَلِيُّ بْنُ مُحَمَّدٍ، قَالاَ '
                        'حَدَّثَنَا وَكِيعٌ، حَدَّثَنَا إِسْمَاعِيلُ بْنُ أَبِي خَالِدٍ، عَنْ قَيْسِ بْنِ أَبِي '
                        'حَازِمٍ، عَنْ عَائِشَةَ، قَالَتْ قَالَ رَسُولُ اللَّهِ ـ صلى الله عليه وسلم ـ فِي مَرَضِهِ '
                        '\u200f"\u200f وَدِدْتُ أَنَّ عِنْدِي بَعْضَ أَصْحَابِي \u200f"\u200f \u200f.\u200f قُلْنَا '
                        'يَا رَسُولَ اللَّهِ أَلاَ نَدْعُو لَكَ أَبَا بَكْرٍ فَسَكَتَ قُلْنَا أَلاَ نَدْعُو لَكَ '
                        'عُمَرَ فَسَكَتَ قُلْنَا أَلاَ نَدْعُو لَكَ عُثْمَانَ قَالَ \u200f"\u200f نَعَمْ \u200f"\u200f '
                        '\u200f.\u200f فَجَاءَ عُثْمَانُ فَخَلاَ بِهِ فَجَعَلَ النَّبِيُّ ـ صلى الله عليه وسلم ـ '
                        'يُكَلِّمُهُ وَوَجْهُ عُثْمَانَ يَتَغَيَّرُ \u200f.\u200f قَالَ قَيْسٌ فَحَدَّثَنِي أَبُو '
                        'سَهْلَةَ مَوْلَى عُثْمَانَ أَنَّ عُثْمَانَ بْنَ عَفَّانَ قَالَ يَوْمَ الدَّارِ إِنَّ رَسُولَ '
                        'اللَّهِ ـ صلى الله عليه وسلم ـ عَهِدَ إِلَىَّ عَهْدًا وَأَنَا صَائِرٌ إِلَيْهِ \u200f.\u200f '
                        'وَقَالَ عَلِيٌّ فِي حَدِيثِهِ وَأَنَا صَابِرٌ عَلَيْهِ \u200f.\u200f قَالَ قَيْسٌ فَكَانُوا '
                        'يُرَوْنَهُ ذَلِكَ الْيَوْمَ \u200f.\u200f',
                 'eng': 'It was narrated that \'Aishah said:"When he was ill, the Messenger of Allah said: \'I would '
                        "like to have some of my Companions with me.' We said: 'O Messenger of Allah! Shall we call "
                        "Abu Bakr for you?' But he remained silent. We said: 'Shall we call 'Umar for you?' But he "
                        "remained silent. We said: 'Shall we call 'Uthman for you?' He said: 'Yes.' So 'Uthman came "
                        "and he spoke to him in private. The Prophet started to speak to him and 'Uthman's expression "
                        'changed." Qais said: "Abu Sahlah, the freed slave of \'Uthman, narrated to me that on the Day '
                        "of the House, 'Uthman bin 'Affan said: 'The Messenger of Allah told me what would come to "
                        'pass and now I am coming to that day.\'"In his narration of the Hadith, \'Ali (one of the '
                        'narrators) said (that he said): "And I am going to bear it with patience." Qais said: "They '
                        'used to think that that was the Day of the House'},
  'source_evidence': {'ara': {'json_pointer': '/hadiths/112/text',
                              'original_text_sha256': '1f1b5f674c6e6d2c9f630b68193d5d40bb2722893c968bb5ea0097bc65967bd9',
                              'quotation_spans': [[0, 936]]},
                      'eng': {'json_pointer': '/hadiths/112/text',
                              'original_text_sha256': '661a29df383287c3111a5c3816effbd6decbc91e7bace3649f8295311b5ed6aa',
                              'quotation_spans': [[0, 866]]}}},
 {'book': 'muslim',
  'id': '7559',
  'expected': 'held',
  'quotations': {'ara': 'حَدَّثَنَا أَبُو بَكْرِ بْنُ أَبِي شَيْبَةَ، حَدَّثَنَا عَلِيُّ بْنُ مُسْهِرٍ، عَنْ أَبِي '
                        'حَيَّانَ، عَنِ الشَّعْبِيِّ، عَنِ ابْنِ عُمَرَ، قَالَ خَطَبَ عُمَرُ عَلَى مِنْبَرِ رَسُولِ '
                        'اللَّهِ صلى الله عليه وسلم فَحَمِدَ اللَّهَ وَأَثْنَى عَلَيْهِ ثُمَّ قَالَ أَمَّا بَعْدُ '
                        'أَلاَ وَإِنَّ الْخَمْرَ نَزَلَ تَحْرِيمُهَا يَوْمَ نَزَلَ وَهْىَ مِنْ خَمْسَةِ أَشْيَاءَ مِنَ '
                        'الْحِنْطَةِ وَالشَّعِيرِ وَالتَّمْرِ وَالزَّبِيبِ وَالْعَسَلِ \u200f.\u200f وَالْخَمْرُ مَا '
                        'خَامَرَ الْعَقْلَ وَثَلاَثَةُ أَشْيَاءَ وَدِدْتُ أَيُّهَا النَّاسُ أَنَّ رَسُولَ اللَّهِ صلى '
                        'الله عليه وسلم كَانَ عَهِدَ إِلَيْنَا فِيهَا الْجَدُّ وَالْكَلاَلَةُ وَأَبْوَابٌ مِنْ '
                        'أَبْوَابِ الرِّبَا \u200f.\u200f',
                 'ben': 'আবূ বাকর ইবনু শাইবাহ (রহঃ) ..... ইবনু উমর (রাযিঃ) থেকে বর্ণিত। তিনি বলেন, একদিন উমর (রাযিঃ) '
                        'রসূলুল্লাহ সাল্লাল্লাহু আলাইহি ওয়াসাল্লাম এর মিম্বারে উঠে খুৎবাহ প্রদান করতঃ প্রথমে আল্লাহর '
                        'প্রশংসা এবং গুণকীর্তন করলেন। অতঃপর বললেন- মদ হারাম হওয়ার বিধান যেদিন অবতীর্ণ হওয়ার অবতীর্ণ '
                        'হয়েছে। তখন তা পাঁচটি জিনিস হতে বানানো হতো, গম, যব, খেজুর, আঙ্গুর এবং মধু হতে। আর যা মানুষের '
                        'বিবেকবুদ্ধি বিলোপ করে দেয়, তা-ই মদ। আর তিনটি বিষয়, হে লোক সকল! আমার প্রত্যাশা। যদি '
                        'রসূলুল্লাহ সাল্লাল্লাহু আলাইহি ওয়াসাল্লাম আমাদের কাছে দাদার (পরিত্যক্ত সম্পত্তি), কালালাহ্ '
                        '(নিঃসন্তান ব্যক্তির পরিত্যাজ্য সম্পত্তি) এবং সুদের বিভিন্ন অধ্যায় সম্পর্কে (আরো স্পষ্ট) বলে '
                        'যেতেন। (ইসলামিক ফাউন্ডেশন ৭২৭৭, ইসলামিক সেন্টার)',
                 'eng': "Ibn 'Umar reported that Umar delivered a sermon on the pulpit of Allah's Messenger (ﷺ) and he "
                        'praised Allah and lauded Him and then said:Now coming to the point. Behold I when the command '
                        'pertaining to the prohibition of wine was revealed, it was prepared from five things: from '
                        'wheat, barley, date, grape, honey; and wine is that which clouds the intellect; and O people, '
                        "I wish Allah's Messenger (ﷺ) could have explained to us in (more) detail the laws pertaining "
                        'to the inheritance of the grandfather, about one who dies leaving no issue, and some of the '
                        'problems pertaining to interest',
                 'urd': 'علی بن مسہر نے ابو حیان سے ، انھوں نے شعبی سے اور انھوں نے حضرت ابن عمر رضی اللہ تعالیٰ عنہ '
                        'سے روایت کی ، کہا : حضرت عمر رضی اللہ تعالیٰ عنہ نے رسول اللہ صلی اللہ علیہ وسلم کے منبر پر ( '
                        'کھڑے ہوکر ) خطبہ دیا ، اللہ تعالیٰ کی حمدوثنا بیان کی ، پھر کہا : اس کے بعد : سنو !شراب کی '
                        'حرمت نازل ہوئی ، جس دن وہ نازل ہوئی ( اس وقت ) وہ پانچ چیزوں سے بنتی تھی ۔ گندم ، جو ، خشک '
                        'کھجور ، انگور اور شہد سے ، خمر وہ ہے جو عقل کو ڈھانپ لے ۔ اورلوگو!تین چیزیں ایسی ہیں جن کے '
                        'متعلق میں شدت سے چاہتا ہوں کہ رسول اللہ صلی اللہ علیہ وسلم نے ان کے بارے میں ہمیں اور زیادہ '
                        'قطعیت سے بتایا ہوتا : دادا اور کلالہ کی میراث اور سود کے ابواب میں سے چند ابواب ۔'},
  'source_evidence': {'ara': {'json_pointer': '/hadiths/7558/text',
                              'original_text_sha256': 'e8796891cf9257af5a3adca1ed3be94896600cbcc18b860c828ba47bc80eede2',
                              'quotation_spans': [[0, 647]]},
                      'ben': {'json_pointer': '/hadiths/7558/text',
                              'original_text_sha256': '9d34dc289a4f6a92cb8f5ba7b6e133a16b0e2a08cbc5a036625de3d3f568117c',
                              'quotation_spans': [[0, 687]]},
                      'eng': {'json_pointer': '/hadiths/7558/text',
                              'original_text_sha256': 'f1a07a68139e25846acb323e29bd0a022c427cd28fb78a2619f574562e9c2857',
                              'quotation_spans': [[0, 589]]},
                      'urd': {'json_pointer': '/hadiths/7559/text',
                              'original_text_sha256': '6bea2d3a291c15107632cc4bf5a57be0f0bd6b7ab0f34dc2e48a20491ef471f1',
                              'quotation_spans': [[0, 632]]}}},
 {'book': 'muslim',
  'id': '7560',
  'expected': 'held',
  'quotations': {'ara': 'وَحَدَّثَنَا أَبُو كُرَيْبٍ، أَخْبَرَنَا ابْنُ إِدْرِيسَ، حَدَّثَنَا أَبُو حَيَّانَ، عَنِ '
                        'الشَّعْبِيِّ، عَنِ ابْنِ، عُمَرَ قَالَ سَمِعْتُ عُمَرَ بْنَ الْخَطَّابِ، عَلَى مِنْبَرِ '
                        'رَسُولِ اللَّهِ صلى الله عليه وسلم يَقُولُ أَمَّا بَعْدُ أَيُّهَا النَّاسُ فَإِنَّهُ نَزَلَ '
                        'تَحْرِيمُ الْخَمْرِ وَهْىَ مِنْ خَمْسَةٍ مِنَ الْعِنَبِ وَالتَّمْرِ وَالْعَسَلِ وَالْحِنْطَةِ '
                        'وَالشَّعِيرِ وَالْخَمْرُ مَا خَامَرَ الْعَقْلَ وَثَلاَثٌ أَيُّهَا النَّاسُ وَدِدْتُ أَنَّ '
                        'رَسُولَ اللَّهِ صلى الله عليه وسلم كَانَ عَهِدَ إِلَيْنَا فِيهِنَّ عَهْدًا نَنْتَهِي إِلَيْهِ '
                        'الْجَدُّ وَالْكَلاَلَةُ وَأَبْوَابٌ مِنْ أَبْوَابِ الرِّبَا \u200f.\u200f',
                 'ben': 'আবু কুরায়ব (রহঃ) ..... ইবনু উমার (রাযিঃ) থেকে বর্ণিত। তিনি বলেন, আমি ‘উমার ইবনুল খাত্তাব '
                        '(রাযিঃ) কে রসূলুল্লাহ সাল্লাল্লাহু আলাইহি ওয়াসাল্লাম এর মিম্বারে উঠে খুৎবাহ রত অবস্থায় এ কথা '
                        'বলতে শুনেছি যে, অতঃপর হে লোক সকল! মদ হারাম হওয়ার বিধান অবতীর্ণ হয়েছে। তা পাঁচটি জিনিস হতে '
                        'বানানো হয়। আঙ্গুর, খেজুর, মধু, গম ও যব হতে। আর যা মানুষের হিতাহিত জ্ঞান বিলুপ্ত করে দেয় '
                        'তা-ই মদ। আর তিনটি বিষয়, হে লোক সকল! আমার মনের কামনা, যদি রসূলুল্লাহ সাল্লাল্লাহু আলাইহি '
                        'ওয়াসাল্লাম আমাদেরকে (নিম্নোক্ত কতিপয় বিষয়ে) আরো বিশদভাবে সুস্পষ্টভাবে বলে যেতেন তবে তো আমরা '
                        'এ সম্পর্কে চূড়ান্ত সিদ্ধান্ত পৌছে যেতে পারতাম। আর তা হচ্ছে, দাদার (মীরাস বণ্টন), কালালাহ্ '
                        '(নিঃসন্তান ব্যক্তির পরিত্যাজ্য সম্পত্তি) এবং সুদের কতিপয় বিষয়াদি সম্পর্কিত বিধান বলে দিতেন। '
                        '(ইসলামিক ফাউন্ডেশন ৭২৭৮, ইসলামিক সেন্টার)',
                 'eng': "Ibn 'Umar reported:I heard 'Umar b. Khattab delivering sermon on the pulpit ol Allah's "
                        "messenger (ﷺ) and saying': Now, coming to the point, O people, there was revealed (the "
                        'command pertaining to the prohibition of wine) and it was prepared (at that time) out of five '
                        'things: grape, date, honey, wheat, barley, and wine is that which clouds the intellect, and, '
                        "O people, I wish Allah's Messenger (ﷺ) had explained to us in greater detail three things: "
                        'the inheritance of the grandfather, of one who dies without leaving any issue, and some of '
                        'the problems of interest',
                 'urd': 'ابن ادریس نے کہا : ہمیں ابو حیان نے شعبی سے حدیث بیان کی ۔ انھوں نے حضرت عبداللہ بن عمر رضی '
                        'اللہ تعالیٰ عنہ سے روایت کی ، کہا : میں نے حضرت عمر بن خطاب رضی اللہ تعالیٰ عنہ کو رسول اللہ '
                        'صلی اللہ علیہ وسلم کے منبر پر فرماتے ہوئے سنا : حمد وثنا کےبعد ، لوگو!شراب کی حرمت نازل ہوئی '
                        'تو وہ پانچ چیزوں سے بنائی جاتی تھی ، انگور ، کھجور ، شہد ، گندم اور جو سے اور خمر ( شراب ) وہ '
                        'ہے جو عقل کو ڈھانک دے ۔ لوگو!تین چیزیں ایسی ہیں جن کے متعلق میں چاہتا تھا کہ رسول اللہ صلی '
                        'اللہ علیہ وسلم ہمیں اور زیادہ قطیعت سے واضح فرمادیتے : دادا اور کلالہ کی میراث اور سود کی '
                        'صورتوں میں سے چند صورتیں ۔'},
  'source_evidence': {'ara': {'json_pointer': '/hadiths/7559/text',
                              'original_text_sha256': '00455f4f3136aa55471072e527d051e75644db3d9caf70205d326fe29cc8c0ea',
                              'quotation_spans': [[0, 611]]},
                      'ben': {'json_pointer': '/hadiths/7559/text',
                              'original_text_sha256': '0c92de13777b5c3b55ef2a9327c47eae4468e9c0421aaa5bc8cf4634c8ecca9d',
                              'quotation_spans': [[0, 775]]},
                      'eng': {'json_pointer': '/hadiths/7559/text',
                              'original_text_sha256': '8ac6ecfb6f455fd9d64e45ee6ec9b905ae47eea63ec3dab4f568034d4ceb307f',
                              'quotation_spans': [[0, 567]]},
                      'urd': {'json_pointer': '/hadiths/7560/text',
                              'original_text_sha256': '9d7b729bcafd203c182b6aa9c4b58b9af0af0c36c20ef23fb4919d0b055d0b1a',
                              'quotation_spans': [[0, 579]]}}},
 {'book': 'nasai',
  'id': '5579',
  'expected': 'held',
  'quotations': {'ara': 'أَخْبَرَنَا مُحَمَّدُ بْنُ الْعَلاَءِ، قَالَ أَنْبَأَنَا ابْنُ إِدْرِيسَ، عَنْ زَكَرِيَّا، '
                        'وَأَبِي، حَيَّانَ عَنِ الشَّعْبِيِّ، عَنِ ابْنِ عُمَرَ، قَالَ سَمِعْتُ عُمَرَ بْنَ '
                        'الْخَطَّابِ، رضى الله عنه عَلَى مِنْبَرِ رَسُولِ اللَّهِ صلى الله عليه وسلم يَقُولُ أَمَّا '
                        'بَعْدُ فَإِنَّ الْخَمْرَ نَزَلَ تَحْرِيمُهَا وَهِيَ مِنْ خَمْسَةٍ مِنَ الْعِنَبِ '
                        'وَالْحِنْطَةِ وَالشَّعِيرِ وَالتَّمْرِ وَالْعَسَلِ \u200f.\u200f',
                 'ben': 'মুহাম্মাদ ইবন আলা (রহঃ) ... ইবন উমর (রাঃ) থেকে বর্ণিত। তিনি বলেন, আমি উমর (রাঃ)-কে মিম্বরে '
                        'বলতে শুনেছি। তিনি আল্লাহর প্রশংসা করার পর বলেনঃ জেনে রাখ! যখন মদ হারাম হয় তখন খেজুর, গম, যব, '
                        'মধু এবং আঙুর এ পাঁচটি বস্তু থেকে মদ তৈরি হতো।',
                 'eng': 'It was narrated that Ibn \'Umar said:"I heard \'Umar bin Al-Khattab, may Allah be pleased '
                        "with him, on the Minbar of the Messenger of Allah [SAW], say: 'The prohibition of Khamr was "
                        'revealed when it was made from five things: From grapes, wheat, barley, dates and honey',
                 'urd': ''},
  'source_evidence': {'ara': {'json_pointer': '/hadiths/5585/text',
                              'original_text_sha256': 'a31bf0ddd9a2946cc69482d3fbdc765f3662a41d1a4cb8dc3ef75e06a5beb9c3',
                              'quotation_spans': [[0, 400]]},
                      'ben': {'json_pointer': '/hadiths/5585/text',
                              'original_text_sha256': '71e8c1b12d264cff4c51ae0344366cfba115ec104f363709c20106e693fc5eec',
                              'quotation_spans': [[0, 230]]},
                      'eng': {'json_pointer': '/hadiths/5585/text',
                              'original_text_sha256': '6dfc6ba371bd672a9375133e7e9b4fae7ebc2b61f5c34df991d10affd6d42784',
                              'quotation_spans': [[0, 267]]},
                      'urd': {'json_pointer': '/hadiths/5585/text',
                              'original_text_sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                              'quotation_spans': [[0, 0]]}}}]


def row(number, text="TEST قال رسول الله TEST source quotation", book=1):
    return {"hadithnumber": number, "arabicnumber": number, "text": text,
            "reference": {"book": book, "hadith": number},
            "grades": [{"name": "TEST assessor", "grade": "TEST source grade"}]}


def catalog(books):
    return {book: {"name": importer.BOOKS[book][1], "collection": [
        {"name": prefix + "-" + book, "book": book, "language": label,
         "author": "Unknown" if prefix != "eng" else "TEST source translator",
         "source": "", "comments": "TEST edition note" if prefix == "eng" else ""}
        for prefix, (_, label, _) in importer.LANGUAGES.items()]} for book in books}


def source_data(book, rows, sections=None):
    return {"metadata": {"name": importer.BOOKS[book][1],
                         "sections": sections or {"0": "The Book of the Sunnah", "1": "TEST section"},
                         "section_details": {}}, "hadiths": rows}


class FawazBulkTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "AGENTS.md").write_text("TEST source-preservation rules")
        self.books = ["bukhari"]
        self.plan = {"schema": "hadith-bank-fawaz-bulk-plan-v1", "enabled": True,
                     "repository": importer.REPOSITORY, "revision": importer.REVISION,
                     "books": self.books, "languages": list(importer.BASE_LANGUAGES), "max_books_per_batch": 7}
        importer.save_json(self.root, importer.PLAN, self.plan)
        self.state = {"schema": "hadith-bank-fawaz-bulk-state-v1", "revision": importer.REVISION, "inputs": {}, "stop": None}

    def inputs(self, books=None):
        books = books or self.books
        values = {"editions.json": importer.encoded(catalog(books)),
                  "README.md": b"TEST whole edition documentation\n", "LICENSE": b"TEST source license bytes\n",
                  "References.md": b"TEST project-wide credit https://example.invalid/source\n",
                  "CONTRIBUTING.md": b"TEST same provider numbering across editions\n"}
        for book in books:
            for prefix in self.plan["languages"]:
                values["editions/" + prefix + "-" + book + ".json"] = importer.encoded(source_data(book, [row(1)]))
        return values

    def seed(self, inputs=None):
        for key, raw in (inputs or self.inputs()).items():
            self.state["inputs"][key] = importer.snapshot(self.root, key, raw, {
                "url": importer.provider_url(key), "retrieved_at": "2026-11-12T00:00:00+00:00"})
        importer.save_json(self.root, importer.IMPORT + "/state.json", self.state)

    def args(self, **changes):
        values = dict(root=self.root, fetch=False, export_only=True, adopt_dir=None,
                      max_books=None, retry_failed=False)
        values.update(changes)
        return argparse.Namespace(**values)

    def test_exact_text_own_references_grades_and_registry_projection(self):
        inputs = self.inputs()
        for prefix in self.plan["languages"]:
            text = "TEST قال رسول الله TEST exact\nsource " if prefix == "ara" else "TEST " + prefix + " quotation\n"
            inputs["editions/" + prefix + "-bukhari.json"] = importer.encoded(source_data("bukhari", [row(1, text)]))
        self.seed(inputs)
        importer.save_json(self.root, "catalog/provenance-policy.json", {
            "schema": "hadith-bank-provenance-policy-v1", "decision_date_japan": "2026-11-11", "source_rules": [],
            "new_material_rule": {"scope": "registered_nonlegacy_materials_and_counterparts", "classification": "human",
                                  "basis": "TEST owner decision", "source_declarations_take_precedence": True}})
        summary, code = importer.run(self.args())
        self.assertEqual((code, summary["registered_occurrences"], summary["held_occurrences"]), (0, 1, 0))
        materials = load_public_materials(self.root)
        records = [value for group in materials["groups"] for value in group]
        self.assertEqual(len(records), 1)
        record = records[0]
        versions = {item["language"]: item for item in record["language_versions"]}
        self.assertEqual(versions["ar"]["text"], "TEST قال رسول الله TEST exact\nsource ")
        self.assertIsNone(versions["ar"]["translation_provenance"])
        self.assertEqual(versions["en"]["translation_provenance"]["current_policy"]["classification"], "human")
        self.assertIsNone(versions["ur"]["source"]["translator"]["name"])
        self.assertEqual(versions["en"]["source"]["translator"]["name"], "TEST source translator")
        for code, prefix in [("ar", "ara"), ("en", "eng"), ("ur", "urd")]:
            own = versions[code]
            self.assertEqual(own["grading"], row(1)["grades"])
            self.assertIn(prefix + "-bukhari", own["source"]["record_url"])
            self.assertEqual(own["references"][0]["numbering_system"], "fawaz_api_hadithnumber")
            self.assertTrue(any(note["text"] == "Source assessment — TEST assessor: TEST source grade" for note in own["comments"]))
        self.assertEqual(len(language_readings(record)), 3)
        self.assertIsNone(record["number"]["canonical"])
        self.assertIsNone(record["grading"]["grade"])

    def test_unique_typed_provider_ids_not_array_positions_or_integer_casts(self):
        inputs = self.inputs()
        for prefix in self.plan["languages"]:
            rows = [row(1), row(1.5)]
            if prefix == "eng":
                rows.reverse()
            if prefix == "urd":
                rows.append(row(1.75, "TEST رسول اللہ نے فرمایا TEST Urdu quotation"))
            inputs["editions/" + prefix + "-bukhari.json"] = importer.encoded(source_data("bukhari", rows))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary["registered_occurrences"], 3)
        rows = [json.loads(line) for path in (self.root / "materials").glob("*/records.jsonl") for line in path.read_text().splitlines()]
        self.assertEqual({item["number"]["source_entry_id"] for item in rows}, {1, 1.5, 1.75})
        for item in rows:
            for version in item["language_versions"]:
                self.assertEqual(version["provider_numbers"]["hadithnumber"], item["number"]["source_entry_id"])

    def test_bengali_extension_preserves_base_books_own_metadata_and_missing_states(self):
        inputs = self.inputs()
        metadata = json.loads(inputs['editions.json'])
        bengali = next(item for item in metadata['bukhari']['collection'] if item['name'] == 'ben-bukhari')
        bengali.update(author='TEST Bengali translator', comments='TEST Bengali edition comment',
                       source='https://example.invalid/bengali-edition')
        inputs['editions.json'] = importer.encoded(metadata)
        for prefix in self.plan['languages']:
            text = 'TEST قال رسول الله TEST quotation' if prefix == 'ara' else 'TEST ' + prefix + ' quotation'
            inputs['editions/' + prefix + '-bukhari.json'] = importer.encoded(source_data('bukhari',
                [row(1, text), row(1.5, text), row(2, text)]))
        self.seed(inputs)
        first, _ = importer.run(self.args())
        self.assertTrue(first['complete'])

        def records():
            return {item['id']: item for path in (self.root / 'materials').glob('*/records.jsonl')
                    for line in path.read_text().splitlines() if (item := json.loads(line))}

        before = records()
        source_hashes = {key: value['sha256'] for key, value in self.state['inputs'].items()}
        self.plan['languages'] = list(importer.LANGUAGES)
        importer.save_json(self.root, importer.PLAN, self.plan)
        pending, _ = importer.run(self.args())
        self.assertFalse(pending['complete'])
        self.assertEqual(pending['registered_occurrences'], 3)
        self.assertEqual(pending['pending_books'], ['bukhari'])
        self.assertEqual(pending['pending_editions'], ['editions/ben-bukhari.json'])
        self.assertEqual(set(records()), set(before))
        self.assertTrue(all(item['source']['language_availability']['bn'] == 'edition_pending'
                            for item in records().values()))

        bengali_row = row(1, 'TEST বাংলা মূল বাণী\n')
        bengali_row['grades'] = [{'name': 'TEST Bengali assessor', 'grade': 'TEST Bengali grade'}]
        raw = importer.encoded(source_data('bukhari', [row(1.5, ' '), bengali_row]))
        with mock.patch.object(importer, 'fetch_bytes', return_value=(raw, {
                'url': importer.provider_url('editions/ben-bukhari.json'), 'retrieved_at': 'TEST'})) as request:
            completed, code = importer.run(self.args(fetch=True, export_only=False))
        self.assertEqual(request.call_args_list, [mock.call('editions/ben-bukhari.json')])
        self.assertEqual((code, completed['complete'], completed['fetched_editions']), (0, True, 4))
        self.assertEqual(completed['registered_occurrences'], 3)
        after = records()
        self.assertEqual(set(before), set(after))
        by_number = {item['number']['source_entry_id']: item for item in after.values()}
        self.assertEqual({number: item['source']['language_availability']['bn'] for number, item in by_number.items()},
                         {1: 'available', 1.5: 'source_text_empty', 2: 'provider_entry_absent'})
        own = next(item for item in by_number[1]['language_versions'] if item['language'] == 'bn')
        self.assertEqual((own['text'], own['script']), (bengali_row['text'], 'Beng'))
        self.assertEqual(own['provider_numbers']['hadithnumber'], 1)
        self.assertEqual(own['source']['provider_edition'], 'ben-bukhari')
        self.assertEqual(own['source']['translator']['name'], 'TEST Bengali translator')
        self.assertEqual(own['grading'], bengali_row['grades'])
        self.assertTrue(any(note['text'] == 'TEST Bengali edition comment' for note in own['comments']))
        self.assertTrue(any('TEST Bengali assessor: TEST Bengali grade' in note['text'] for note in own['comments']))
        for identifier, item in after.items():
            self.assertEqual([view for view in item['language_versions'] if view['language'] != 'bn'],
                             before[identifier]['language_versions'])
        saved_state = importer.read_json(self.root, importer.IMPORT + '/state.json')
        self.assertTrue(all(saved_state['inputs'][key]['sha256'] == value for key, value in source_hashes.items()))
        projected = [item for group in load_public_materials(self.root)['groups'] for item in group]
        self.assertEqual(len(projected), 3)
        self.assertEqual(sum(view['language'] == 'bn' for item in projected for view in language_readings(item)), 1)

    def test_duplicate_or_inconsistent_provider_identity_is_held(self):
        inputs = self.inputs()
        for prefix in self.plan["languages"]:
            rows = [row(1), row(2)]
            if prefix == "eng":
                rows.append(row(1))
                rows[1]["arabicnumber"] = 99
            inputs["editions/" + prefix + "-bukhari.json"] = importer.encoded(source_data("bukhari", rows))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual((summary["registered_occurrences"], summary["held_occurrences"]), (0, 2))
        held = [json.loads(line) for line in gzip.decompress((self.root / importer.IMPORT / "held/bukhari.jsonl.gz").read_bytes()).splitlines()]
        self.assertEqual({item["classification"]["reason"] for item in held},
                         {"duplicate_provider_identity_within_edition", "inconsistent_shared_provider_arabicnumber"})
        self.assertTrue(all(item["show_in_html_hadith"] is False for item in held))
        self.assertEqual(len(held[0]["source_versions"]["eng"]), 2)

    def test_bengali_nawawi_has_no_urdu_edition_or_invented_translator(self):
        self.plan.update(books=['nawawi'], languages=list(importer.LANGUAGES))
        importer.save_json(self.root, importer.PLAN, self.plan)
        inputs = self.inputs(['nawawi'])
        del inputs['editions/urd-nawawi.json']
        catalog_data = json.loads(inputs['editions.json'])
        catalog_data['nawawi']['collection'] = [item for item in catalog_data['nawawi']['collection'] if item['name'] != 'urd-nawawi']
        for meta in catalog_data['nawawi']['collection']:
            meta['author'] = 'Imam Nawawi'
        inputs['editions.json'] = importer.encoded(catalog_data)
        for prefix, text in [('eng', 'TEST source English quotation'), ('ben', 'TEST source Bengali quotation')]:
            inputs['editions/' + prefix + '-nawawi.json'] = importer.encoded(source_data('nawawi', [row(1, text)]))
        self.seed(inputs)
        with mock.patch.object(importer, 'fetch_bytes', side_effect=AssertionError('No unavailable edition may be requested')) as fetch:
            summary, code = importer.run(self.args(fetch=True, export_only=False))
        self.assertEqual((code, summary['complete'], summary['configured_editions'], summary['fetched_editions']), (0, True, 3, 3))
        self.assertEqual(summary['pending_editions'], [])
        fetch.assert_not_called()
        records = [item for group in load_public_materials(self.root)['groups'] for item in group]
        self.assertEqual(len(records), 1)
        canonical = [json.loads(line) for path in (self.root / 'materials').glob('*/records.jsonl') for line in path.read_text().splitlines()]
        self.assertEqual(canonical[0]['source']['language_availability']['ur'], 'edition_not_published_in_pinned_catalog')
        self.assertEqual({view['language'] for view in records[0]['language_versions']}, {'ar', 'en', 'bn'})
        for view in records[0]['language_versions']:
            self.assertIsNone(view['source']['translator']['name'])
            self.assertEqual(view['source']['catalog_author_as_supplied'], 'Imam Nawawi')
            self.assertEqual(view['source']['catalog_author_role'], 'collection_compiler_not_translation_credit')
        with self.assertRaisesRegex(ValueError, 'Unconfigured upstream path'):
            importer.provider_url('editions/urd-nawawi.json')

    def test_non_prophetic_empty_and_explicit_intro_are_held_but_book_zero_is_not_enough(self):
        inputs = self.inputs()
        for prefix in self.plan["languages"]:
            rows = [row(1, book=0), row(2, "TEST independent statement"), row(3, " "), row(4, book=2)]
            inputs["editions/" + prefix + "-bukhari.json"] = importer.encoded(source_data("bukhari", rows,
                {"0": "The Book of the Sunnah", "1": "TEST", "2": "Introduction"}))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual((summary["registered_occurrences"], summary["held_occurrences"]), (1, 3))

    def test_literal_compiler_note_spans_partition_without_rewriting(self):
        for book, language, text in [
            ("abudawud", "en", "TEST narration. Abu Dawud said: TEST note with additional report"),
            ("tirmidhi", "en", "TEST narration. [Abu 'Eisa said:] TEST note"),
            ("tirmidhi", "en", "TEST narration. [Abu `Eisa said: TEST note]"),
            ("tirmidhi", "ar", "TEST قَالَ رَسُولُ اللَّهِ TEST. قَالَ أَبُو عِيسَى TEST note"),
            ("abudawud", "bn", "TEST বাংলা বাণী। ইমাম আবূ দাঊদ (রহঃ) বলেন, TEST note"),
            ("abudawud", "bn", "TEST বাংলা বাণী। ইমাম আবূ দাউদ (রহঃ) বলেছেন, TEST note"),
            ("abudawud", "bn", "TEST বাংলা বাণী। قَالَ أَبُو دَاوُدَ TEST note. ইমাম আবূ দাঊদ (রহঃ) বলেন, TEST note"),
            ("tirmidhi", "bn", "TEST বাংলা বাণী। আবু ঈসা বলেন, TEST note"),
            ("tirmidhi", "bn", "TEST বাংলা বাণী। আবূ ঈসা বলেছেন, TEST note"),
            ("tirmidhi", "bn", "TEST বাংলা বাণী। TEST হাদীসটিকে আবু ঈসা হাসান সহীহ বলেছেন। TEST note"),
            ("tirmidhi", "bn", "TEST বাংলা বাণী। TEST হাদীসটিকে আবূ ঈসা গারীব বলেছেন। TEST note"),
            ("tirmidhi", "bn", "TEST বাংলা বাণী। আমি (আবূ ঈসা) TEST note"),
            ("tirmidhi", "bn", "TEST বাংলা বাণী। —সহীহ। TEST source grade. আবূ ঈসা বলেন, TEST note"),
        ]:
            with self.subTest(language=language, book=book):
                quotation, notes, spans = importer.split_compiler_note(text, book, language)
                self.assertEqual(quotation + "".join(notes), text)
                self.assertEqual(quotation, text[slice(*spans["quotation"])])
                self.assertEqual(notes, [text[slice(*item)] for item in spans["notes"]])
                self.assertIn("pending", spans["note_embedded_narration_extraction"])
                if language == "bn":
                    self.assertTrue(quotation.strip().endswith('বাণী।'))
                    self.assertNotIn('قَالَ', quotation)
                    self.assertNotIn('সহীহ', quotation)
        untouched = "TEST Anas ibn Malik said TEST"
        self.assertEqual(importer.split_compiler_note(untouched, "malik", "en")[0], untouched)

    def test_explicit_compiler_tail_is_kept_in_its_own_source_notes(self):
        inputs = self.inputs()
        inputs["editions/ara-bukhari.json"] = importer.encoded(source_data("bukhari", [
            row(1, "TEST قال رسول الله TEST quotation. قال أبو عبد الله TEST compiler material")]))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary["registered_occurrences"], 1)
        records = [json.loads(line) for path in (self.root / 'materials').glob('*/records.jsonl') for line in path.read_text().splitlines()]
        own = next(item for item in records[0]['language_versions'] if item['language'] == 'ar')
        self.assertNotIn('compiler material', own['text'])
        self.assertTrue(any('compiler material' in item['text'] for item in own['comments']))

    def test_nabidh_and_wishes_about_prophet_do_not_establish_speaker_identity(self):
        inputs = self.inputs()
        arabic = [row(1, 'TEST عن النبيذ TEST'),
                  row(2, 'TEST وددت أن رسول الله صلى الله عليه وسلم كان عهد إلينا TEST'),
                  row(3, 'TEST سمعت عمر علي منبر رسول الله صلى الله عليه وسلم يقول TEST')]
        for prefix in self.plan["languages"]:
            rows = arabic if prefix == 'ara' else [row(i, 'TEST independent source statement') for i in (1, 2, 3)]
            inputs['editions/' + prefix + '-bukhari.json'] = importer.encoded(source_data('bukhari', rows))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary['registered_occurrences'], 0)
        self.assertEqual(summary['by_book']['bukhari']['by_hold_reason']['attribution_subject_requires_review'], 2)

    def test_actual_wish_contexts_allow_independent_evidence_but_six_umar_sermons_stay_held(self):
        for fixture in ACTUAL_SUBJECT_REGRESSIONS:
            with self.subTest(book=fixture['book'], number=fixture['id']):
                versions = {language: {'quotation': text, 'row': row(int(fixture['id']), text),
                                       'metadata': {'sections': {}}}
                            for language, text in fixture['quotations'].items()}
                before = copy.deepcopy(versions)
                normalized, _ = importer.normalized_with_offsets(versions['ara']['quotation'])
                self.assertIsNotNone(importer.AMBIGUOUS_ATTRIBUTION.search(normalized))
                result = importer.classify_group(versions)
                self.assertEqual(result['classification'], fixture['expected'])
                self.assertEqual(versions, before)
                if fixture['expected'] == 'hadith':
                    self.assertEqual(result['subject_check'], 'source_local_guarded_evidence')
                    start, end = result['span']
                    self.assertEqual(result['text'], versions[result['source_language']]['quotation'][start:end])
                else:
                    self.assertEqual(result['reason'], 'attribution_subject_requires_review')

    def test_ambiguous_groups_never_fall_back_to_broad_legacy_attribution(self):
        fixture = next(item for item in ACTUAL_SUBJECT_REGRESSIONS if item['book'] == 'ibnmajah')
        versions = {language: {'quotation': text, 'row': row(113, text), 'metadata': {'sections': {}}}
                    for language, text in fixture['quotations'].items()}
        with mock.patch.object(importer, 'explicit_report_evidence', return_value=None):
            result = importer.classify_group(versions)
        self.assertEqual(result['reason'], 'attribution_subject_requires_review')

    def test_introduction_gate_and_verified_span_order_survive_ambiguity_handling(self):
        fixture = next(item for item in ACTUAL_SUBJECT_REGRESSIONS if item['book'] == 'ibnmajah')
        versions = {language: {'quotation': text, 'row': row(113, text, book=0),
                               'metadata': {'sections': {'0': 'Introduction'}}}
                    for language, text in fixture['quotations'].items()}
        with mock.patch.object(importer, 'explicit_report_evidence') as helper:
            self.assertEqual(importer.classify_group(versions)['reason'], 'source_introduction_requires_bounded_narration_review')
            helper.assert_not_called()
        text = versions['eng']['quotation']
        decision = {'source_text_sha256': importer.sha(text.encode()), 'quotation_spans': [[0, len(text)]]}
        # The normal caller verifies the exact source before marking a span reviewed.
        quotation, _, _ = importer.apply_reviewed_span(text, decision)
        versions['eng'].update(quotation=quotation, reviewed_source_span=decision)
        with mock.patch.object(importer, 'explicit_report_evidence') as helper:
            self.assertEqual(importer.classify_group(versions)['reason'], 'reviewed_explicit_source_attribution')
            helper.assert_not_called()

    def test_explicit_tirmidhi_grading_tail_is_source_commentary(self):
        self.plan['books'] = ['tirmidhi']
        importer.save_json(self.root, importer.PLAN, self.plan)
        inputs = self.inputs(['tirmidhi'])
        inputs['editions/ara-tirmidhi.json'] = importer.encoded(source_data('tirmidhi', [
            row(1, 'TEST قال رسول الله TEST quotation. هذا حديث حسن صحيح TEST compiler analysis')]))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary['registered_occurrences'], 1)
        records = [json.loads(line) for path in (self.root / 'materials').glob('*/records.jsonl') for line in path.read_text().splitlines()]
        own = next(item for item in records[0]['language_versions'] if item['language'] == 'ar')
        self.assertNotIn('compiler analysis', own['text'])
        self.assertTrue(any('compiler analysis' in item['text'] for item in own['comments']))

    def test_pending_english_context_does_not_hide_valid_arabic_or_become_matn(self):
        self.plan['books'] = ['malik']
        importer.save_json(self.root, importer.PLAN, self.plan)
        inputs = self.inputs(['malik'])
        source = 'Malik said TEST independent legal discussion. The Prophet said TEST embedded report.'
        inputs['editions/eng-malik.json'] = importer.encoded(source_data('malik', [row(1, source)]))
        inputs['editions/urd-malik.json'] = importer.encoded(source_data('malik', [row(1, 'TEST Urdu translation')]))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary['registered_occurrences'], 1)
        records = [item for group in load_public_materials(self.root)['groups'] for item in group]
        own = next(item for item in records[0]['language_versions'] if item['language'] == 'en')
        self.assertIsNone(own['text'])
        self.assertEqual(own['quotation_status'], 'boundary_pending')
        self.assertEqual(own['comments'][0]['text'], source)
        self.assertEqual(own['comments'][0]['scope'], 'source_context_not_narration')
        self.assertIn('narration boundary', next(item for item in language_readings(records[0]) if item['language'] == 'en')['qualification'])

    def test_missing_book_zero_reference_does_not_extend_muslim_introduction(self):
        item = {'row': row(125, book=0), 'metadata': {'sections': {'0': 'Introduction'},
                'section_details': {'0': {'hadithnumber_first': 1, 'hadithnumber_last': 92}}}}
        original = copy.deepcopy(item)
        self.assertIsNone(importer.source_section_name(item))
        self.assertEqual(item, original)
        item['row']['hadithnumber'] = 15
        self.assertEqual(importer.source_section_name(item), 'Introduction')
        item['row']['hadithnumber'] = 0
        self.assertEqual(importer.source_section_name(item), 'Introduction')

    def test_reviewed_excerpt_is_hash_bound_and_preserves_context_on_both_sides(self):
        text = 'TEST Quran/context. TEST Prophetic quotation. TEST compiler discussion.'
        start, end = text.index('TEST Prophetic'), text.index(' TEST compiler')
        decision = {'source_text_sha256': importer.sha(text.encode()), 'quotation_spans': [[start, end]]}
        quotation, notes, spans = importer.apply_reviewed_span(text, decision)
        self.assertEqual(quotation, text[start:end])
        self.assertEqual(notes, [text[:start], text[end:]])
        self.assertEqual(spans['quotation'], [start, end])
        with self.assertRaisesRegex(ValueError, 'source hash changed'):
            importer.apply_reviewed_span(text + 'x', decision)

    def test_reviewed_separate_reports_preserve_every_intervening_note(self):
        from validate_fawaz_sources import verify_partition, verify_report_components
        text = 'TEST context. TEST report A. TEST compiler note. TEST report B 🧪. TEST ending.'
        spans = [[text.index('TEST report A'), text.index(' TEST compiler')],
                 [text.index('TEST report B'), text.index(' TEST ending')]]
        decision = {'source_text_sha256': importer.sha(text.encode()), 'quotation_spans': spans,
                    'source_report_count': 2, 'source_report_boundaries': spans}
        quotation, notes, evidence = importer.apply_reviewed_span(text, decision)
        self.assertEqual(notes, ['TEST context. ', ' TEST compiler note. ', ' TEST ending.'])
        self.assertNotIn('compiler', quotation)
        self.assertNotIn('quotation', evidence)
        verify_partition(text, evidence, quotation, notes)
        self.assertEqual(verify_report_components(text, {
            'text_spans': evidence, 'source_report_count': 2, 'source_report_boundaries': spans},
            'multiple_source_reports'), (2, 0))
        one_report = {**decision, 'source_report_count': 1, 'source_passage_boundaries': spans,
                      'source_report_relationship': 'separate_passages_of_one_source_report'}
        one_report.pop('source_report_boundaries')
        single_text, single_notes, single_evidence = importer.apply_reviewed_span(text, one_report)
        self.assertEqual((single_text, single_notes), (quotation, notes))
        self.assertNotIn('source_report_boundaries', single_evidence)
        self.assertEqual(verify_report_components(text, {'text_spans': single_evidence,
            'source_report_count': 1}, 'disjoint_source_spans'), (0, 0))
        for mutation in ({'source_report_count': 1}, {'source_report_boundaries': [spans[0]]},
                         {'quotation_spans': list(reversed(spans)), 'source_report_boundaries': list(reversed(spans))}):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                importer.apply_reviewed_span(text, {**decision, **mutation})

    def test_source_attribution_pending_keeps_unnamed_subject_out_of_counterpart_text(self):
        self.plan.update(books=['nasai'], languages=list(importer.LANGUAGES))
        importer.save_json(self.root, importer.PLAN, self.plan)
        inputs, decisions = self.inputs(['nasai']), []
        for prefix in self.plan['languages']:
            text = 'TEST explicitly named source report' if prefix == 'ben' else 'TEST ' + prefix + ' unnamed subject did this.'
            inputs['editions/' + prefix + '-nasai.json'] = importer.encoded(source_data('nasai', [row(1, text)]))
            d = {'provider_book':'nasai', 'provider_edition':prefix+'-nasai', 'typed_hadithnumber':'1',
                 'source_text_sha256':importer.sha(text.encode()), 'quotation_spans':[[0,len(text)]]}
            if prefix != 'ben':
                d.update(action='source_attribution_pending', quotation_spans=[], reason='TEST source leaves its subject unnamed')
            decisions.append(d)
        importer.save_json(self.root, 'catalog/fawaz-reviewed-spans.json', {
            'schema':'hadith-bank-fawaz-reviewed-spans-v1', 'repository':importer.REPOSITORY,
            'revision':importer.REVISION, 'decisions':decisions})
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary['registered_occurrences'],1)
        records = [item for group in load_public_materials(self.root)['groups'] for item in group]
        canonical = next(json.loads(line) for path in (self.root/'materials').glob('*/records.jsonl')
                         for line in path.read_text().splitlines())
        record = records[0]
        self.assertIsNone(record['text_arabic'])
        for version in record['language_versions']:
            if version['language'] == 'bn':
                self.assertEqual(version['text'],'TEST explicitly named source report')
            else:
                self.assertIsNone(version['text'])
                self.assertEqual(version['quotation_status'],'attribution_pending')
                prefix = version['source']['provider_edition'].split('-')[0]
                self.assertEqual(version['comments'][0]['text'],'TEST ' + prefix + ' unnamed subject did this.')
                self.assertEqual(canonical['source']['language_availability'][version['language']],
                                 'attribution_pending_source_context')

    def test_numbered_companion_report_keeps_own_speaker_and_unreviewed_siblings(self):
        inputs = self.inputs()
        text = 'TEST Umar said: TEST attributed saying. TEST compiler explanation.'
        end = text.index(' TEST compiler')
        inputs['editions/eng-bukhari.json'] = importer.encoded(source_data('bukhari', [row(1, text)]))
        decision = {'provider_book':'bukhari', 'provider_edition':'eng-bukhari', 'typed_hadithnumber':'1',
            'source_text_sha256':importer.sha(text.encode()), 'quotation_spans':[[0,end]],
            'report_type':'companion_report',
            'reported_speakers':[{'name_as_supplied':'Umar', 'role':'companion', 'source_spans':[[5,9]]}],
            'report_classification_note':'TEST This source attributes the saying to Umar, a Companion.'}
        importer.save_json(self.root, 'catalog/fawaz-reviewed-spans.json', {
            'schema':'hadith-bank-fawaz-reviewed-spans-v1', 'repository':importer.REPOSITORY,
            'revision':importer.REVISION, 'decisions':[decision]})
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary['registered_occurrences'], 1)
        canonical = next(json.loads(line) for path in (self.root/'materials').glob('*/records.jsonl')
                         for line in path.read_text().splitlines())
        self.assertEqual(canonical['content_kind'], 'source_numbered_attributed_report')
        self.assertEqual(canonical['report_types'], ['companion_report'])
        own = next(v for v in canonical['language_versions'] if v['language'] == 'en')
        self.assertEqual(own['text'], text[:end])
        self.assertEqual(own['source']['reported_speakers'], decision['reported_speakers'])
        self.assertEqual(own['comments'][0]['text'], text[end:])
        self.assertIn('attributes the saying to Umar', next(v for v in language_readings(canonical) if v['language'] == 'en')['qualification'])
        self.assertTrue(all(v['text'] is None and v['quotation_status'] == 'attribution_pending'
                            for v in canonical['language_versions'] if v['language'] != 'en'))
        from build_reader import record_type_info
        self.assertEqual(record_type_info(canonical)['label'], 'Report or saying')
        for mutation in (
            {'reported_speakers':[{'name_as_supplied':'Invented', 'role':'companion', 'source_spans':[[5,9]]}]},
            {'reported_speakers':[{'name_as_supplied':'compiler', 'role':'other', 'source_spans':[[end,len(text)]]}]},
            {'reported_speakers':[{'name_as_supplied':None, 'role':'prophet', 'source_spans':[]}]},
            {'report_classification_note':''},
        ):
            with self.assertRaises(ValueError):
                importer.apply_reviewed_span(text, {**decision, **mutation})

    def test_source_content_mismatch_does_not_create_false_arabic_or_english_counterparts(self):
        self.plan.update(books=['malik'], languages=list(importer.LANGUAGES))
        importer.save_json(self.root, importer.PLAN, self.plan)
        inputs, decisions = self.inputs(['malik']), []
        for prefix in self.plan['languages']:
            text = 'TEST Urdu Prophetic report' if prefix == 'urd' else 'TEST independent ruling ' + prefix
            inputs['editions/' + prefix + '-malik.json'] = importer.encoded(source_data('malik', [row(224, text)]))
            decision = {'provider_book': 'malik', 'provider_edition': prefix + '-malik', 'typed_hadithnumber': '224',
                        'source_text_sha256': importer.sha(text.encode()), 'quotation_spans': [[0, len(text)]]}
            if prefix != 'urd':
                decision.update(action='source_context_only', quotation_spans=[], reason='TEST verified provider content mismatch')
            decisions.append(decision)
        importer.save_json(self.root, 'catalog/fawaz-reviewed-spans.json', {
            'schema': 'hadith-bank-fawaz-reviewed-spans-v1', 'repository': importer.REPOSITORY,
            'revision': importer.REVISION, 'decisions': decisions})
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary['registered_occurrences'], 1)
        records = [item for group in load_public_materials(self.root)['groups'] for item in group]
        record = records[0]
        self.assertEqual(record['language'], 'ur')
        self.assertIsNone(record['text_arabic'])
        for view in language_readings(record):
            if view['language'] == 'ur':
                self.assertEqual(view['text'], 'TEST Urdu Prophetic report')
            else:
                self.assertIsNone(view['text'])
                self.assertEqual(view['scope'], 'source_context')
                self.assertIn('not a translation or Arabic counterpart', view['qualification'])
                self.assertTrue(view['comments'][0]['text'].startswith('TEST independent ruling'))
        from counterpart_coverage import availability_for
        self.assertEqual(availability_for(record), {'arabic': 'missing', 'english': 'missing'})

    def test_reviewed_abbreviation_preserves_own_wording_and_language_owned_reference(self):
        inputs = self.inputs()
        own_text = 'TEST abbreviated source wording with TEST previous-chain citation'
        for prefix in self.plan['languages']:
            text = own_text if prefix == 'ara' else 'TEST ' + prefix + ' supplied short wording'
            inputs['editions/' + prefix + '-bukhari.json'] = importer.encoded(source_data('bukhari', [row(2, text)]))
        decision = {'provider_book': 'bukhari', 'provider_edition': 'ara-bukhari', 'typed_hadithnumber': '2',
                    'source_text_sha256': importer.sha(own_text.encode()), 'quotation_spans': [[0, len(own_text)]],
                    'quotation_kind': 'source_explicit_abbreviated_transmission',
                    'source_reference': {'parent_source': {'provider_edition': 'ara-bukhari', 'typed_hadithnumber': '1'},
                        'reference_evidence': [{'source': {'provider_edition': 'ara-bukhari'}, 'text': 'TEST previous-chain citation'}]}}
        importer.save_json(self.root, 'catalog/fawaz-reviewed-spans.json', {
            'schema': 'hadith-bank-fawaz-reviewed-spans-v1', 'repository': importer.REPOSITORY,
            'revision': importer.REVISION, 'decisions': [decision]})
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary['registered_occurrences'], 1)
        records = [json.loads(line) for path in (self.root / 'materials').glob('*/records.jsonl')
                   for line in path.read_text().splitlines()]
        self.assertEqual(len(records), 1)
        for version in records[0]['language_versions']:
            if version['language'] == 'ar':
                self.assertEqual(version['text'], own_text)
                self.assertEqual(version['scope'], 'source_excerpt')
                self.assertEqual(version['quotation_status'], 'abbreviated_source_report')
                self.assertEqual(version['source']['quotation_kind'], 'source_explicit_abbreviated_transmission')
                reference = version['references'][1]
                self.assertEqual(reference['source_citation'], 'TEST previous-chain citation')
                self.assertEqual(reference['url'], importer.entry_url('ara-bukhari', 1))
                self.assertFalse(reference['identity_merged'])
                self.assertFalse(reference['parent_text_inserted'])
            else:
                self.assertEqual(len(version['references']), 1)
                self.assertEqual(version['quotation_status'], 'bounded')

    def test_partial_book_never_published_and_saved_checksums_are_required(self):
        inputs = self.inputs()
        del inputs["editions/urd-bukhari.json"]
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary["registered_occurrences"], 0)
        self.assertEqual(summary["pending_books"], ["bukhari"])
        item = self.state["inputs"]["editions/ara-bukhari.json"]
        path = self.root / item["path"]
        path.write_bytes(path.read_bytes() + b"TEST corrupt")
        with self.assertRaisesRegex(ValueError, "checksum"):
            importer.run(self.args())
        self.assertFalse((self.root / "materials").exists())

    def test_swapped_language_snapshot_descriptors_are_rejected_before_export(self):
        self.seed()
        inputs = self.state["inputs"]
        left, right = "editions/ara-bukhari.json", "editions/eng-bukhari.json"
        inputs[left], inputs[right] = inputs[right], inputs[left]
        importer.save_json(self.root, importer.IMPORT + "/state.json", self.state)
        with self.assertRaisesRegex(ValueError, "input key does not match"):
            importer.run(self.args())
        with self.assertRaisesRegex(ValueError, "input key does not match"):
            importer.export_saved(self.root, self.plan, self.state)
        self.assertFalse((self.root / "materials").exists())

    def test_fetch_is_whole_book_bounded_and_resumes_without_reacquiring_inputs(self):
        self.plan["books"] = ["bukhari", "malik"]
        importer.save_json(self.root, importer.PLAN, self.plan)
        inputs = self.inputs(self.plan["books"])
        def fetch(key):
            return inputs[key], {"url": importer.provider_url(key), "retrieved_at": "TEST"}
        with mock.patch.object(importer, "fetch_bytes", side_effect=fetch) as request:
            first, code = importer.run(self.args(fetch=True, export_only=False, max_books=1))
            self.assertEqual(code, 0)
            self.assertEqual(first["completed_books"], ["bukhari"])
            self.assertEqual(request.call_count, len(importer.DOCUMENTS) + 3)
            request.reset_mock()
            second, code = importer.run(self.args(fetch=True, export_only=False, max_books=1))
            self.assertEqual(code, 0)
            self.assertTrue(second["complete"])
            self.assertEqual(request.call_count, 3)
            self.assertTrue(all(call.args[0].endswith("-malik.json") for call in request.call_args_list))
        with mock.patch.object(importer, "fetch_bytes", side_effect=AssertionError("offline must not fetch")):
            before = {path.relative_to(self.root).as_posix(): importer.sha(path.read_bytes()) for path in (self.root / "materials").rglob("*") if path.is_file()}
            offline, _ = importer.run(self.args())
            after = {path.relative_to(self.root).as_posix(): importer.sha(path.read_bytes()) for path in (self.root / "materials").rglob("*") if path.is_file()}
            self.assertEqual(before, after)
            self.assertEqual(offline, second)

    def test_later_access_failure_preserves_completed_book_and_does_not_retry(self):
        self.plan["books"] = ["bukhari", "malik"]
        importer.save_json(self.root, importer.PLAN, self.plan)
        inputs = self.inputs(self.plan["books"])
        def fetch(key):
            if key == "editions/ara-malik.json":
                raise importer.FetchFailure("TEST HTTP 403", access_denied=True)
            return inputs[key], {"url": importer.provider_url(key), "retrieved_at": "TEST"}
        with mock.patch.object(importer, "fetch_bytes", side_effect=fetch):
            summary, code = importer.run(self.args(fetch=True, export_only=False))
        self.assertEqual(code, 1)
        self.assertEqual(summary["completed_books"], ["bukhari"])
        with mock.patch.object(importer, "fetch_bytes", side_effect=AssertionError("denial must not retry")):
            offline, code = importer.run(self.args())
            self.assertEqual(code, 0)
            self.assertEqual(offline, summary)
            with self.assertRaisesRegex(ValueError, "access denials"):
                importer.run(self.args(fetch=True, export_only=False, retry_failed=True))

    def test_invalid_edition_is_preserved_as_rejected_evidence_not_active_input(self):
        inputs = self.inputs()
        inputs["editions/urd-bukhari.json"] = importer.encoded({"metadata": {}, "hadiths": []})
        with mock.patch.object(importer, "fetch_bytes", side_effect=lambda key: (inputs[key], {"url": importer.provider_url(key), "retrieved_at": "TEST"})):
            summary, code = importer.run(self.args(fetch=True, export_only=False))
        state = importer.read_json(self.root, importer.IMPORT + "/state.json")
        self.assertEqual(code, 1)
        self.assertEqual(summary["registered_occurrences"], 0)
        self.assertNotIn("editions/urd-bukhari.json", state["inputs"])
        self.assertIn("editions/urd-bukhari.json", state["rejected_inputs"])
        self.assertEqual(importer.run(self.args())[1], 0)

    def test_adoption_verifies_pinned_receipts_and_shards_preserve_ids(self):
        directory = self.root / "seed"
        directory.mkdir()
        raw = self.inputs()["editions/ara-bukhari.json"]
        (directory / "ara-bukhari.json").write_bytes(raw)
        receipt = {"url": importer.provider_url("editions/ara-bukhari.json"), "commit": importer.REVISION,
                   "sha256": importer.sha(raw), "bytes": len(raw), "retrieved_at": "TEST"}
        (directory / "ara-bukhari.receipt.json").write_bytes(importer.encoded(receipt))
        self.assertEqual(importer.adopt_input(self.root, directory, "editions/ara-bukhari.json")[0], raw)
        receipt["commit"] = "0" * 40
        (directory / "ara-bukhari.receipt.json").write_bytes(importer.encoded(receipt))
        with self.assertRaisesRegex(ValueError, "revision/URL"):
            importer.adopt_input(self.root, directory, "editions/ara-bukhari.json")
        records = [{"id": "TEST-" + str(i), "edition": importer.EDITION, "text": "TEST " * 50} for i in range(4)]
        shards = importer.canonical_shards(records, limit=450)
        recovered = [json.loads(line) for _, data in shards for line in data.splitlines()]
        self.assertEqual([row["id"] for row in recovered], [row["id"] for row in records])
        self.assertTrue(all(len(data) <= 450 for _, data in shards))
        with self.assertRaisesRegex(ValueError, "exceeds"):
            importer.canonical_shards(records, limit=10)


if __name__ == "__main__":
    unittest.main()
