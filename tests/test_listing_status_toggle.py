from motormatch.moderation import next_listing_status


def test_admin_approve_sets_listing_visible():
    assert next_listing_status("approve") == "approved"


def test_admin_hide_sets_listing_hidden():
    assert next_listing_status("hide") == "hidden"


def test_unknown_action_defaults_to_hidden():
    assert next_listing_status("anything") == "hidden"


def test_action_strips_whitespace():
    assert next_listing_status("  approve ") == "approved"

