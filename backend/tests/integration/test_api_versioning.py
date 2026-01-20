"""Tests for API v1 versioning to ensure all endpoints use correct prefix."""

from app.main import app


def test_all_endpoints_use_v1_prefix():
    """Verify all API endpoints include /v1 prefix in OpenAPI schema."""
    openapi_schema = app.openapi_schema
    assert openapi_schema is not None, "OpenAPI schema not configured"

    paths = openapi_schema.paths
    assert paths is not None, "OpenAPI paths not found"

    # Check that all /api paths use /v1
    for path_str in paths:
        if isinstance(path_str, str) and path_str.startswith("/api/"):
            assert path_str.startswith("/api/v1/"), (
                f"Endpoint '{path_str}' missing v1 prefix. All API endpoints must start with '/api/v1/'"
            )


def test_old_api_endpoints_not_in_schema():
    """Verify old /api/* paths (without v1) are not in the OpenAPI schema."""
    openapi_schema = app.openapi_schema
    paths = openapi_schema.paths
    assert paths is not None

    # Ensure no old /api/auth, /api/admin, etc. paths exist
    invalid_paths = [p for p in paths if isinstance(p, str) and p.startswith("/api/") and not p.startswith("/api/v1/")]

    assert len(invalid_paths) == 0, f"Found endpoints without v1 prefix: {invalid_paths}"


def test_v1_endpoints_exist():
    """Test that v1 endpoints exist in OpenAPI schema."""
    openapi_schema = app.openapi_schema
    paths = openapi_schema.paths
    assert paths is not None

    # List of paths to check (converted to strings for comparison)
    path_list = [p for p in paths if isinstance(p, str)]

    # At least some v1 endpoints should exist
    v1_paths = [p for p in path_list if "/api/v1/" in p]
    assert len(v1_paths) > 0, "No /api/v1 endpoints found in OpenAPI schema"


def test_auth_controller_v1_endpoints():
    """Test that auth endpoints are available under /api/v1/auth."""
    openapi_schema = app.openapi_schema
    paths = openapi_schema.paths
    assert paths is not None

    path_list = [p for p in paths if isinstance(p, str)]

    # Only check caregiver auth controller endpoints (admin auth lives under /api/v1/admin/auth)
    auth_paths = [p for p in path_list if p.startswith("/api/v1/auth/")]
    assert len(auth_paths) > 0, "No /api/v1/auth endpoints found"


def test_admin_controller_v1_endpoints():
    """Test that admin endpoints are available under /api/v1/admin."""
    openapi_schema = app.openapi_schema
    paths = openapi_schema.paths
    assert paths is not None

    # Check for admin endpoints
    path_list = [p for p in paths if isinstance(p, str)]
    admin_paths = [p for p in path_list if "/admin" in p]
    assert len(admin_paths) > 0, "No admin endpoints found"

    # All admin paths should start with /api/v1/admin
    for path in admin_paths:
        assert "/api/v1/admin" in path, f"Admin endpoint '{path}' doesn't use /api/v1/admin prefix"


def test_health_endpoint_v1():
    """Test that health check endpoint exists under /api/v1."""
    openapi_schema = app.openapi_schema
    paths = openapi_schema.paths
    assert paths is not None

    path_list = [p for p in paths if isinstance(p, str)]
    health_paths = [p for p in path_list if "health" in p]
    assert len(health_paths) > 0, "No health endpoints found"

    for path in health_paths:
        assert "/api/v1/health" in path, f"Health endpoint '{path}' doesn't use /api/v1/health prefix"
