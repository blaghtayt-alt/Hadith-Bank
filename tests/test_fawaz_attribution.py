"""Synthetic boundary fixtures, never source records or new religious quotations.

The short reporting forms are taken from observed patterns in the pinned Fawaz
editions. TEST marks deliberately artificial surrounding text and is not a
translation, hadith, or source assertion. Full-corpus evidence is audited against
the preserved files separately; these fixtures test substantive failure modes.
"""

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from fawaz_attribution import explicit_report_evidence


def versions(prefix, quotation, **other):
    return {prefix: {"quotation": quotation, **other}}


class FawazAttributionTests(unittest.TestCase):
    def evidence(self, prefix, quotation, rule=None):
        value = explicit_report_evidence(versions(prefix, quotation))
        self.assertIsNotNone(value, quotation)
        self.assertEqual(value["source_language"], prefix)
        self.assertEqual(value["text"], quotation[slice(*value["span"])])
        self.assertTrue(value["text"].strip())
        self.assertEqual(value["span_unit"], "unicode_code_points")
        self.assertFalse(value["independent_authenticity_assessment"])
        if rule:
            self.assertEqual(value["rule"], rule)
        return value

    def test_uses_quotation_only_and_does_not_mutate_versions(self):
        value = versions("ara", "TEST independent saying",
                         row={"text": "TEST قال رسول الله TEST"},
                         notes=["TEST قال رسول الله TEST"],
                         metadata={"title": "TEST قال رسول الله TEST"})
        before = copy.deepcopy(value)
        self.assertIsNone(explicit_report_evidence(value))
        self.assertEqual(value, before)
        for missing in (None, {}, {"ara": None}, {"ara": {}}, {"ara": {"quotation": None}},
                        {"ara": {"quotation": "  "}}, {"unknown": {"quotation": "The Prophet said TEST"}}):
            with self.subTest(missing=missing):
                self.assertIsNone(explicit_report_evidence(missing))

    def test_source_offsets_survive_diacritics_bidi_and_whitespace(self):
        quotation = "TEST 日本語 \u200f نَهَى\n\tرَسُولُ اللَّهِ TEST"
        value = self.evidence("ara", quotation, "arabic_explicit_speech_or_command")
        self.assertEqual(value["text"], "نَهَى\n\tرَسُولُ اللَّهِ")
        self.assertEqual(value["language"], "ar")
        self.assertNotIn("TEST", value["text"])

    def test_reported_actions_do_not_require_speech(self):
        # Observed action forms include Abu Dawud 23/42 and Ibn Majah 44/47.
        for quotation in (
            "TEST أَتَى رَسُولُ اللَّهِ صلى الله عليه وسلم TEST",
            "TEST بَالَ رَسُولُ اللَّهِ صلى الله عليه وسلم TEST",
            "TEST صَلَّى بِنَا رَسُولُ اللَّهِ TEST",
            "TEST فَأَتَاهُ النَّبِيُّ صلى الله عليه وسلم TEST",
            "TEST وَمَرَّ رَسُولُ اللَّهِ TEST",
        ):
            with self.subTest(quotation=quotation):
                self.evidence("ara", quotation, "arabic_reported_action")
        self.evidence("ara", "TEST تلا رسول الله TEST", "arabic_explicit_speech_or_command")

    def test_pledges_and_shared_practices_are_supported(self):
        # Bukhari 57; Nasai 963; Abu Dawud 1222.
        for quotation in ("TEST بايعت رسول الله TEST", "TEST سجدنا مع النبي TEST",
                          "TEST صحبت رسول الله TEST", "TEST صلينا خلف رسول الله TEST"):
            with self.subTest(quotation=quotation):
                self.evidence("ara", quotation, "arabic_direct_encounter_or_practice")

    def test_literal_salutation_and_punctuation_allow_named_predicate(self):
        for quotation in ("TEST بينا النبي ﷺ، يقول TEST", "TEST شهدت رسول الله (ﷺ) دعا TEST",
                          "TEST سمعت من النبي صلى الله عليه وسلم، يقرأ TEST"):
            with self.subTest(quotation=quotation):
                self.evidence("ara", quotation, "arabic_explicit_named_predicate")
        self.evidence("ara", "TEST فأتي به النبي ﷺ فأمر TEST", "arabic_reported_response")

    def test_attributed_dhikr_has_actual_reported_formula(self):
        # The source form occurs in Tirmidhi 825; no formula is reconstructed.
        self.evidence("ara", 'TEST أن تلبية النبي، صلى الله عليه وسلم كانت " لبيك TEST',
                      "arabic_attributed_dhikr_formula")
        self.assertIsNone(explicit_report_evidence(versions("ara", "TEST تلبية النبي TEST")))

    def test_practice_or_description_needs_a_bound_question_and_answer(self):
        # Bukhari 5045; Muslim 1726; Tirmidhi 449 supply these question forms.
        for quotation in (
            "TEST سألت أنس بن مالك عن قراءة النبي صلى الله عليه وسلم فقال كان يمد TEST",
            "TEST أخبريني عن صلاة رسول الله صلى الله عليه وسلم فقالت كانت صلاته TEST",
            "TEST سألت عائشة كيف كان قراءة النبي بالليل فقالت كل ذلك TEST",
        ):
            with self.subTest(quotation=quotation):
                value = self.evidence("ara", quotation, "arabic_question_and_reported_description")
                self.assertEqual(value["scope"], "explicit_prophetic_practice_or_description")
        for quotation in (
            "TEST سألت عن قراءة النبي TEST unanswered question",
            "TEST سألت عن قراءة النبي فقال لا أدري TEST",
            "TEST سألت عن قراءة عمر فقال كان TEST independent Companion description",
        ):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("ara", quotation)))

    def test_dialogue_requires_an_actual_direct_response(self):
        self.evidence("ara", 'TEST قالت يا رسول الله TEST question قال " TEST response',
                      "arabic_address_and_explicit_response")
        self.evidence("ara", 'TEST فقلت له يا رسول الله TEST question فقال " TEST response',
                      "arabic_address_and_explicit_response")
        for quotation in (
            'TEST قلت يا رسول الله TEST question without an answer',
            'TEST قالت يا رسول الله TEST فقال عمر " TEST independent answer',
            'TEST قالت يا رسول الله TEST فقالت " TEST another woman answers',
            'TEST لو قلت يا رسول الله TEST فقال " TEST hypothetical answer',
        ):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("ara", quotation)))

    def test_explicit_abridged_transmission_is_preserved_as_excerpt(self):
        # Abu Dawud 5240 explicitly supplies a Prophetic target and 'similarly'.
        quotation = "TEST يرفع الحديث إلى النبي صلى الله عليه وسلم نحوه TEST"
        value = self.evidence("ara", quotation, "arabic_explicit_transmission_target")
        self.assertEqual(value["scope"], "source_explicit_abbreviated_report")
        self.assertEqual(value["text"], "يرفع الحديث إلى النبي")
        self.evidence("ara", "TEST يبلغ به النبي TEST", "arabic_explicit_transmission_target")
        self.evidence("eng", "TEST A similar report was attributed it to the Prophet TEST",
                      "english_explicit_transmission_target")

    def test_bare_variants_and_physical_raising_are_not_technical_attribution(self):
        # Malik 122's يبلغ به describes how far to wipe, not marfu attribution.
        for quotation in ("TEST حدثنا TEST بهذا الإسناد مثله TEST", "TEST أين يبلغ به فقال TEST",
                          "TEST رفع الثوب TEST", "TEST كان الثوب مرفوعا TEST"):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("ara", quotation)))
        self.evidence("eng", "This hadith has been narrated as Marfu TEST", "english_technical_marfu_report")
        value = self.evidence("eng", "This hadith has been narrated as Marfu by another chain of transmitters",
                              "english_technical_marfu_report")
        self.assertEqual(value["scope"], "source_explicit_abbreviated_report")
        self.assertIsNone(explicit_report_evidence(versions("eng", "TEST the cloth was raised TEST")))

    def test_nabidh_and_independent_companion_sayings_stay_unresolved(self):
        # Regression derived from Nasai 5754, whose subject is Ubayy, not Nabi.
        for quotation in ("TEST سألت أبي بن كعب عن النبيذ فقال اشرب الماء TEST",
                          "TEST قال عمر TEST independent saying",
                          "TEST على عهد النبي TEST independent event",
                          "TEST يعرف النبي صلى الله عليه وسلم TEST name and blessing only",
                          "TEST عائشة زوج النبي TEST independent saying",
                          "TEST فاطمة بنت رسول الله TEST independent action"):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("ara", quotation)))

    def test_pulpit_possession_and_counterfactual_wishes_are_not_speech(self):
        # Muslim 7559/7560 and Ibn Majah 2727 are specific held regressions.
        for quotation in ("TEST عمر على منبر رسول الله صلى الله عليه وسلم يقول TEST",
                          "TEST وددت أن رسول الله صلى الله عليه وسلم قال TEST",
                          "TEST ثلاث لأن يكون رسول الله صلى الله عليه وسلم قال TEST",
                          "TEST ممن بايع رسول الله صلى الله عليه وسلم قال عمر TEST independent saying",
                          "TEST لما مات النبي صلى الله عليه وسلم جاء أبو بكر TEST independent event",
                          "TEST لا أدري أعن النبي صلى الله عليه وسلم قال أم لا TEST"):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("ara", quotation)))
        for quotation in ("TEST I wish the Prophet had said TEST",
                          "TEST If the Prophet came TEST",
                          "TEST the Prophet's companion said TEST",
                          "TEST Umar on the pulpit of the Prophet said TEST",
                          "TEST it was not attributed it to the Prophet TEST"):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("eng", quotation)))

    def test_english_named_actions_honorifics_and_habitual_dhikr(self):
        for quotation in (
            "TEST The Messenger of Allah (ﷺ) came TEST",
            "TEST the Prophet, may Allah bless him and grant him peace, recited TEST",
            "TEST Allah’s Messenger (may peace be upon him) has forbidden TEST",
            "TEST the Prophet (s.a.w.) would say TEST",
            "TEST he (the Holy Prophet) remarked TEST",
            "TEST the Prophet who accepted TEST",
            "TEST the Apostle of Allaah (ﷺ) did not return TEST",
            "TEST the Messenger of Allah [SAW] forbade TEST",
            "TEST Allah's Apostle (ﷺ) effected separation TEST",
            "TEST Allah's Messenger (ﷺ) met TEST",
            "TEST The Messenger of Allah set out TEST",
            # 'chose' is the spelling in the observed source; do not correct it.
            "TEST the Messenger of Allah let her chose TEST",
        ):
            with self.subTest(quotation=quotation):
                self.evidence("eng", quotation, "english_explicit_named_predicate")

    def test_english_first_person_practices_and_explicit_transmission(self):
        self.evidence("eng", "TEST We prostrated with the Messenger of Allah TEST",
                      "english_direct_encounter_or_practice")
        self.evidence("eng", "TEST I accompanied the Messenger of Allah TEST",
                      "english_direct_encounter_or_practice")
        self.evidence("eng", "TEST I prayed one night with the Messenger of Allah TEST",
                      "english_direct_encounter_or_practice")
        self.evidence("eng", "TEST reported directly from Allah's Messenger TEST",
                      "english_explicit_transmission_target")
        self.assertIsNone(explicit_report_evidence(versions("eng", "TEST I met the Prophet Moses TEST")))
        self.assertIsNone(explicit_report_evidence(versions("eng", "TEST I prayed with the Prophet's companion TEST")))
        self.assertIsNone(explicit_report_evidence(versions("eng", "TEST reported directly from the Prophet's wife TEST")))

    def test_reported_preference_requires_own_prophetic_subject(self):
        value = self.evidence("eng", "TEST The drink most beloved to the Messenger of Allah (ﷺ) was the TEST",
                              "english_attributed_preference")
        self.assertNotIn("TEST", value["text"])
        for quotation in ("TEST the drink most beloved to the Prophet's wife was the TEST",
                          "TEST the drink most beloved to Umar was the TEST",
                          "TEST I wish the drink most beloved to the Prophet was the TEST"):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("eng", quotation)))

    def test_english_dialogue_requires_the_direct_respondent(self):
        quotation = "TEST A man asked the Messenger of Allah (ﷺ): TEST question? He replied: (The TEST answer)"
        self.evidence("eng", quotation, "english_question_and_explicit_response")
        for quotation in (
            "TEST A man asked the Messenger of Allah (ﷺ): TEST question without reply",
            "TEST A man asked the Messenger of Allah (ﷺ): TEST question? Umar replied: TEST",
            "TEST A man asked the Messenger of Allah (ﷺ): TEST question? She replied: TEST",
            "TEST Suppose a man asked the Messenger of Allah (ﷺ): TEST? He replied: TEST",
        ):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("eng", quotation)))

    def test_confirmed_attribution_question_is_not_an_unanswered_question(self):
        quotation = 'TEST Did `Abdullah ascribe it to Allah\'s Messenger (ﷺ)?" He said, "Yes TEST'
        self.evidence("eng", quotation, "english_explicit_attribution_confirmation")
        for quotation in (
            'TEST Did `Abdullah ascribe it to Allah\'s Messenger (ﷺ)?" He said, "No TEST',
            'TEST Did `Abdullah ascribe it to Allah\'s Messenger (ﷺ)? TEST unanswered',
            'TEST Did `Abdullah not ascribe it to Allah\'s Messenger (ﷺ)?" He said, "Yes TEST',
            'TEST Did `Abdullah ascribe it to Allah\'s Messenger (ﷺ)?" He said, "Perhaps TEST',
        ):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("eng", quotation)))

    def test_reported_action_with_explicit_abridgement_retains_that_scope(self):
        quotation = "TEST Allah's Messenger (ﷺ) met TEST. The rest of the hadith is the same."
        value = self.evidence("eng", quotation, "english_explicit_named_predicate")
        self.assertEqual(value["scope"], "source_explicit_abbreviated_report")

    def test_observed_subject_actions_keep_a_finite_predicate(self):
        # Bukhari 60/96/163/125; Nasai 70/91; Abu Dawud 33; Muslim 7129.
        for quotation in (
            "TEST The Prophet (ﷺ) remained behind us TEST",
            "TEST Allah's Messenger (ﷺ) then said TEST",
            "TEST the Messenger of Allah (ﷺ) would put TEST",
            "TEST the Prophet of Allah (ﷺ) purified himself TEST",
            "TEST the Prophet used his right hand TEST",
            "TEST Allah's Messenger (ﷺ) did not deliver TEST",
            "TEST the Prophet (ﷺ) used to do with us TEST",
            "TEST the Messenger of Allah was leading the TEST",
            "TEST the Prophet had been sitting TEST",
            "TEST When the Prophet (ﷺ) remained behind TEST",
            "TEST This is how the Prophet of Allah (ﷺ) purified himself TEST",
        ):
            with self.subTest(quotation=quotation):
                self.evidence("eng", quotation, "english_reported_subject_action")
        for quotation in (
            "TEST the Prophet TEST name without predicate",
            "TEST the Prophet inventedTESTed TEST unknown predicate",
            "TEST the Prophet used to inventedTEST TEST unknown predicate",
            "TEST what the Prophet would do TEST unanswered speculation",
            "TEST I wish the Prophet had remained TEST",
            "TEST the Messenger of Allah did not mention it in one or two traditions TEST generic citation claim",
        ):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("eng", quotation)))

    def test_reported_object_does_not_become_another_subject(self):
        # Actual trap shapes: Abu Dawud 3673/2656; Nasai 5191.
        for quotation in (
            "TEST the herald of the Messenger of Allah (ﷺ) made an announcement TEST",
            "TEST the Companions of the Prophet (ﷺ), disliked shouting TEST",
            "TEST a man, among those who met the Prophet [SAW], wore a ring TEST",
            "TEST the wife of the Prophet (ﷺ) had a cloth TEST",
            "TEST a man who accompanied the Prophet (ﷺ) then said TEST",
            "TEST a man who met the Prophet (ﷺ) returned TEST",
        ):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("eng", quotation)))

    def test_observed_salutation_variants_preserve_source_text(self):
        # Abu Dawud 16 and the Nawawi English edition supply these spellings.
        for quotation in (
            "TEST The Prophet (sal Allaahu alayhi wa sallam ) did not return TEST",
            "TEST the Messenger of Allah (peace and blessings of Allah be upon him) said TEST",
            "TEST the Prophet (SWAS) came TEST",
        ):
            with self.subTest(quotation=quotation):
                self.evidence("eng", quotation, "english_explicit_named_predicate")

    def test_observed_encounters_include_progressive_and_overnight_forms(self):
        # Bukhari155, Nasai4/18, AbuDawud58, Tirmidhi34/71, Muslim625.
        for quotation in (
            "TEST I followed the Prophet (ﷺ) TEST",
            "TEST I came to the Prophet (ﷺ) TEST",
            "TEST I was walking with the Messenger of Allah TEST",
            "TEST I spent a night with the Prophet TEST",
            "TEST she saw the Prophet performing TEST",
            "TEST I entered upon the Prophet TEST",
        ):
            with self.subTest(quotation=quotation):
                self.evidence("eng", quotation, "english_reported_encounter")
        self.evidence("eng", "TEST I and the Messenger of Allah (ﷺ) were going together TEST",
                      "english_explicit_shared_practice")
        for quotation in (
            "TEST she saw the Prophet's companion TEST",
            "TEST I spent a night with the Prophet's wife TEST",
            "TEST perhaps she saw the Prophet TEST",
            "TEST I and the Messenger of Allah TEST names without shared practice",
        ):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("eng", quotation)))
        for language, quotation in (
            ("eng", "TEST We were sitting with the Prophet (He then mentioned the Hadith above)"),
            ("eng", "TEST I went to the Prophet. He then mentioned something similar TEST"),
            ("ara", "TEST كنت أمشي مع النبي TEST بنحو حديث حفص TEST"),
        ):
            with self.subTest(quotation=quotation):
                value = self.evidence(language, quotation)
                self.assertEqual(value["scope"], "source_explicit_abbreviated_report")

    def test_learning_and_attributed_demonstration_have_source_ownership(self):
        # Nawawi11, Tirmidhi48, Nasai81/91.
        self.evidence("ara", 'TEST حفظت من رسول الله " TEST', "arabic_explicit_learned_report")
        self.evidence("ara", "TEST حفظت من رسول الله صلى الله عليه و سلم دع TEST",
                      "arabic_explicit_learned_report")
        self.evidence("eng", "TEST I memorised from the Messenger of Allah TEST",
                      "english_explicit_learned_report")
        self.evidence("ara", "TEST أريكم كيف كان طهور رسول الله TEST",
                      "arabic_demonstrated_prophetic_practice")
        self.evidence("ara", "TEST هذا طهور نبي الله TEST",
                      "arabic_demonstrated_prophetic_practice")
        self.evidence("ara", "TEST يسند ذلك إلى النبي TEST", "arabic_explicit_transmission_target")
        self.evidence("eng", "TEST he attributed that to the Prophet TEST", "english_explicit_transmission_target")
        for language, quotation in (
            ("eng", "TEST I memorised from the Prophet's wife TEST"),
            ("ara", "TEST هذا طهور عمر TEST"),
            ("ara", "TEST لا أدري أريكم كيف كان طهور رسول الله TEST"),
            ("ara", "TEST حفظت من رسول الله صلى الله عليه وسلم وعاءين TEST"),
            ("eng", "TEST I retain anything that I have heard from the Messenger of Allah TEST"),
            ("eng", "TEST I wrote everything which I heard from the Prophet TEST"),
        ):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions(language, quotation)))

    def test_reported_message_requires_the_immediate_prophetic_response(self):
        # Abu Dawud3646 has a general transmission claim followed by this
        # independent, concrete Prophetic gesture and reply.
        self.evidence("eng", "TEST mentioned it to the Messenger of Allah (ﷺ). He signalled TEST",
                      "english_direct_message_and_response")
        for quotation in (
            "TEST mentioned it to the Messenger of Allah (ﷺ). TEST no response",
            "TEST mentioned it to the Messenger of Allah (ﷺ). Umar replied TEST",
            "TEST mentioned it to the Messenger of Allah (ﷺ). Umar arrived. He said TEST",
            "TEST I wish I mentioned it to the Messenger of Allah (ﷺ). He signalled TEST",
        ):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("eng", quotation)))

    def test_arabic_reported_encounter_variants_do_not_need_quoted_speech(self):
        for quotation in (
            "TEST تخلف عنا النبي TEST",
            "TEST اتبعت النبي TEST",
            "TEST أقبلت إلى النبي TEST",
            "TEST كنت أمشي مع رسول الله TEST",
            "TEST بت ليلة عند النبي TEST",
            "TEST فيضع رسول الله TEST",
        ):
            with self.subTest(quotation=quotation):
                self.evidence("ara", quotation)
        for quotation in ("TEST لو بت ليلة عند النبي TEST", "TEST ليلة عند النبي TEST no reported action"):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("ara", quotation)))

    def test_colon_punctuation_preserves_direct_dialogue_subject(self):
        # Nawawi21/29 use quoted and unquoted imperatives after قال:.
        for quotation in ('TEST قلت: يا رسول الله TEST قال: " TEST response',
                          'TEST قلت:يا رسول الله TEST قال: قل TEST response'):
            with self.subTest(quotation=quotation):
                self.evidence("ara", quotation, "arabic_address_and_explicit_response")
        self.assertIsNone(explicit_report_evidence(versions(
            "ara", 'TEST قلت: يا رسول الله TEST قال عمر: " TEST independent answer')))

    def test_own_physical_description_is_not_a_relative_description(self):
        # Tirmidhi53, Muslim1827, AbuDawud2583/4134, Bukhari6456.
        for quotation in ("TEST Allah's Messenger had a cloth TEST",
                          "TEST the Messenger of Allah had a mat TEST"):
            with self.subTest(quotation=quotation):
                value = self.evidence("eng", quotation, "english_owned_practice_object")
                self.assertEqual(value["scope"], "explicit_prophetic_practice_or_description")
        for quotation in ("TEST The sandals of the Prophet had two thongs TEST",
                          "TEST The pommel of the sword of the Messenger of Allah was of silver TEST",
                          "TEST The bed mattress of the Prophet was made of leather TEST"):
            with self.subTest(quotation=quotation):
                self.evidence("eng", quotation, "english_reported_property_description")
        for quotation in ("TEST The wife of the Prophet had a cloth TEST",
                          "TEST The sandals of the Prophet's wife had two thongs TEST",
                          "TEST Perhaps the bed of the Prophet was made TEST",
                          "TEST the Prophet had a wife TEST"):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("eng", quotation)))

    def test_actual_permission_grant_is_separate_from_narrators_wish(self):
        # Muslim3119/3120 and Nasai3049 narrate an actual grant; a separate
        # narrator's wish does not erase or establish the event.
        for quotation in (
            "TEST she sought permission from Allah's Messenger (ﷺ) to proceed. He granted her permission TEST",
            "TEST she asked the Messenger of Allah for permission, and he gave her permission TEST",
            "TEST I wish I had asked the Messenger of Allah for permission. She asked the Messenger of Allah for permission, and he gave her permission TEST",
        ):
            with self.subTest(quotation=quotation):
                self.evidence("eng", quotation, "english_permission_request_and_grant")
        for quotation in (
            "TEST she asked the Messenger of Allah for permission TEST no grant",
            "TEST she asked the Messenger of Allah for permission. Umar granted her permission TEST",
            "TEST she asked the Messenger of Allah for permission. Umar said TEST. He granted her permission TEST",
            "TEST I wish she asked the Messenger of Allah for permission and he gave her permission TEST",
        ):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("eng", quotation)))

    def test_urdu_has_own_evidence_and_rejects_second_subject(self):
        quotation = "TEST رسول اللہ صلی اللہ علیہ وسلم نے ہم سے فرمایا TEST"
        value = self.evidence("urd", quotation, "urdu_explicit_named_predicate")
        self.assertEqual(value["language"], "ur")
        self.evidence("urd", "TEST رسول اللہﷺ تشریف لائے TEST", "urdu_explicit_named_predicate")
        for quotation in ("TEST کاش رسول اللہ نے فرمایا TEST", "TEST کیا رسول اللہ نے فرمایا TEST",
                          "TEST رسول اللہ نے TEST عمر نے فرمایا TEST", "TEST رسول اللہ کے صحابی نے فرمایا TEST"):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("urd", quotation)))

    def test_bengali_evidence_is_own_language_and_notes_never_supply_it(self):
        quotation = "TEST রাসূলুল্লাহ সাল্লাল্লাহু আলাইহি ওয়াসাল্লাম বলেছেন TEST"
        value = self.evidence("ben", quotation, "bengali_explicit_named_predicate")
        self.assertEqual(value["language"], "bn")
        self.evidence("ben", "TEST আল্লাহ্‌র রাসূল বলেছেন TEST", "bengali_explicit_named_predicate")
        self.evidence("ben", "TEST নবী সাল্লাল্লাহু আলাইহি ওয়াসাল্লাম বলেছেনঃ TEST",
                      "bengali_explicit_named_predicate")
        self.assertIsNone(explicit_report_evidence(versions("ben", "TEST independent saying", notes=[quotation])))
        for quotation in ("TEST নবীর সাহাবী বলেছেন TEST", "TEST যদি নবী বলেছেন TEST",
                          "TEST নবী বলেছেনের TEST invalid word continuation"):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("ben", quotation)))

    def test_only_supplied_language_can_own_evidence_and_order_is_stable(self):
        source = {"eng": {"quotation": "TEST the Prophet came TEST"},
                  "ara": {"quotation": ""}, "urd": {"quotation": "TEST own Urdu text"}}
        evidence = explicit_report_evidence(source)
        self.assertEqual(evidence["language"], "en")
        self.assertEqual(evidence, explicit_report_evidence(dict(reversed(list(source.items())))))
        self.assertEqual(evidence["text"], source["eng"]["quotation"][slice(*evidence["span"])])
        self.assertIsNone(explicit_report_evidence({"ara": {"quotation": "TEST"},
                                                   "eng": {"row": {"text": "the Prophet came TEST"}}}))

    def test_source_observed_finite_actions_keep_the_named_subject(self):
        # Arabic report syntax from Bukhari184/478/1836/2069/4031,
        # Muslim774/1546 and the separately logged held-source cohort.
        for verb in ("انصرف", "تغيظ", "رد", "أراد", "شبك", "أخر", "احتجم", "حلق", "رهن",
                     "حرق", "عاب", "حالف", "أردفني", "صعد", "اتخذ", "اشتكى", "زجر",
                     "قنت", "رخص", "اعتمر", "رمل", "رجم", "ضرب", "سمل", "تبنى"):
            with self.subTest(verb=verb):
                self.evidence("ara", "TEST " + verb + " رسول الله ﷺ TEST", "arabic_reported_action")
        # Explicit narrated nonaction is not an absence of attribution.
        self.evidence("ara", "TEST ما عاب النبي طعاما TEST", "arabic_reported_action")
        for quotation in ("TEST هل اتخذ النبي TEST", "TEST هل قنت رسول الله TEST",
                          "TEST كيف انصرف رسول الله TEST", "TEST لو رجم النبي TEST",
                          "TEST احتجم صاحب رسول الله TEST", "TEST شبك عمر TEST"):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("ara", quotation)))

    def test_object_command_and_witnessed_service_preserve_actor(self):
        # Nasai286/374; Malik132; AbuDawud1745/376/2940/885/881.
        for quotation, rule in (
            ("TEST أمرها رسول الله TEST", "arabic_reported_command_to_person"),
            ("TEST نهاهم النبي TEST", "arabic_reported_command_to_person"),
            ("TEST كنت أرجل رأس رسول الله TEST", "arabic_witnessed_service_or_practice"),
            ("TEST كنت أطيب رسول الله TEST", "arabic_witnessed_service_or_practice"),
            ("TEST كنت أخدم رسول الله TEST", "arabic_witnessed_service_or_practice"),
            ("TEST كنا نبايع رسول الله TEST", "arabic_witnessed_service_or_practice"),
            ("TEST رمقت النبي TEST", "arabic_witnessed_service_or_practice"),
            ("TEST صليت إلى جنب رسول الله TEST", "arabic_reported_adjacent_prayer"),
        ):
            with self.subTest(quotation=quotation):
                self.evidence("ara", quotation, rule)
        for quotation in ("TEST أمرها عمر TEST", "TEST كنت أخدم صاحب رسول الله TEST",
                          "TEST كنت أرجل رأس عمر TEST", "TEST لو صليت إلى جنب رسول الله TEST",
                          "TEST كنا على عهد رسول الله TEST"):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("ara", quotation)))

    def test_reported_encounter_and_demonstration_are_qualified(self):
        # Bukhari182 and186 report an encounter and reproduced ablution.
        self.evidence("ara", "TEST أنه كان مع رسول الله ﷺ في سفر TEST",
                      "arabic_qualified_shared_encounter")
        value = self.evidence("ara", "TEST فتوضأ لهم وضوء النبي TEST",
                              "arabic_reproduced_prophetic_practice")
        self.assertEqual(value["scope"], "explicit_prophetic_practice_or_description")
        for quotation in ("TEST أنه كان مع رسول الله TEST unspecified", "TEST فتوضأ لهم وضوء عمر TEST",
                          "TEST لو أنه كان مع رسول الله في سفر TEST"):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("ara", quotation)))

    def test_shared_bathing_and_expeditions_have_actual_narrated_predicate(self):
        # Bukhari225/250/261/299/300/301 and Muslim731/4696.
        for quotation in ("TEST كنت أغتسل أنا ورسول الله ﷺ TEST",
                          "TEST كنا نغزو مع النبي TEST", "TEST غزا مع رسول الله TEST"):
            with self.subTest(quotation=quotation):
                self.evidence("ara", quotation, "arabic_explicit_shared_practice")
        self.evidence("ara", "TEST رأيتني أنا والنبي ﷺ نتماشى TEST", "arabic_witnessed_shared_walk")
        for quotation in ("TEST أنا والنبي TEST", "TEST كنت أغتسل أنا وزوج النبي TEST",
                          "TEST لو كنا نغزو مع النبي TEST", "TEST رأيتني أنا والنبي TEST"):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("ara", quotation)))

    def test_retrospective_hearing_and_prophetic_pledge_have_explicit_target(self):
        # Bukhari179, Muslim219/240, IbnMajah114. These are indirect report
        # constructions, not a claim that all narrator framing is direct speech.
        for quotation in ("TEST سمعته من رسول الله TEST", "TEST سمعت أذناي من رسول الله TEST",
                          "TEST سمع أذناى من رسول الله TEST"):
            with self.subTest(quotation=quotation):
                self.evidence("ara", quotation, "arabic_retrospective_hearing_attribution")
        for quotation in ("TEST عهد إلي النبي الأمي ﷺ TEST",
                          "TEST إنه لعهد النبي الأمي صلى الله عليه وسلم إلي TEST"):
            with self.subTest(quotation=quotation):
                self.evidence("ara", quotation, "arabic_explicit_prophetic_pledge")
        for quotation in ("TEST لم سمعته من رسول الله TEST deliberately negated fixture",
                          "TEST ما سمعت هذا من رسول الله TEST", "TEST سمعته من عمر TEST",
                          "TEST إن كانت سمعت هذا من رسول الله TEST conjecture",
                          "TEST إني لأظنها سمعت هذا من رسول الله TEST conjecture",
                          "TEST اكتب إلي بحديث سمعته من رسول الله TEST request without response",
                          "TEST لا أدع شيئا سمعته من رسول الله TEST generic transmission claim",
                          "TEST وقد سَمِعْتَهُ من رسول الله TEST second-person unspecified report",
                          "TEST كيف كان عبد الله يقرأ TEST وقد سمعتها من رسول الله TEST Quran context",
                          "TEST أكتب لها مصحفا TEST سمعتها من رسول الله TEST Quran context",
                          "TEST على عهد النبي ﷺ إلى المدينة TEST lifetime and destination",
                          "TEST هل عهد إلي النبي TEST", "TEST على عهد النبي TEST independent event"):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("ara", quotation)))
        source = "TEST أشيء سَمِعْتَهُ من رسول الله TEST قال بل سَمِعْتُهُ من رسول الله TEST"
        value = self.evidence("ara", source, "arabic_retrospective_hearing_attribution")
        self.assertIn("سَمِعْتُهُ", value["text"])
        self.assertNotIn("سَمِعْتَهُ", value["text"])

    def test_habit_question_requires_its_actual_answer(self):
        # Nasai8 / AbuDawud51. A question by itself is insufficient.
        source = "TEST قلت لعائشة بأي شيء كان يبدأ النبي صلى الله عليه وسلم إذا دخل بيته قالت بالسواك TEST"
        self.evidence("ara", source, "arabic_habit_question_with_reported_answer")
        for quotation in (source.replace("قالت بالسواك", "قالت لا أدري"),
                          source.replace("قالت بالسواك", "قال عمر بالسواك"),
                          source.replace("النبي", "عمر"),
                          source.replace("قالت بالسواك", "TEST unanswered")):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("ara", quotation)))

    def test_owned_vessel_and_affirmed_prohibition_are_actual_report_evidence(self):
        # AbuDawud24 / Nasai32 and AbuDawud7 / Tirmidhi16.
        self.evidence("ara", "TEST كان للنبي ﷺ قدح من عيدان TEST", "arabic_owned_practice_object")
        self.evidence("ara", "TEST قد علمكم نبيكم ﷺ كل شيء حتى الخراءة فقال سلمان أجل نهانا TEST",
                      "arabic_explicit_taught_and_prohibited")
        for quotation in ("TEST كان لصاحب النبي قدح TEST", "TEST كان للنبي زوجة TEST",
                          "TEST قد علمكم نبيكم كل شيء حتى الخراءة فقال سلمان لا أدري TEST",
                          "TEST إن صاحبكم ليعلمكم حتى الخراءة قال أجل نهانا TEST unknown antecedent"):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("ara", quotation)))

    def test_endpoint_raised_attribution_does_not_complete_abbreviated_text(self):
        # Muslim208 explicitly says رفعه and identifies Shu'ba's other report.
        source = 'TEST عن أبي هريرة، رفعه قال " TEST ثم ذكر بمثل حديث شعبة TEST'
        value = self.evidence("ara", source, "arabic_endpoint_raised_transmission")
        self.assertEqual(value["scope"], "source_explicit_abbreviated_report")
        for quotation in ('TEST عن أبي هريرة، لم يرفعه قال " TEST',
                          'TEST عن أبي هريرة، رفع الثوب قال " TEST',
                          'TEST عن أبي هريرة، رفعه TEST no supplied quoted clause',
                          'TEST ولم يرفعاه زاد " TEST'):
            with self.subTest(quotation=quotation):
                self.assertIsNone(explicit_report_evidence(versions("ara", quotation)))


if __name__ == "__main__":
    unittest.main()
