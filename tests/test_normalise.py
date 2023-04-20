from brf2ebrf.normalise import normalise_brf


def test_prepend_form_feed():
    assert normalise_brf("TE/ BRF", 40, 25).startswith("\fTE/ BRF")


def test_do_not_prepend_if_form_feed_exists():
    assert normalise_brf("\fTE/ BRF", 40, 25).startswith("\fTE/ BRF")


def test_line_is_padded_when_short():
    assert normalise_brf("\fTE/ BRF", 40, 25).startswith("\fTE/ BRF                                 \n")


def test_line_is_truncated_when_too_long():
    assert normalise_brf("\fTE/ BRF TEXT", 4, 25).startswith("\fTE/ \n")
