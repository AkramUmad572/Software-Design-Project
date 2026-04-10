from motormatch.moderation import next_listing_status


def test_admin_approve_sets_listing_visible():
    assert next_listing_status("approve") == "approved"


def test_admin_hide_sets_listing_hidden():
    assert next_listing_status("hide") == "hidden"


def test_unknown_action_defaults_to_hidden():
    assert next_listing_status("anything") == "hidden"


def test_action_strips_whitespace():
    assert next_listing_status("  approve ") == "approved"


def test_empty_string_is_hidden():
    assert next_listing_status("") == "hidden"


def test_none_action_is_hidden():
    assert next_listing_status(None) == "hidden"


def test_uppercase_approve_is_not_exact_match():
    assert next_listing_status("APPROVE") == "hidden"


def test_mixed_case_approve_is_hidden():
    assert next_listing_status("Approve") == "hidden"


def test_whitespace_only_is_hidden():
    assert next_listing_status("   \t  ") == "hidden"


def test_approve_substring_not_accepted():
    assert next_listing_status("approval") == "hidden"


def test_newlines_around_approve_still_approved():
    assert next_listing_status("\napprove\n") == "approved"


def test_numeric_string_is_hidden():
    assert next_listing_status("123") == "hidden"


def test_reject_action_is_hidden():
    assert next_listing_status("reject") == "hidden"


def test_delete_action_is_hidden():
    assert next_listing_status("delete") == "hidden"

