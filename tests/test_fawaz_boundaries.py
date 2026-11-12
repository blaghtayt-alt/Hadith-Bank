"""Source-shaped TEST fixtures; compiler phrases are source metadata, not new hadiths.

Cases name pinned provider IDs to document the observed structure. Synthetic
TEST narration text keeps these tests small and independent of bulk downloads.
The separate saved-source audit checks the complete immutable source rows.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from fawaz_boundaries import split_source_reading


class FawazBoundaryTests(unittest.TestCase):
    def assert_partition(self, original, result):
        self.assertIsNotNone(result)
        spans = result['spans']
        quotations, notes = spans['quotation_spans'], spans['notes']
        ordered = sorted([(start, end, 'quotation') for start, end in quotations] +
                         [(start, end, 'note') for start, end in notes])
        cursor, pieces = 0, []
        for start, end, _ in ordered:
            self.assertEqual(start, cursor)
            self.assertGreater(end, start)
            pieces.append(original[start:end])
            cursor = end
        self.assertEqual(cursor, len(original))
        self.assertEqual(''.join(pieces), original)
        self.assertEqual(result['quotation'], ''.join(original[s:e] for s, e in quotations))
        self.assertEqual(result['notes'], [original[s:e] for s, e in notes])
        self.assertFalse(spans['independent_attribution_assessment'])
        if result['pending_reason']:
            self.assertEqual(result['quotation'], '')
            self.assertEqual(result['notes'], [original])

    def split(self, text, book, language):
        result = split_source_reading(text, book, language)
        self.assert_partition(text, result)
        return result

    def test_unhandled_books_and_languages_keep_existing_language_specific_rules(self):
        for book, language in [('abudawud', 'ar'), ('tirmidhi', 'bn'), ('tirmidhi', 'ur'), ('malik', 'bn')]:
            self.assertIsNone(split_source_reading('TEST exact source', book, language))
        self.assertIsNone(split_source_reading('', 'malik', 'en'))

    def test_arabic_tirmidhi_grade_before_named_compiler_is_note(self):
        text = 'حَدَّثَنَا TEST عَنِ النَّبِيِّ "TEST exact matn". هَذَا حَدِيثٌ حَسَنٌ. قَالَ أَبُو عِيسَى TEST note.'
        result = self.split(text, 'tirmidhi', 'ar')
        self.assertEqual(result['quotation'], text[:text.index('هَذَا')])
        self.assertEqual(result['notes'], [text[text.index('هَذَا'):]])
        self.assertIsNone(result['pending_reason'])

    def test_arabic_tirmidhi_parallel_list_precedes_grade_and_stays_a_note(self):
        text = 'حَدَّثَنَا TEST "TEST exact matn". قَالَ وَفِي الْبَابِ عَنْ TEST witness. وَهَذَا حَدِيثٌ صَحِيحٌ.'
        result = self.split(text, 'tirmidhi', 'ar')
        self.assertEqual(result['quotation'], text[:text.index('قَالَ')])
        self.assertNotIn('TEST witness', result['quotation'])
        self.assertIn('parallel_reference_list', result['spans']['rule'])

    def test_tirmidhi_3659_alternate_report_comment_precedes_grade(self):
        text = 'حَدَّثَنَا TEST "TEST exact matn". وَقَدْ رُوِيَ هَذَا الْحَدِيثُ TEST other chain. هَذَا حَدِيثٌ غَرِيبٌ.'
        result = self.split(text, 'tirmidhi', 'ar')
        self.assertEqual(result['quotation'], text[:text.index('وَقَدْ')])
        self.assertIn('compiler_parallel_report', result['spans']['rule'])

    def test_tirmidhi_grade_or_compiler_only_text_is_source_context(self):
        for text in ['هَذَا حَدِيثٌ حَسَنٌ TEST metadata.', 'قَالَ أَبُو عِيسَى TEST compiler discussion.']:
            result = self.split(text, 'tirmidhi', 'ar')
            self.assertEqual(result['pending_reason'], 'compiler_material_precedes_established_narration')

    def test_compiler_phrase_inside_unclosed_quotation_is_not_silently_cut(self):
        text = 'حَدَّثَنَا TEST "TEST quotation هَذَا حَدِيثٌ حَسَنٌ TEST rest".'
        result = self.split(text, 'tirmidhi', 'ar')
        self.assertIn('unclosed_source_quotation', result['pending_reason'])

    def test_bukhari_6119_name_gloss_is_exact_disjoint_note_and_isnad_resumes(self):
        text = ('حَدَّثَنَا TEST عَنْ مَوْلَى أَنَسٍ ـ قَالَ أَبُو عَبْدِ اللَّهِ '
                'اسْمُهُ عَبْدُ اللَّهِ بْنُ أَبِي عُتْبَةَ ـ سَمِعْتُ أَبَا سَعِيدٍ TEST narration.')
        result = self.split(text, 'bukhari', 'ar')
        self.assertEqual(len(result['spans']['quotation_spans']), 2)
        self.assertNotIn('quotation', result['spans'])
        self.assertTrue(result['spans']['disjoint_quotation'])
        self.assertIn('سَمِعْتُ أَبَا سَعِيدٍ', result['quotation'])
        self.assertNotIn('اسْمُهُ', result['quotation'])
        self.assertTrue(result['notes'][0].startswith('ـ'))
        self.assertTrue(result['notes'][0].endswith('ـ'))

    def test_bukhari_313_alternate_isnad_is_not_deleted_as_a_gloss(self):
        text = ('حَدَّثَنَا TEST عَنْ حَفْصَةَ ـ قَالَ أَبُو عَبْدِ اللَّهِ أَوْ هِشَامِ بْنِ '
                'حَسَّانَ عَنْ حَفْصَةَ، عَنْ أُمِّ عَطِيَّةَ ـ TEST narration.')
        result = self.split(text, 'bukhari', 'ar')
        self.assertEqual(result['quotation'], text)
        self.assertEqual(result['notes'], [])
        self.assertIn('alternate_isnad', result['spans']['rule'])

    def test_bukhari_initial_and_parallel_chain_introducers_are_preserved(self):
        for prefix in ['', 'حَدَّثَنَا TEST عَنِ الزُّهْرِيِّ ح ']:
            text = prefix + 'قَالَ أَبُو عَبْدِ اللَّهِ وَقَالَ اللَّيْثُ حَدَّثَنِي TEST عَنِ النَّبِيِّ TEST narration.'
            result = self.split(text, 'bukhari', 'ar')
            self.assertEqual(result['quotation'], text)
            self.assertFalse(result['notes'])

    def test_bukhari_explicit_terminal_compiler_note_is_separated(self):
        text = 'حَدَّثَنَا TEST عَنِ النَّبِيِّ "TEST narration". قَالَ أَبُو عَبْدِ اللَّهِ TEST compiler note.'
        result = self.split(text, 'bukhari', 'ar')
        self.assertEqual(result['quotation'], text[:text.index('قَالَ')])
        self.assertEqual(len(result['spans']['quotation_spans']), 1)
        self.assertEqual(result['spans']['quotation'], result['spans']['quotation_spans'][0])

    def test_bukhari_ambiguous_inline_compiler_context_stays_pending(self):
        text = 'حَدَّثَنَا TEST عَنِ النَّبِيِّ TEST قَالَ أَبُو عَبْدِ اللَّهِ TEST unexplained insertion.'
        result = self.split(text, 'bukhari', 'ar')
        self.assertIsNotNone(result['pending_reason'])

    def test_malik_13_same_name_narrator_is_not_misread_as_compiler(self):
        text = 'وَحَدَّثَنِي TEST عَنْ أَبِي سُهَيْلٍ TEST ـ قَالَ مَالِكٌ وَالِدُ أَبِي سُهَيْلٍ ـ TEST continuation.'
        result = self.split(text, 'malik', 'ar')
        self.assertEqual(result['quotation'], text)
        self.assertEqual(result['notes'], [])
        self.assertIn('not_compiler', result['spans']['rule'])

    def test_malik_244_attribution_uncertainty_is_never_removed(self):
        text = 'وَحَدَّثَنِي TEST - قَالَ مَالِكٌ لاَ أَدْرِي أَعَنِ النَّبِيِّ أَمْ لاَ - TEST report.'
        result = self.split(text, 'malik', 'ar')
        self.assertEqual(result['pending_reason'], 'source_attribution_or_continuation_explicitly_qualified')

    def test_malik_1744_qualified_narration_ending_keeps_full_context(self):
        arabic = 'وَحَدَّثَنِي TEST عَنِ النَّبِيِّ TEST وَإِذَا أَبْغَضَ اللَّهُ الْعَبْدَ. قَالَ مَالِكٌ لاَ أَحْسَبُهُ إِلاَّ أَنَّهُ قَالَ TEST.'
        english = 'Yahya related to me TEST ' + ('narrative context ' * 5) + '. When Allah is angry with a slave, Malik said, TEST qualified ending.'
        for text, language in [(arabic, 'ar'), (english, 'en')]:
            result = self.split(text, 'malik', language)
            self.assertIsNotNone(result['pending_reason'])

    def test_malik_1851_bracketed_english_gloss_retains_both_narration_spans(self):
        text = 'TEST first narrative. (Malik explained that an uqiya was forty dirhams.) TEST resumed narrative.'
        result = self.split(text, 'malik', 'en')
        self.assertEqual(len(result['spans']['quotation_spans']), 2)
        self.assertIn('TEST first narrative.', result['quotation'])
        self.assertIn('TEST resumed narrative.', result['quotation'])
        self.assertNotIn('Malik', result['quotation'])
        self.assertIsNone(result['pending_reason'])

    def test_malik_1851_unbracketed_arabic_gloss_does_not_discard_resumed_report(self):
        text = 'وَحَدَّثَنِي TEST عَنِ النَّبِيِّ TEST. قَالَ مَالِكٌ وَالأُوقِيَّةُ أَرْبَعُونَ دِرْهَمًا. قَالَ فَرَجَعْتُ TEST resumed narration.'
        result = self.split(text, 'malik', 'ar')
        self.assertEqual(result['pending_reason'], 'unbracketed_inline_gloss_with_resumed_narration')

    def test_malik_696_1015_1465_mixed_english_needs_own_spans(self):
        fixtures = {
            '696': 'Malik was asked whether TEST legal discussion. TEST embedded report. Malik said, TEST later ruling.',
            '1015': 'Yahya related to me from Malik that what he preferred TEST legal discussion ' + ('TEST law ' * 6) + '. Malik said, TEST law. TEST later narration.',
            '1465': 'Malik said, TEST generally agreed legal position. TEST long law. TEST embedded reported lottery.',
        }
        for identifier, text in fixtures.items():
            with self.subTest(provider_id=identifier):
                result = self.split(text, 'malik', 'en')
                self.assertEqual(result['pending_reason'], 'mixed_compiler_discussion_requires_language_local_narration_spans')

    def test_malik_696_clean_arabic_never_transfers_its_boundary_to_english(self):
        arabic = 'وَحَدَّثَنِي TEST عَنْ رَسُولِ اللَّهِ TEST reported practice. قَالَ مَالِكٌ لاَ يَخْرُجُ TEST legal comment.'
        english = 'Malik was asked whether TEST law. TEST embedded report. Malik said, TEST ruling.'
        ar = self.split(arabic, 'malik', 'ar')
        en = self.split(english, 'malik', 'en')
        self.assertTrue(ar['quotation'])
        self.assertFalse(en['quotation'])
        self.assertIsNone(ar['pending_reason'])
        self.assertIsNotNone(en['pending_reason'])

    def test_malik_compiler_introducing_further_report_is_not_plain_tail(self):
        text = 'وَحَدَّثَنِي TEST "TEST first report". قَالَ مَالِكٌ قَالَ هِشَامٌ قَالَتْ عَائِشَةُ TEST next narrative.'
        result = self.split(text, 'malik', 'ar')
        self.assertEqual(result['pending_reason'], 'compiler_cue_introduces_or_resumes_narrational_context')

    def test_abudawud_5210_compiler_transmits_attribution_after_narrator_heading(self):
        text = 'Narrated TEST narrator: AbuDawud said: TEST transmitter traced this tradition back to the Prophet: TEST exact report.'
        result = self.split(text, 'abudawud', 'en')
        self.assertEqual(result['quotation'], text)
        self.assertEqual(result['notes'], [])
        self.assertIn('transmitted_attribution', result['spans']['rule'])

    def test_abudawud_named_compiler_tail_still_uses_its_own_language_boundary(self):
        text = 'Narrated TEST narrator: "TEST report". AbuDawud said: TEST compiler discussion.'
        result = self.split(text, 'abudawud', 'en')
        self.assertEqual(result['quotation'], text[:text.index('AbuDawud')])
        self.assertEqual(result['notes'], ['AbuDawud said: TEST compiler discussion.'])

    def test_abudawud_2306_explicit_personal_opinion_is_a_separate_note(self):
        text = 'حَدَّثَنَا TEST عَنِ النَّبِيِّ TEST report. قَالَ ابْنُ شِهَابٍ وَلاَ أَرَى بَأْسًا أَنْ تَتَزَوَّجَ حِينَ وَضَعَتْ TEST ruling.'
        result = self.split(text, 'abudawud', 'ar')
        self.assertEqual(result['quotation'], text[:text.index('قَالَ')])
        self.assertIn('ابْنُ شِهَابٍ', result['notes'][0])
        self.assertIsNone(split_source_reading('حَدَّثَنَا ابْنُ شِهَابٍ TEST ordinary chain.', 'abudawud', 'ar'))

    def test_urdu_and_bengali_anas_ibn_malik_are_not_compiler_cues(self):
        self.assertIsNone(split_source_reading('انس بن مالک کہتے ہیں TEST narrator report.', 'malik', 'ur'))
        self.assertIsNone(split_source_reading('আনাস ইবন মালিক (রাঃ) বলেন TEST narrator report.', 'malik', 'bn'))

    def test_english_anas_ibn_bin_or_b_malik_are_not_compiler_cues(self):
        for name in ('Anas ibn Malik', 'Anas bin Malik', 'Anas b. Malik', 'Anas b.Malik'):
            with self.subTest(name=name):
                text = 'Yahya related to me from Malik from TEST that ' + name + ' said, "TEST narration."'
                self.assertIsNone(split_source_reading(text, 'malik', 'en'))

    def test_malik_1788_exact_source_narrator_name_is_not_a_compiler_boundary(self):
        # Exact pinned eng-malik provider row1788. Its missing final quotation
        # mark is preserved; it does not turn Anas ibn Malik into the compiler.
        text = ('Malik related to me from Humayd at-Tawil that Anas ibn Malik said, '
                '"The Messenger of Allah, may Allah bless him and grant him peace, was cupped. '
                'Abu Tayba cupped him, and the Messenger of Allah, may Allah bless him and grant him peace, '
                'ordered him to be given a sa of dates and ordered his family to lessen what he paid '
                'them for his kitaba or kharaj')
        self.assertIsNone(split_source_reading(text, 'malik', 'en'))

    def test_english_anas_narration_does_not_hide_a_later_true_compiler_tail(self):
        prefix = ('Yahya related to me from Malik from TEST that Anas ibn Malik said, '
                  '"TEST complete source narration." ')
        tail = 'Malik said, "TEST separately attributed compiler ruling."'
        result = self.split(prefix + tail, 'malik', 'en')
        self.assertEqual(result['quotation'], prefix)
        self.assertEqual(result['notes'], [tail])
        self.assertIsNone(result['pending_reason'])

    def test_malik_13_urdu_and_bengali_preserve_named_father(self):
        urdu = 'مالک بن ابی عامر TEST source context. مالک نے کہا TEST continuation.'
        bengali = 'TEST source তাহার পিতা মালিক (রহঃ) বলিয়াছেন TEST narration.'
        for text, language in [(urdu, 'ur'), (bengali, 'bn')]:
            result = self.split(text, 'malik', language)
            self.assertEqual(result['quotation'], text)
            self.assertFalse(result['notes'])

    def test_simple_urdu_and_bengali_compiler_tails_use_own_offsets(self):
        for prefix, tail, language in [
            (('TEST original source ' * 6) + '۔ ', 'امام مالک نے کہا TEST separate ruling.', 'ur'),
            (('TEST own Bengali source ' * 5) + '। ', 'মালিক (রহঃ) বলেনঃ TEST separate ruling.', 'bn'),
        ]:
            result = self.split(prefix + tail, 'malik', language)
            self.assertEqual(result['quotation'], prefix)
            self.assertEqual(result['notes'], [tail])
            self.assertIsNone(result['pending_reason'])

    def test_initial_urdu_and_bengali_compiler_context_is_never_stripped_to_empty_matn(self):
        for text, language in [
            ('امام مالک کہتے ہیں TEST chain or compiler context.', 'ur'),
            ('রেওয়ায়ত ৬. মালিক (রহঃ) বলিয়াছেনঃ TEST initial chain or commentary.', 'bn'),
        ]:
            result = self.split(text, 'malik', language)
            self.assertEqual(result['notes'], [text])
            self.assertIn('initial', result['pending_reason'])

    def test_urdu_and_bengali_qualification_cannot_be_removed(self):
        for text, language in [
            ('TEST source مالک کہتے ہیں کہ مجھے معلوم نہیں TEST attribution uncertainty.', 'ur'),
            ('TEST source মালিক (রহঃ) বলিয়াছেন TEST আমার জানা নাই TEST attribution uncertainty.', 'bn'),
            (('TEST source ' * 12) + '। মালিক (রহঃ) বলেন, চল্লিশ দিরহামে এক উকিয়া হয়। TEST narration resumes.', 'bn'),
        ]:
            result = self.split(text, 'malik', language)
            self.assertEqual(result['pending_reason'], 'compiler_cue_may_qualify_or_continue_source_narration')

    def test_bengali_malik_visible_reference_without_boundary_is_source_context(self):
        text = 'TEST narration and discussion ইমাম মালিক TEST reference with no supported boundary.'
        result = self.split(text, 'malik', 'bn')
        self.assertIn('no_supported_local_boundary', result['pending_reason'])

    def test_residual_bengali_named_analysis_and_initial_chains_remain_complete_context(self):
        cases = [
            ('abudawud', 'TEST report. হাদীসটি দুর্বলঃ TEST analysis আবূ দাঊদ (২২৯) TEST references.'),
            ('abudawud', 'ইমাম আবূ দাউদ (রহঃ) সূত্রে বর্ণিত। TEST initial transmitted report.'),
            ('tirmidhi', 'TEST report. আবূ ঈসা আরো বলেন TEST unidentified commentary boundary.'),
            ('tirmidhi', 'TEST narrator উপনাম আবূ ঈসা TEST a different narrator, not necessarily the compiler.'),
        ]
        for book, text in cases:
            result = self.split(text, book, 'bn')
            self.assertEqual(result['pending_reason'], 'named_source_reference_requires_bengali_local_boundary_review')

    def test_existing_bengali_splitter_keeps_ownership_of_earlier_supported_cues(self):
        for book, text in [
            ('abudawud', 'TEST report. ইমাম আবূ দাঊদ (রহঃ) বলেন TEST note.'),
            ('tirmidhi', 'TEST report. আবূ ঈসা বলেন TEST note.'),
            ('tirmidhi', 'TEST report। —সহীহ। TEST note আবূ ঈসার সন্দেহ।'),
            ('abudawud', 'TEST report. قَالَ أَبُو دَاوُدَ TEST note আবূ দাঊদ TEST reference.'),
        ]:
            self.assertIsNone(split_source_reading(text, book, 'bn'))

    def test_bengali_4356_literal_spelling_variant_is_separated_without_correction(self):
        text = 'TEST complete source clause। ইমাম আবূ দাঊদ (রহঃ) বরেন, TEST compiler commentary.'
        result = self.split(text, 'abudawud', 'bn')
        self.assertEqual(result['quotation'], text[:text.index('ইমাম')])
        self.assertIn('বরেন', result['notes'][0])
        self.assertIsNone(result['pending_reason'])

    def test_nawawi_citations_and_assessments_keep_exact_own_language_tails(self):
        for language, tail in [
            ('ar', 'رَوَاهُ التِّرْمِذِيُّ [رقم:TEST] وَقَالَ: حَدِيثٌ حَسَنٌ.'),
            ('ar', 'حَدِيثٌ حَسَنٌ، رَوَاهُ ابْنُ مَاجَهْ [رقم:TEST].'),
            ('ar', '[رَوَاهُ مُسْلِمٌ] بهذا اللفظ'),
            ('en', '[Bukhari & Muslim]'),
            ('en', 'A hasan (good) hadeeth which was related by TEST compiler.'),
            ('en', 'Related by [Muslim] in these words'),
            ('en', '[Imam an-Nawawi says:] TEST compiler assessment.'),
            ('bn', '[সহীহ্ আল-বুখারীঃ TEST, সহীহ্ মুসলিমঃ TEST]'),
            ('bn', '[এ হাদীসটি হাসান। TEST source assessment।]'),
            ('bn', '[তিরমিযীঃ TEST source with missing closing bracket.'),
        ]:
            with self.subTest(language=language, tail=tail[:20]):
                prefix = 'TEST exact source narration. '
                result = self.split(prefix + tail, 'nawawi', language)
                self.assertEqual(result['quotation'], prefix)
                self.assertEqual(result['notes'], [tail])
                self.assertIsNone(result['pending_reason'])

    def test_nawawi_16_missing_opening_quote_and_literal_br_are_preserved(self):
        prefix = 'TEST source with missing opening quote" .'
        tail = '<br>[رَوَاهُ الْبُخَارِيُّ]'
        result = self.split(prefix + tail, 'nawawi', 'ar')
        self.assertEqual(result['quotation'], prefix)
        self.assertEqual(result['notes'], [tail])
        self.assertIsNone(result['pending_reason'])

    def test_nawawi_bracket_glosses_footnote_markers_and_narrated_quran_citation_remain(self):
        for language, prefix, tail in [
            ('en', 'TEST [truly] [on the same mount] narration. ', '[Muslim]'),
            ('bn', 'TEST [১] [২] [বললে] [সূরা আস্-সাজদাহ্ঃ ১৬-১৭] narration। ', '[তিরমিযীঃ TEST]'),
        ]:
            result = self.split(prefix + tail, 'nawawi', language)
            self.assertEqual(result['quotation'], prefix)
            self.assertEqual(result['notes'], [tail])
        for language in ('ar', 'en', 'bn', 'ur'):
            self.assertIsNone(split_source_reading('TEST source with no supplied citation', 'nawawi', language))

    def test_nawawi_5_and_19_keep_explicit_variants_after_internal_citation(self):
        cases = [
            ('ar', '[رَوَاهُ الْبُخَارِيُّ] ،[وَمُسْلِمٌ] ', 'وَفِي رِوَايَةٍ لِمُسْلِمٍ: TEST variant'),
            ('ar', 'رَوَاهُ التِّرْمِذِيُّ وَقَالَ: حَدِيثٌ حَسَنٌ صَحِيحٌ. ',
             'وَفِي رِوَايَةِ غَيْرِ التِّرْمِذِيِّ: "TEST variant with source missing closing quote'),
            ('en', '[Bukhari & Muslim] ', 'In another version in Muslim it reads: TEST variant'),
            ('en', 'It was related by at-Tirmidhi, who said it was a good and sound hadeeth. ',
             'Another narration, other than that of Tirmidhi, reads: TEST variant'),
            ('bn', '[বুখারীঃ TEST, মুসলিমঃ TEST] ', 'মুসলিমের বর্ণনার ভাষা হলো এই যে, TEST variant'),
            ('bn', '[তিরমিযীঃ TEST, হাদীসটি সহীহ্ (হাসান) বলেছেন।] ',
             'তিরমিযী ছাড়া অন্য বর্ণনায় বলা হয়েছেঃ "TEST variant'),
        ]
        for language, citation, variant in cases:
            with self.subTest(language=language, variant=variant[:20]):
                prefix = 'TEST primary source narration. '
                result = self.split(prefix + citation + variant, 'nawawi', language)
                self.assertEqual(result['quotation'], prefix + variant)
                self.assertEqual(result['notes'], [citation])
                self.assertEqual(result['spans']['quotation_spans'],
                                 [[0, len(prefix)], [len(prefix + citation), len(prefix + citation + variant)]])
                self.assertTrue(result['spans']['disjoint_quotation'])
                self.assertNotIn('source_report_count', result['spans'])

    def test_nawawi_27_preserves_two_reports_and_internal_citation_as_original_source_unit(self):
        cases = [
            ('ar', 'رَوَاهُ مُسْلِمٌ [رَوَاهُ مُسْلِمٌ]. ',
             'وَعَنْ وَابِصَةَ بْنِ مَعْبَدٍ TEST second source report. ',
             'حَدِيثٌ حَسَنٌ، رَوَيْنَاهُ TEST final source assessment.'),
            ('en', '[Muslim] ',
             'And on the authority of Wabisah bin Ma’bad TEST second source report. ',
             'A good hadeeth transmitted from TEST source.'),
            ('bn', '[মুসলিমঃ ২৫৫৩] ',
             "ওয়াবেসা ইব্\u200cন মা'বাদ TEST second source report। ",
             '[এটি হচ্ছে হাসান হাদীস TEST source]'),
        ]
        for language, citation, second, tail in cases:
            with self.subTest(language=language):
                first = 'TEST first attributed source report. '
                quotation = first + citation + second
                result = self.split(quotation + tail, 'nawawi', language)
                self.assertEqual(result['quotation'], quotation)
                self.assertEqual(result['notes'], [tail])
                self.assertEqual(result['spans']['quotation_spans'], [[0, len(quotation)]])
                self.assertFalse(result['spans']['disjoint_quotation'])
                self.assertEqual(result['source_report_count'], 2)
                expected = [[0, len(first)], [len(first + citation), len(quotation)]]
                self.assertEqual(result['source_report_boundaries'], expected)
                self.assertEqual(result['spans']['source_report_boundaries'], expected)
                self.assertEqual(result['spans']['retained_internal_citation_spans'],
                                 [[len(first), len(first + citation)]])

    def test_nawawi_40_companion_advice_is_distinct_from_the_prophetic_quotation(self):
        for language, tail in [
            ('ar', 'وَكَانَ ابْنُ عُمَرَ رَضِيَ اللَّهُ عَنْهُمَا يَقُولُ: TEST advice. [رَوَاهُ الْبُخَارِيُّ]'),
            ('en', 'And Ibn Umar (may Allah be pleased with him) used to say, TEST advice. [Al-Bukhari]'),
            ('bn', 'ইবনে উমার (রাঃ) বলতেন, TEST advice। [বুখারীঃ]'),
        ]:
            with self.subTest(language=language):
                prefix = 'TEST bounded source narration. '
                result = self.split(prefix + tail, 'nawawi', language)
                self.assertEqual(result['quotation'], prefix)
                self.assertEqual(result['notes'], [tail])
                self.assertIn('companion', result['spans']['rule'])

    def test_nawawi_citation_only_or_unsupported_inline_boundary_is_not_matn(self):
        for text, language in [('[Muslim]', 'en'), ('رَوَاهُ مُسْلِمٌ TEST metadata', 'ar'),
                               ('TEST inline رواه TEST unclear continuation.', 'ar')]:
            result = self.split(text, 'nawawi', language)
            self.assertIsNotNone(result['pending_reason'])
            self.assertEqual(result['notes'], [text])


if __name__ == '__main__':
    unittest.main()
