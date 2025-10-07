"""
Integration tests for the school activity management system.
These tests verify that the API and frontend integration work correctly.
"""
import pytest
from fastapi.testclient import TestClient


def test_activity_signup_integration(client, reset_activities):
    """Test the complete flow that mirrors frontend usage"""
    # Get initial state
    response = client.get("/activities")
    assert response.status_code == 200
    initial_activities = response.json()
    
    # Test signing up for Chess Club
    activity_name = "Chess Club"
    email = "integration.test@mergington.edu"
    
    initial_participants = len(initial_activities[activity_name]["participants"])
    
    # Sign up
    signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert signup_response.status_code == 200
    
    # Verify the activity list reflects the change (like frontend would see)
    updated_response = client.get("/activities")
    updated_activities = updated_response.json()
    
    assert len(updated_activities[activity_name]["participants"]) == initial_participants + 1
    assert email in updated_activities[activity_name]["participants"]
    
    # Test unregistering (like delete button click)
    unregister_response = client.post(f"/activities/{activity_name}/unregister?email={email}")
    assert unregister_response.status_code == 200
    
    # Verify removal
    final_response = client.get("/activities")
    final_activities = final_response.json()
    
    assert len(final_activities[activity_name]["participants"]) == initial_participants
    assert email not in final_activities[activity_name]["participants"]


def test_multiple_users_same_activity(client, reset_activities):
    """Test multiple users signing up for the same activity"""
    activity_name = "Programming Class"
    users = ["user1@mergington.edu", "user2@mergington.edu", "user3@mergington.edu"]
    
    # Get initial state
    response = client.get("/activities")
    initial_count = len(response.json()[activity_name]["participants"])
    
    # Sign up multiple users
    for user in users:
        response = client.post(f"/activities/{activity_name}/signup?email={user}")
        assert response.status_code == 200
    
    # Verify all users are registered
    response = client.get("/activities")
    activities = response.json()
    participants = activities[activity_name]["participants"]
    
    assert len(participants) == initial_count + len(users)
    for user in users:
        assert user in participants


def test_error_handling_integration(client, reset_activities):
    """Test error scenarios that frontend needs to handle"""
    email = "error.test@mergington.edu"
    
    # Test 404 for non-existent activity
    response = client.post(f"/activities/Non Existent Activity/signup?email={email}")
    assert response.status_code == 404
    error_data = response.json()
    assert "detail" in error_data
    
    # Test 400 for duplicate signup
    response = client.post(f"/activities/Chess Club/signup?email={email}")
    assert response.status_code == 200  # First signup should work
    
    response = client.post(f"/activities/Chess Club/signup?email={email}")
    assert response.status_code == 400  # Second signup should fail
    error_data = response.json()
    assert "detail" in error_data
    assert "already signed up" in error_data["detail"]
    
    # Test 400 for unregistering non-participant
    response = client.post(f"/activities/Art Workshop/unregister?email=nonexistent@mergington.edu")
    assert response.status_code == 400
    error_data = response.json()
    assert "detail" in error_data
    assert "not signed up" in error_data["detail"]