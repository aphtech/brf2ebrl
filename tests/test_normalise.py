from brf2ebrf.normalise import normalise_brf


def test_prepend_formfeed():
    assert normalise_brf("TE/ BRF", 40, 25) == "\fTE/ BRF"

def test_do_not_prepend_if_formfeed_exists():
    assert normalise_brf("\fTE/ BRF", 40, 25) == "\fTE/ BRF"
