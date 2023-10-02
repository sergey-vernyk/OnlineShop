from rest_framework.schemas import AutoSchema


class PresentCardActionsSchema(AutoSchema):
    """
    Schema with particular fields inside
    """

    def get_serializer_fields(self, path, method):
        """
        Return empty list, since no sense to show serializer fields in API
        """
        return []
