def test_signup_and_login(client):
    # 1. Test Signup
    signup_payload = {
        "email": "pytest_user@example.com",
        "password": "TestPassword123!",
        "full_name": "Pytest User"
    }
    response = client.post("/api/v1/auth/signup", json=signup_payload)
    assert response.status_code in (201, 400)

    # 2. Test Login
    login_data = {
        "username": "pytest_user@example.com",
        "password": "TestPassword123!"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"