from story_spark.licenses import internal_license


def test_internal_license_is_stable_and_provider_scoped():
    first = internal_license("gumroad", "purchase-key")
    second = internal_license("gumroad", "purchase-key")
    assert first.startswith("SSS-")
    assert first == second
    assert first != internal_license("payhip", "purchase-key")
