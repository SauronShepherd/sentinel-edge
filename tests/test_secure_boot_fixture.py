from sentinel_edge.qualification.secure_boot_fixture import SecureBootFixture


def test_unsigned_wrong_key_and_rollback_boot_fixtures_fail() -> None:
    base = dict(board_model="Pi5", eeprom_config_digest="eeprom", signed_boot_image_digest="image", key_lifecycle_ref="keys", recovery_procedure_ref="recovery")
    assert SecureBootFixture(**base, signature_valid=False, key_matches=True, rollback_detected=False).boot_allowed() is False
    assert SecureBootFixture(**base, signature_valid=True, key_matches=False, rollback_detected=False).boot_allowed() is False
    assert SecureBootFixture(**base, signature_valid=True, key_matches=True, rollback_detected=True).boot_allowed() is False
