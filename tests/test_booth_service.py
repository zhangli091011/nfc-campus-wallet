"""
Unit tests for BoothService.

Tests booth management functionality including creation, retrieval,
listing, status updates, and validation.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from core.database import Base
from models.booth import Booth
from models.event import Event
from services.booth_service import (
    BoothService,
    BoothNotFoundError,
    BoothInactiveError,
    InvalidEventError,
    BoothNotInEventError
)


# Test database setup
@pytest.fixture
def test_db():
    """Create a test database session."""
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestSessionLocal()
    
    yield db
    
    db.close()


@pytest.fixture
def booth_service(test_db):
    """Create BoothService instance with test database."""
    return BoothService(test_db)


@pytest.fixture
def test_event(test_db):
    """Create a test event in the database."""
    event = Event(
        name="Test Event",
        start_time=datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone.utc),
        status="active",
        recharge_enabled=True,
        consume_enabled=True,
        expire_rule="event_end",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)
    return event


@pytest.fixture
def test_booth(test_db, test_event):
    """Create a test booth in the database."""
    booth = Booth(
        event_id=test_event.id,
        name="Test Booth",
        class_name="Class 1A",
        status="active",
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(booth)
    test_db.commit()
    test_db.refresh(booth)
    return booth


@pytest.fixture
def inactive_booth(test_db, test_event):
    """Create an inactive test booth."""
    booth = Booth(
        event_id=test_event.id,
        name="Inactive Booth",
        class_name="Class 2B",
        status="inactive",
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(booth)
    test_db.commit()
    test_db.refresh(booth)
    return booth


class TestBoothServiceCreateBooth:
    """Test BoothService.create_booth method."""
    
    def test_create_booth_success(self, booth_service, test_event):
        """Test successful booth creation with valid event_id."""
        booth = booth_service.create_booth(
            event_id=test_event.id,
            name="Food Stall",
            class_name="Class 3C"
        )
        
        # Verify booth was created
        assert booth.id is not None
        assert booth.event_id == test_event.id
        assert booth.name == "Food Stall"
        assert booth.class_name == "Class 3C"
        assert booth.status == "active"
        assert booth.created_at is not None
    
    def test_create_booth_with_custom_status(self, booth_service, test_event):
        """Test booth creation with custom status."""
        booth = booth_service.create_booth(
            event_id=test_event.id,
            name="Drink Stand",
            class_name="Class 4D",
            status="inactive"
        )
        
        assert booth.status == "inactive"
    
    def test_create_booth_invalid_event_id(self, booth_service):
        """Test booth creation with non-existent event_id."""
        with pytest.raises(InvalidEventError) as exc_info:
            booth_service.create_booth(
                event_id=99999,
                name="Invalid Booth",
                class_name="Class 5E"
            )
        
        assert exc_info.value.error_code == "INVALID_EVENT_ID"
        assert exc_info.value.event_id == 99999


class TestBoothServiceGetBooth:
    """Test BoothService.get_booth method."""
    
    def test_get_booth_success(self, booth_service, test_booth):
        """Test retrieving existing booth."""
        booth = booth_service.get_booth(test_booth.id)
        
        assert booth.id == test_booth.id
        assert booth.name == "Test Booth"
        assert booth.class_name == "Class 1A"
        assert booth.status == "active"
    
    def test_get_booth_not_found(self, booth_service):
        """Test retrieving non-existent booth."""
        with pytest.raises(BoothNotFoundError) as exc_info:
            booth_service.get_booth(99999)
        
        assert exc_info.value.error_code == "BOOTH_NOT_FOUND"
        assert exc_info.value.booth_id == 99999


class TestBoothServiceListBooths:
    """Test BoothService.list_booths method."""
    
    def test_list_all_booths(self, booth_service, test_booth, inactive_booth):
        """Test listing all booths without filters."""
        booths = booth_service.list_booths()
        
        assert len(booths) == 2
        booth_ids = [b.id for b in booths]
        assert test_booth.id in booth_ids
        assert inactive_booth.id in booth_ids
    
    def test_list_booths_by_event_id(self, booth_service, test_event, test_booth):
        """Test listing booths filtered by event_id."""
        # Create another event
        event2 = Event(
            name="Event 2",
            start_time=datetime(2024, 2, 1, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 2, 1, 18, 0, 0, tzinfo=timezone.utc),
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        booth_service.db.add(event2)
        booth_service.db.commit()
        booth_service.db.refresh(event2)
        
        # Create booth for event2
        booth2 = Booth(
            event_id=event2.id,
            name="Booth in Event 2",
            class_name="Class 6F",
            status="active",
            created_at=datetime.now(timezone.utc)
        )
        booth_service.db.add(booth2)
        booth_service.db.commit()
        
        # List booths for test_event only
        booths = booth_service.list_booths(event_id=test_event.id)
        
        assert len(booths) >= 1
        for booth in booths:
            assert booth.event_id == test_event.id
    
    def test_list_booths_by_status(self, booth_service, test_booth, inactive_booth):
        """Test listing booths filtered by status."""
        # List only active booths
        active_booths = booth_service.list_booths(status="active")
        
        assert len(active_booths) >= 1
        for booth in active_booths:
            assert booth.status == "active"
        
        # List only inactive booths
        inactive_booths = booth_service.list_booths(status="inactive")
        
        assert len(inactive_booths) >= 1
        for booth in inactive_booths:
            assert booth.status == "inactive"
    
    def test_list_booths_with_limit_and_offset(self, booth_service, test_booth, inactive_booth):
        """Test listing booths with pagination."""
        # Get first booth
        booths_page1 = booth_service.list_booths(limit=1, offset=0)
        assert len(booths_page1) == 1
        
        # Get second booth
        booths_page2 = booth_service.list_booths(limit=1, offset=1)
        assert len(booths_page2) == 1
        
        # Verify they are different booths
        assert booths_page1[0].id != booths_page2[0].id
    
    def test_list_booths_empty_result(self, booth_service):
        """Test listing booths when no booths exist."""
        # Create a new database session with no booths
        booths = booth_service.list_booths(event_id=99999)
        
        assert len(booths) == 0


class TestBoothServiceUpdateBoothStatus:
    """Test BoothService.update_booth_status method."""
    
    def test_update_booth_status_success(self, booth_service, test_booth):
        """Test successful booth status update."""
        updated_booth = booth_service.update_booth_status(
            booth_id=test_booth.id,
            status="closed"
        )
        
        assert updated_booth.id == test_booth.id
        assert updated_booth.status == "closed"
    
    def test_update_booth_status_to_inactive(self, booth_service, test_booth):
        """Test updating booth status to inactive."""
        updated_booth = booth_service.update_booth_status(
            booth_id=test_booth.id,
            status="inactive"
        )
        
        assert updated_booth.status == "inactive"
    
    def test_update_booth_status_not_found(self, booth_service):
        """Test updating status of non-existent booth."""
        with pytest.raises(BoothNotFoundError) as exc_info:
            booth_service.update_booth_status(
                booth_id=99999,
                status="closed"
            )
        
        assert exc_info.value.error_code == "BOOTH_NOT_FOUND"


class TestBoothServiceValidateBoothBelongsToEvent:
    """Test BoothService.validate_booth_belongs_to_event method."""
    
    def test_validate_booth_belongs_to_event_success(self, booth_service, test_booth, test_event):
        """Test validation succeeds when booth belongs to event."""
        booth = booth_service.validate_booth_belongs_to_event(
            booth_id=test_booth.id,
            event_id=test_event.id
        )
        
        assert booth.id == test_booth.id
        assert booth.event_id == test_event.id
    
    def test_validate_booth_belongs_to_event_wrong_event(self, booth_service, test_booth):
        """Test validation fails when booth belongs to different event."""
        with pytest.raises(BoothNotInEventError) as exc_info:
            booth_service.validate_booth_belongs_to_event(
                booth_id=test_booth.id,
                event_id=99999
            )
        
        assert exc_info.value.error_code == "BOOTH_NOT_IN_EVENT"
        assert exc_info.value.booth_id == test_booth.id
        assert exc_info.value.event_id == 99999
    
    def test_validate_booth_belongs_to_event_booth_not_found(self, booth_service, test_event):
        """Test validation fails when booth doesn't exist."""
        with pytest.raises(BoothNotFoundError) as exc_info:
            booth_service.validate_booth_belongs_to_event(
                booth_id=99999,
                event_id=test_event.id
            )
        
        assert exc_info.value.error_code == "BOOTH_NOT_FOUND"


class TestBoothServiceValidateBoothActive:
    """Test BoothService.validate_booth_active method."""
    
    def test_validate_booth_active_success(self, booth_service, test_booth):
        """Test validation succeeds for active booth."""
        booth = booth_service.validate_booth_active(test_booth.id)
        
        assert booth.id == test_booth.id
        assert booth.status == "active"
    
    def test_validate_booth_active_inactive_booth(self, booth_service, inactive_booth):
        """Test validation fails for inactive booth."""
        with pytest.raises(BoothInactiveError) as exc_info:
            booth_service.validate_booth_active(inactive_booth.id)
        
        assert exc_info.value.error_code == "BOOTH_INACTIVE"
        assert exc_info.value.booth_id == inactive_booth.id
    
    def test_validate_booth_active_closed_booth(self, booth_service, test_booth):
        """Test validation fails for closed booth."""
        # Update booth to closed status
        test_booth.status = "closed"
        booth_service.db.commit()
        
        with pytest.raises(BoothInactiveError) as exc_info:
            booth_service.validate_booth_active(test_booth.id)
        
        assert exc_info.value.error_code == "BOOTH_INACTIVE"
    
    def test_validate_booth_active_booth_not_found(self, booth_service):
        """Test validation fails when booth doesn't exist."""
        with pytest.raises(BoothNotFoundError) as exc_info:
            booth_service.validate_booth_active(99999)
        
        assert exc_info.value.error_code == "BOOTH_NOT_FOUND"


class TestBoothServiceIntegration:
    """Integration tests for complete booth management flow."""
    
    def test_complete_booth_lifecycle(self, booth_service, test_event):
        """Test complete booth lifecycle: create -> get -> update -> validate."""
        # Step 1: Create booth
        booth = booth_service.create_booth(
            event_id=test_event.id,
            name="Lifecycle Test Booth",
            class_name="Class 7G"
        )
        booth_id = booth.id
        
        # Step 2: Get booth
        retrieved_booth = booth_service.get_booth(booth_id)
        assert retrieved_booth.name == "Lifecycle Test Booth"
        assert retrieved_booth.status == "active"
        
        # Step 3: Validate booth is active
        booth_service.validate_booth_active(booth_id)
        
        # Step 4: Validate booth belongs to event
        booth_service.validate_booth_belongs_to_event(booth_id, test_event.id)
        
        # Step 5: Update booth status to inactive
        updated_booth = booth_service.update_booth_status(booth_id, "inactive")
        assert updated_booth.status == "inactive"
        
        # Step 6: Verify validation now fails
        with pytest.raises(BoothInactiveError):
            booth_service.validate_booth_active(booth_id)
    
    def test_list_booths_multiple_events(self, booth_service, test_db):
        """Test listing booths across multiple events."""
        # Create two events
        event1 = Event(
            name="Event 1",
            start_time=datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone.utc),
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        event2 = Event(
            name="Event 2",
            start_time=datetime(2024, 2, 1, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 2, 1, 18, 0, 0, tzinfo=timezone.utc),
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        test_db.add_all([event1, event2])
        test_db.commit()
        test_db.refresh(event1)
        test_db.refresh(event2)
        
        # Create booths for each event
        booth1 = booth_service.create_booth(event1.id, "Booth 1", "Class A")
        booth2 = booth_service.create_booth(event1.id, "Booth 2", "Class B")
        booth3 = booth_service.create_booth(event2.id, "Booth 3", "Class C")
        
        # List all booths
        all_booths = booth_service.list_booths()
        assert len(all_booths) == 3
        
        # List booths for event1
        event1_booths = booth_service.list_booths(event_id=event1.id)
        assert len(event1_booths) == 2
        
        # List booths for event2
        event2_booths = booth_service.list_booths(event_id=event2.id)
        assert len(event2_booths) == 1
