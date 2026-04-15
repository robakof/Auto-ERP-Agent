from pydantic import BaseModel, ConfigDict

from app.db.models.location import LocationType


class LocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: LocationType
    parent_id: int | None
