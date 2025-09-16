"""Unit tests for models."""

import pytest
from datetime import datetime
from app.models import User, District, FOK, Sport, Application


class TestUser:
    """Test User model."""
    
    def test_user_creation(self, sample_user: User):
        """Test user creation with valid data."""
        assert sample_user.telegram_id > 0
        assert sample_user.first_name
        assert sample_user.display_name
        assert sample_user.registration_completed is True
        assert sample_user.phone_shared is True
    
    def test_user_full_name(self, sample_user: User):
        """Test full_name property."""
        expected = f"{sample_user.first_name} {sample_user.last_name}"
        assert sample_user.full_name == expected
    
    def test_user_full_name_no_last_name(self):
        """Test full_name property without last_name."""
        user = User(
            telegram_id=123456,
            first_name="John",
            display_name="John"
        )
        assert user.full_name == "John"
    
    def test_can_make_applications_with_phone(self, sample_user: User):
        """Test can_make_applications with phone."""
        sample_user.phone = "+1234567890"
        sample_user.phone_shared = True
        assert sample_user.can_make_applications is True
    
    def test_can_make_applications_without_phone(self, sample_user: User):
        """Test can_make_applications without phone."""
        sample_user.phone = None
        sample_user.phone_shared = False
        assert sample_user.can_make_applications is False
    
    def test_update_activity(self, sample_user: User):
        """Test update_activity method."""
        initial_activity = sample_user.last_activity
        sample_user.update_activity()
        assert sample_user.last_activity > initial_activity


class TestDistrict:
    """Test District model."""
    
    def test_district_creation(self, sample_district: District):
        """Test district creation with valid data."""
        assert sample_district.name
        assert sample_district.is_active is True
        assert sample_district.id is not None


class TestFOK:
    """Test FOK model."""
    
    def test_fok_creation(self, sample_fok: FOK):
        """Test FOK creation with valid data."""
        assert sample_fok.name
        assert sample_fok.district_id
        assert sample_fok.address
        assert sample_fok.is_active is True
        assert sample_fok.id is not None


class TestSport:
    """Test Sport model."""
    
    def test_sport_creation(self, sample_sport: Sport):
        """Test sport creation with valid data."""
        assert sample_sport.name
        assert sample_sport.is_active is True
        assert sample_sport.id is not None


class TestApplication:
    """Test Application model."""
    
    def test_application_creation(self, sample_application: Application):
        """Test application creation with valid data."""
        assert sample_application.user_id
        assert sample_application.fok_id
        assert sample_application.status == "pending"
        assert sample_application.id is not None
    
    def test_application_status_transitions(self, sample_application: Application):
        """Test application status transitions."""
        # Test valid status transitions
        valid_statuses = ["pending", "approved", "transferred", "completed", "cancelled", "rejected"]
        
        for status in valid_statuses:
            sample_application.status = status
            assert sample_application.status == status