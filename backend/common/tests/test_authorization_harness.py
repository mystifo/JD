import pytest
from django.test import override_settings

from common.testing import assert_anonymous_denied, assert_cross_user_hidden, assert_owner_visible


@override_settings(ROOT_URLCONF="common.tests.urls_leaky")
def test_harness_passes_for_the_real_owner(owner_client):
    response = assert_owner_visible(owner_client, "/leaky/")
    assert response.status_code == 200


@override_settings(ROOT_URLCONF="common.tests.urls_leaky")
def test_harness_rejects_anonymous(anon_client):
    assert_anonymous_denied(anon_client, "/leaky/")


@override_settings(ROOT_URLCONF="common.tests.urls_leaky")
def test_harness_fails_loudly_on_a_cross_tenant_leak(other_client):
    # The scratch view leaks every user's rows, so the harness must fail. If this
    # test ever stops failing, the authorization matrix is not enforcing anything.
    with pytest.raises(AssertionError, match="cross-tenant leak"):
        assert_cross_user_hidden(other_client, "/leaky/")


@override_settings(ROOT_URLCONF="common.tests.urls_leaky")
def test_harness_reports_expected_status(owner_client, other_client):
    with pytest.raises(AssertionError, match="expected 403"):
        assert_cross_user_hidden(other_client, "/leaky/", expected=403)
