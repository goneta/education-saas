"""Partner API schemas must not shadow the main application's contracts."""

from backend import schemas
from backend.routers import public_api_v2


def test_school_registration_schema_retains_country_and_localization():
    school = schemas.SchoolCreate(name="Example", domain_prefix="example", school_type="general")
    assert school.country_code == "CI"
    assert school.currency_code is None
    assert school.primary_language is None


def test_partner_school_schema_is_separate():
    assert public_api_v2.PublicV2SchoolCreate is schemas.PublicV2SchoolCreate
    assert schemas.PublicV2SchoolCreate is not schemas.SchoolCreate


def test_existing_education_schemas_keep_their_fields():
    assert "school_id" in schemas.ClassCreate.model_fields
    assert "school_id" in schemas.TeacherCreate.model_fields or "role" in schemas.TeacherCreate.model_fields
    assert "school_id" not in schemas.PublicV2ClassCreate.model_fields
