import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "LinguAlyzer_Final_Polished"))
from checks import arabic_ratio, extract_numbers, extract_placeholders, length_ratio, strip_tags  # noqa: E402


def test_arabic_indic_digits_match_western_digits():
    assert extract_numbers("Try again in 5 minutes.") == extract_numbers("بعد ٥ دقائق")
    assert extract_numbers("12.5%") == extract_numbers("١٢.٥٪")


def test_different_numbers_still_differ():
    assert extract_numbers("3 new items") != extract_numbers("العناصر الجديدة")


def test_inline_tags_do_not_count_as_latin_text():
    assert arabic_ratio('أُلغي طلبك <pc id="1">رقم</pc>.') == 1.0


def test_tags_ignored_for_length_and_numbers():
    assert strip_tags('Tap <g id="1">Continue</g>') == "Tap Continue"
    assert extract_numbers('<x id="7"/> done') == []
    assert length_ratio('<g id="1">ab</g>', "ab") == 1.0


def test_placeholders_still_compare_tags():
    assert extract_placeholders('Hi <x id="name"/>') != extract_placeholders("مرحبًا")
    assert extract_placeholders('Tap <g id="1">Go</g>') == extract_placeholders('اضغط <g id="1">انتقل</g>')
