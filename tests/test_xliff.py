import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "LinguAlyzer_Final_Polished"))
from xliff import XliffError, parse  # noqa: E402

EXAMPLES = ROOT / "examples"


def load(name):
    return parse((EXAMPLES / name).read_bytes())


def test_xliff_1_2_units_and_skips_translate_no():
    units = load("sample-1.2.xlf")
    assert [u.id for u in units] == ["settings.title", "files.backup", "greeting", "delete.confirm"]
    assert units[0].target == "انتقل إلى الإعدادات لتحديث تفضيلات الخصوصية."
    assert units[0].state == "translated"


def test_xliff_1_2_inline_tags_become_tokens():
    unit = load("sample-1.2.xlf")[1]
    assert unit.source == 'Your files were backed up. Tap <g id="1">Continue</g> to review the 3 new items.'
    assert '<g id="1">متابعة</g>' in unit.target
    assert unit.note == "Button label inside g."


def test_xliff_1_2_missing_placeholder_is_visible():
    unit = load("sample-1.2.xlf")[2]
    assert '<x id="name"/>' in unit.source
    assert "<x" not in unit.target


def test_xliff_1_2_untranslated_unit_has_empty_target():
    assert load("sample-1.2.xlf")[3].target == ""


def test_xliff_2_0_segments_and_notes():
    units = load("sample-2.0.xlf")
    assert [u.id for u in units] == ["u1", "u2.s1", "u2.s2"]
    assert units[0].target == "سجّل الدخول للمتابعة."
    assert units[0].note == "Shown on the sign-in screen."
    assert '<pc id="1">#4821</pc>' in units[1].target
    assert units[2].target == "" and units[2].state == "initial"


def test_sdlxliff_segments_are_paired_by_mid():
    units = load("sample.sdlxliff")
    assert [u.id for u in units] == ["a1b2.1", "a1b2.2"]
    assert units[0].source == "Download failed."
    assert units[0].target == "فشل التنزيل."
    assert units[1].target == "يُرجى المحاولة مرة أخرى بعد ٥ دقائق."


def test_rejects_non_xliff():
    with pytest.raises(XliffError):
        parse("<html><body/></html>")
    with pytest.raises(XliffError):
        parse("not xml")
