from app.metadata.registry import MetadataRegistry

class AuthorizationPolicy:
    """Authorization is metadata-based: only registered logical views are visible."""
    def __init__(self, registry: MetadataRegistry):
        self.registry = registry

    def can_access_view(self, view_name: str) -> bool:
        try:
            self.registry.get_view(view_name)
        except Exception:
            return False
        return True
