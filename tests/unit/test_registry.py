import pytest
from app.main import registry
from app.metadata.registry import MetadataError, MetadataRegistry

def test_all_sample_views_load():
    assert {view.name for view in registry.list_views()} == {
        "customers", "investments", "products", "accounts", "positions"
    }

def test_composite_relationship_is_metadata_driven():
    relationship = registry.get_relationship("accounts", "positions")
    assert len(relationship.column_mappings) == 2

def test_duplicate_yaml_keys_fail_fast(tmp_path):
    (tmp_path / "broken.yaml").write_text("name: customers\nname: duplicate\n")
    with pytest.raises(MetadataError, match="Duplicate YAML key"):
        MetadataRegistry(tmp_path)
