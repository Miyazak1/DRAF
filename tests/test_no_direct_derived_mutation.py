import pytest
from pydantic import ValidationError

from rpf.core.views import PersonView, RelationshipView


def test_derived_views_are_frozen():
    person = PersonView(process_id="p1", apparent_labels=["careful"])
    with pytest.raises(ValidationError):
        person.apparent_labels = ["primitive_trait"]

    relationship = RelationshipView(phase_label="fragile")
    with pytest.raises(ValidationError):
        relationship.phase_label = "mutated"
