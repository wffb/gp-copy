import pytest


def test_get_fields_success(client, sample_field):
    """Test successfully retrieving fields."""
    response = client.get("/api/v1/fields/")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1

def test_get_fields_empty(client):
    """Test retrieving fields when none exist."""
    response = client.get("/api/v1/fields/")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 0

def test_get_fields_structure(client, sample_field):
    """Test field response structure."""
    response = client.get("/api/v1/fields/")

    assert response.status_code == 200
    fields = response.json()["data"]

    field = fields[0]
    assert "id" in field
    assert "code" in field
    assert "name" in field
    assert "subfields" in field
    assert isinstance(field["subfields"], list)

def test_get_fields_with_subfields(client, sample_field, sample_subfield):
    """Test fields include their subfields."""
    response = client.get("/api/v1/fields/")

    assert response.status_code == 200
    fields = response.json()["data"]

    parent = next(f for f in fields if f["id"] == str(sample_field.id))
    assert len(parent["subfields"]) == 1
    assert parent["subfields"][0]["id"] == str(sample_subfield.id)
    assert parent["subfields"][0]["code"] == sample_subfield.code

def test_get_fields_sorted_by_sort_order(client, field_factory):
    """Test fields are sorted by sort_order."""
    field_factory(code="z", name="Z Field", sort_order=3)
    field_factory(code="a", name="A Field", sort_order=1)
    field_factory(code="m", name="M Field", sort_order=2)

    response = client.get("/api/v1/fields/")

    assert response.status_code == 200
    fields = response.json()["data"]

    assert fields[0]["name"] == "A Field"
    assert fields[1]["name"] == "M Field"
    assert fields[2]["name"] == "Z Field"

def test_get_fields_nulls_last_in_sorting(client, field_factory):
    """Test fields with null sort_order come last."""
    field_factory(code="sorted", name="Sorted", sort_order=1)
    field_factory(code="unsorted", name="Unsorted", sort_order=None)

    response = client.get("/api/v1/fields/")

    assert response.status_code == 200
    fields = response.json()["data"]

    sorted_fields = [f for f in fields if f["sort_order"] is not None]
    unsorted_fields = [f for f in fields if f["sort_order"] is None]

    for i, field in enumerate(fields):
        if i < len(sorted_fields):
            assert field["sort_order"] is not None
        else:
            assert field["sort_order"] is None

def test_get_fields_subfields_sorted(client, sample_field, field_factory):
    """Test subfields are also sorted."""
    field_factory(code="sub3", name="Sub 3", parent_id=sample_field.id, sort_order=3)
    field_factory(code="sub1", name="Sub 1", parent_id=sample_field.id, sort_order=1)
    field_factory(code="sub2", name="Sub 2", parent_id=sample_field.id, sort_order=2)

    response = client.get("/api/v1/fields/")

    assert response.status_code == 200
    fields = response.json()["data"]

    parent = next(f for f in fields if f["id"] == str(sample_field.id))
    subfields = parent["subfields"]

    assert subfields[0]["name"] == "Sub 1"
    assert subfields[1]["name"] == "Sub 2"
    assert subfields[2]["name"] == "Sub 3"

def test_get_fields_only_top_level(client, sample_field, sample_subfield):
    """Test only top-level fields are returned (subfields nested)."""
    response = client.get("/api/v1/fields/")

    assert response.status_code == 200
    fields = response.json()["data"]

    top_level_ids = [f["id"] for f in fields]
    assert str(sample_field.id) in top_level_ids
    assert str(sample_subfield.id) not in top_level_ids

def test_get_fields_no_authentication_required(client, sample_field):
    """Test fields endpoint doesn't require authentication."""
    response = client.get("/api/v1/fields/")

    assert response.status_code == 200

def test_get_fields_multiple_parents_with_children(client, field_factory):
    """Test multiple parent fields each with their own subfields."""
    parent1 = field_factory(code="parent1", name="Parent 1")
    parent2 = field_factory(code="parent2", name="Parent 2")

    field_factory(code="p1sub1", name="P1 Sub 1", parent_id=parent1.id)
    field_factory(code="p1sub2", name="P1 Sub 2", parent_id=parent1.id)
    field_factory(code="p2sub1", name="P2 Sub 1", parent_id=parent2.id)

    response = client.get("/api/v1/fields/")

    assert response.status_code == 200
    fields = response.json()["data"]

    p1 = next(f for f in fields if f["id"] == str(parent1.id))
    p2 = next(f for f in fields if f["id"] == str(parent2.id))

    assert len(p1["subfields"]) == 2
    assert len(p2["subfields"]) == 1
