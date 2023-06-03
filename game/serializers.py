from typing import List, Dict

from sqlalchemy import inspect

from entities.models import User, UserSession
from repos.managers import UserManager
from utils.exceptions import ImproperlyConfigured, ShouldBeCalledOnInstanceException


class BaseSerializer:
    """Base serializer class for models"""

    def __init__(self, instance=None, data=None, many: bool = False):
        self.errors = {}
        self.instance = instance
        if instance:
            self._validate_instance(self.instance)
        self.data = data
        if data:
            self.validate_fields(self.data)
        self.fields = self.get_fields()
        self.many = many
        self.original_passed_data = data

    def get_fields(self) -> dict:
        """Get fields from model and return only those that are defined in Meta.fields"""
        if hasattr(self, "Meta") and hasattr(self.Meta, "model"):
            fields: dict = {}

            field_dict = {
                column.name: str(column.type)
                for column in inspect(self.instance.__class__).columns
            }
            for key, val in field_dict.items():
                try:
                    if self.Meta.fields == "__all__":
                        return field_dict
                    if key in self.Meta.fields:
                        fields[key] = val
                except AttributeError:
                    try:
                        if key not in self.Meta.exclude:
                            fields[key] = val
                    except AttributeError:
                        return field_dict
            return fields
        else:
            raise ImproperlyConfigured(
                "You must define a 'Meta' class with a 'model' attribute."
            )

    def is_valid(self) -> bool:
        try:
            if self.errors:
                return False
            self.data = self.serialize()
            return True
        except (AttributeError, ValueError):
            return False

    def validate_fields(self, fields: dict) -> None:
        """Validate fields and return only those that are defined in Meta.fields"""
        for key, val in fields.items():
            if key not in self.Meta.fields:  # noqa
                self.errors[key] = "This field is not allowed."

    def save(self):
        """Save/update data to database"""
        if not self.instance:
            raise ShouldBeCalledOnInstanceException

        for key, val in self.original_passed_data.items():
            if key in self.Meta.fields:  # noqa
                UserManager().update_fields(self.instance, **{key: val})

        UserManager().refresh_from_db(self.instance)
        self.data = self.serialize()

    def _validate_instance(self, instance) -> None:
        """Validate if instance is of type defined in Meta.model"""
        if not isinstance(instance, self.Meta.model):  # noqa
            raise ValueError(
                f"Invalid instance type. Expected '{self.Meta.model.__name__}' instance."  # noqa
            )
        try:
            if self.Meta.fields and self.Meta.exlude:  # noqa
                raise AttributeError(
                    f"Invalid instance fields. Expected 'fields' or 'exclude' attribute."
                )
        except AttributeError:
            pass

    def _serialize_instance(self, instance) -> Dict[str, str]:
        """Serialize instance to dict."""
        serialized_data: dict = {}
        for field_name, field in self.fields.items():
            field_value = getattr(instance, field_name)
            serialized_data[field_name] = field_value
        return serialized_data

    def _serialize_queryset(self, queryset: list) -> List[dict]:
        serialized_data: list = []
        for instance in queryset:
            self._validate_instance(instance)
            serialized_data.append(self._serialize_instance(instance))
        return serialized_data

    def serialize(self) -> dict | List[dict] | None:
        if self.instance is not None:
            return self._serialize_instance(self.instance)
        elif self.data is not None:
            if self.many:
                return self._serialize_queryset(self.data)
            else:
                return self.data
        else:
            return None


class UserSerializer(BaseSerializer):
    """Serializer for link models"""

    class Meta:
        model = User
        exclude = ["password", "id"]


class UserUpdateSerializer(BaseSerializer):
    """Serializer for link models"""

    class Meta:
        model = User
        fields = ["email", "credits"]


class UserSessionSerializer(BaseSerializer):
    """Serializer for link models"""

    class Meta:
        model = UserSession
