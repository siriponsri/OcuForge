from scripts.validate_colab_lane import build_report, validate_notebook


def test_colab_reproduction_notebook_is_clean():
    result = validate_notebook()
    assert result["status"] == "PASS"
    assert result["execution"].startswith("structural-only")


def test_colab_lane_does_not_claim_unverified_authentication():
    report = build_report()
    integrations = report["checks"]["integrations"]
    assert integrations["security"]["auth_attempted"] is False
    assert integrations["security"]["credential_values_logged"] is False
    assert report["checks"]["notebook"]["status"] == "PASS"
