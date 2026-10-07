from app.rag.cleaner import clean_academic_text


def test_clean_academic_text_hyphenation():
    raw = "This is a demon-\nstration of hyphen removal in algo-\nrithms."
    cleaned = clean_academic_text(raw)
    assert "demonstration" in cleaned
    assert "algorithms" in cleaned
    assert "algo-\nrithm" not in cleaned


def test_clean_academic_text_whitespace():
    raw = "Multiple    spaces    and \t\t tabs \n\n\n\n should be normalized."
    cleaned = clean_academic_text(raw)
    assert "Multiple spaces and tabs" in cleaned
    assert "\n\n\n" not in cleaned


def test_clean_academic_text_control_characters():
    raw = "Clean\x00 null\x07 bell\x1f unit separator text."
    cleaned = clean_academic_text(raw)
    assert "\x00" not in cleaned
    assert "\x07" not in cleaned
    assert "Clean null bell unit separator text." in cleaned


def test_clean_academic_text_empty():
    assert clean_academic_text("") == ""
    assert clean_academic_text(None) == ""
