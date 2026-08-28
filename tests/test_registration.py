

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlmodel import select

from main import RegisterRequest, register_user
from userTypes import DoctorProfile, PatientProfile, StageOfCare, User, UserRole


def make_payload(email, role="PATIENT", specialization=None, stage_of_care="Mild"):
    return RegisterRequest(
        email=email,
        password="1234qwerty",
        role=role,
        full_name="Shiva Verma",
        specialization=specialization,
        stage_of_care=stage_of_care,
    )


@pytest.mark.parametrize("role", ["doctor", "Doctor", " DOCTOR "])
def test_role_is_case_insensitive(role):
    assert make_payload("role@example.com", role).role is UserRole.DOCTOR


def test_registers_doctor_and_creates_doctor_profile(session):
    response = register_user(
        make_payload("doctor@example.com", "doctor", "Neurology"), session
    )

    user = session.exec(select(User).where(User.email == "doctor@example.com")).one()
    profile = session.exec(
        select(DoctorProfile).where(DoctorProfile.user_id == user.id)
    ).one()

    assert response.success is True
    assert response.data["user_id"] == user.id
    assert user.role is UserRole.DOCTOR
    assert profile.full_name == "Shiva Verma"
    assert profile.specialization == "Neurology"
    assert session.exec(select(PatientProfile)).first() is None


def test_registers_patient_and_creates_patient_profile(session):
    register_user(make_payload("patient@example.com"), session)

    user = session.exec(select(User).where(User.email == "patient@example.com")).one()
    profile = session.exec(
        select(PatientProfile).where(PatientProfile.user_id == user.id)
    ).one()

    assert user.role is UserRole.PATIENT
    assert profile.full_name == "Shiva Verma"
    assert profile.stage_of_care is StageOfCare.MILD
    assert session.exec(select(DoctorProfile)).first() is None


def test_duplicate_email_returns_bad_request(session):
    register_user(make_payload("duplicate@example.com"), session)

    with pytest.raises(HTTPException) as error:
        register_user(make_payload("duplicate@example.com"), session)

    assert error.value.status_code == 400
    assert error.value.detail["code"] == "EMAIL_ALREADY_EXISTS"


def test_invalid_registration_payload_is_rejected():
    with pytest.raises(ValidationError):
        make_payload("not-an-email", "nurse")


def test_patient_stage_of_care_is_required():
    with pytest.raises(ValidationError, match="stage_of_care is required"):
        make_payload("missing-stage@example.com", stage_of_care=None)


def test_patient_stage_of_care_must_be_valid():
    with pytest.raises(ValidationError):
        make_payload("invalid-stage@example.com", stage_of_care="Critical")


def test_registers_admin_without_creating_a_profile(session):
    register_user(make_payload("admin@example.com", "admin"), session)

    user = session.exec(select(User).where(User.email == "admin@example.com")).one()

    assert user.role is UserRole.ADMIN
    assert session.exec(select(DoctorProfile)).first() is None
    assert session.exec(select(PatientProfile)).first() is None
