from bson import ObjectId
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        def validate_objectid(v: str) -> ObjectId:
            if isinstance(v, ObjectId):
                return v
            if isinstance(v, str) and ObjectId.is_valid(v):
                return ObjectId(v)
            raise ValueError("Invalid ObjectId")
        return core_schema.no_info_plain_validator_function(
            validate_objectid,
            serialization=core_schema.plain_serializer_function_ser_schema(lambda v: str(v))
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, handler):
        # Represent this field as a string in the JSON schema
        return handler(core_schema.str_schema())