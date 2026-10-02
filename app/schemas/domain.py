from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ProvinceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

class DistrictOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    province_id: int

class SubstationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    district_id: int

class InstallationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    site_name: str
    meter_id: str
    capacity_kw: float
    address: str
    substation_id: int

class ReadingCreate(BaseModel):
    timestamp: datetime
    power_kw: float = Field(ge=0)
    cumulative_energy_kwh: float = Field(ge=0)
    voltage: float = Field(gt=0)

class ReadingOut(ReadingCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    installation_id: int
    created_at: datetime

class InstallationComposite(BaseModel):
    installation: InstallationOut
    substation: SubstationOut
    district: DistrictOut
    province: ProvinceOut
    last_known_reading: ReadingOut | None

class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int
    next: str | None
    previous: str | None

class ReadingPage(BaseModel):
    data: list[ReadingOut]
    meta: PageMeta

class GenerationSummary(BaseModel):
    district_id: int
    district_name: str
    current_total_power_kw: float
    today_total_energy_kwh: float
    installation_count: int
    reading_count_today: int

class ErrorDetail(BaseModel):
    code: str
    message: str
    detail: str | None = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
