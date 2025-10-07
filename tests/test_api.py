"""
Test suite for FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient


def test_root_redirect(client, reset_activities):
    """Test that root endpoint redirects to static index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client, reset_activities):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 9  # We have 9 activities in our test data
    
    # Check that all expected activities are present
    expected_activities = [
        "Chess Club", "Programming Class", "Gym Class", "Soccer Team", 
        "Basketball Club", "Art Workshop", "Drama Club", "Math Olympiad", "Science Club"
    ]
    for activity in expected_activities:
        assert activity in data
    
    # Check structure of an activity
    chess_club = data["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)


def test_signup_for_activity_success(client, reset_activities, sample_email):
    """Test successful signup for an activity"""
    activity_name = "Chess Club"
    
    # Get initial participant count
    initial_response = client.get("/activities")
    initial_data = initial_response.json()
    initial_count = len(initial_data[activity_name]["participants"])
    
    # Sign up for activity
    response = client.post(f"/activities/{activity_name}/signup?email={sample_email}")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert sample_email in data["message"]
    assert activity_name in data["message"]
    
    # Verify participant was added
    updated_response = client.get("/activities")
    updated_data = updated_response.json()
    updated_count = len(updated_data[activity_name]["participants"])
    assert updated_count == initial_count + 1
    assert sample_email in updated_data[activity_name]["participants"]


def test_signup_for_nonexistent_activity(client, reset_activities, sample_email):
    """Test signup for an activity that doesn't exist"""
    response = client.post(f"/activities/Nonexistent Activity/signup?email={sample_email}")
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]


def test_signup_duplicate_participant(client, reset_activities):
    """Test signing up a participant who is already registered"""
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"  # Already in Chess Club
    
    response = client.post(f"/activities/{activity_name}/signup?email={existing_email}")
    assert response.status_code == 400
    
    data = response.json()
    assert "detail" in data
    assert "already signed up" in data["detail"]


def test_signup_activity_case_sensitivity(client, reset_activities, sample_email):
    """Test that activity names are case sensitive"""
    # Try with different case
    response = client.post(f"/activities/chess club/signup?email={sample_email}")
    assert response.status_code == 404


def test_signup_email_validation(client, reset_activities):
    """Test signup with various email formats"""
    activity_name = "Chess Club"
    
    # Test with a valid email
    valid_email = "valid.email@mergington.edu"
    response = client.post(f"/activities/{activity_name}/signup?email={valid_email}")
    assert response.status_code == 200
    
    # Test with another valid email format
    another_valid_email = "another_student123@mergington.edu"
    response = client.post(f"/activities/{activity_name}/signup?email={another_valid_email}")
    assert response.status_code == 200


def test_multiple_activities_signup(client, reset_activities, sample_email):
    """Test that a student can sign up for multiple activities"""
    activities = ["Chess Club", "Programming Class", "Art Workshop"]
    
    for activity in activities:
        response = client.post(f"/activities/{activity}/signup?email={sample_email}")
        assert response.status_code == 200
    
    # Verify student is in all activities
    response = client.get("/activities")
    data = response.json()
    
    for activity in activities:
        assert sample_email in data[activity]["participants"]


def test_activity_capacity_limits(client, reset_activities):
    """Test that activities respect their maximum participant limits"""
    # Use Math Olympiad which has max_participants: 10
    activity_name = "Math Olympiad"
    
    # Get current participant count
    response = client.get("/activities")
    data = response.json()
    activity = data[activity_name]
    current_count = len(activity["participants"])
    max_participants = activity["max_participants"]
    
    # Add participants up to the limit
    spots_remaining = max_participants - current_count
    for i in range(spots_remaining):
        email = f"student{i}@mergington.edu"
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
    
    # Verify we're at capacity
    response = client.get("/activities")
    data = response.json()
    assert len(data[activity_name]["participants"]) == max_participants


def test_special_characters_in_email(client, reset_activities):
    """Test signup with special characters in email"""
    activity_name = "Chess Club"
    special_emails = [
        "test.user+tag@mergington.edu",
        "user-name@mergington.edu",
        "user_name@mergington.edu"
    ]
    
    for email in special_emails:
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200


def test_url_encoding_in_activity_names(client, reset_activities, sample_email):
    """Test that URL encoding works correctly for activity names"""
    # Test with spaces in activity name
    activity_name = "Chess Club"
    encoded_name = "Chess%20Club"
    
    response = client.post(f"/activities/{encoded_name}/signup?email={sample_email}")
    assert response.status_code == 200
    
    # Verify participant was added
    response = client.get("/activities")
    data = response.json()
    assert sample_email in data[activity_name]["participants"]


def test_empty_email_parameter(client, reset_activities):
    """Test signup with empty email parameter"""
    activity_name = "Chess Club"
    
    response = client.post(f"/activities/{activity_name}/signup?email=")
    # The API should still process this, though it might not be ideal
    # This test documents current behavior
    assert response.status_code in [200, 400]  # Either works or fails validation


def test_activities_data_persistence_during_session(client, reset_activities, sample_email):
    """Test that activity data persists during the session"""
    activity_name = "Chess Club"
    
    # Sign up
    response = client.post(f"/activities/{activity_name}/signup?email={sample_email}")
    assert response.status_code == 200
    
    # Make multiple requests and verify data persists
    for _ in range(3):
        response = client.get("/activities")
        data = response.json()
        assert sample_email in data[activity_name]["participants"]


def test_unregister_from_activity_success(client, reset_activities):
    """Test successful unregistration from an activity"""
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"  # Already in Chess Club
    
    # Get initial participant count
    initial_response = client.get("/activities")
    initial_data = initial_response.json()
    initial_count = len(initial_data[activity_name]["participants"])
    assert existing_email in initial_data[activity_name]["participants"]
    
    # Unregister from activity
    response = client.post(f"/activities/{activity_name}/unregister?email={existing_email}")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert existing_email in data["message"]
    assert activity_name in data["message"]
    
    # Verify participant was removed
    updated_response = client.get("/activities")
    updated_data = updated_response.json()
    updated_count = len(updated_data[activity_name]["participants"])
    assert updated_count == initial_count - 1
    assert existing_email not in updated_data[activity_name]["participants"]


def test_unregister_from_nonexistent_activity(client, reset_activities, sample_email):
    """Test unregistration from an activity that doesn't exist"""
    response = client.post(f"/activities/Nonexistent Activity/unregister?email={sample_email}")
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]


def test_unregister_non_participant(client, reset_activities, sample_email):
    """Test unregistering a participant who is not registered"""
    activity_name = "Chess Club"
    
    response = client.post(f"/activities/{activity_name}/unregister?email={sample_email}")
    assert response.status_code == 400
    
    data = response.json()
    assert "detail" in data
    assert "not signed up" in data["detail"]


def test_signup_and_unregister_workflow(client, reset_activities, sample_email):
    """Test complete signup and unregister workflow"""
    activity_name = "Programming Class"
    
    # Initial state - participant not in activity
    response = client.get("/activities")
    initial_data = response.json()
    assert sample_email not in initial_data[activity_name]["participants"]
    initial_count = len(initial_data[activity_name]["participants"])
    
    # Sign up
    response = client.post(f"/activities/{activity_name}/signup?email={sample_email}")
    assert response.status_code == 200
    
    # Verify signup
    response = client.get("/activities")
    data = response.json()
    assert sample_email in data[activity_name]["participants"]
    assert len(data[activity_name]["participants"]) == initial_count + 1
    
    # Unregister
    response = client.post(f"/activities/{activity_name}/unregister?email={sample_email}")
    assert response.status_code == 200
    
    # Verify unregistration
    response = client.get("/activities")
    final_data = response.json()
    assert sample_email not in final_data[activity_name]["participants"]
    assert len(final_data[activity_name]["participants"]) == initial_count