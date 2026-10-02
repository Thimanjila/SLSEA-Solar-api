from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class Province(Base):
    __tablename__ = "provinces"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    districts: Mapped[list["District"]] = relationship(back_populates="province")

class District(Base):
    __tablename__ = "districts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    province_id: Mapped[int] = mapped_column(ForeignKey("provinces.id"), nullable=False)
    province: Mapped["Province"] = relationship(back_populates="districts")
    substations: Mapped[list["GridSubstation"]] = relationship(back_populates="district")

class GridSubstation(Base):
    __tablename__ = "grid_substations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    district_id: Mapped[int] = mapped_column(ForeignKey("districts.id"), nullable=False)
    district: Mapped["District"] = relationship(back_populates="substations")
    installations: Mapped[list["SolarInstallation"]] = relationship(back_populates="substation")

class SolarInstallation(Base):
    __tablename__ = "solar_installations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    site_name: Mapped[str] = mapped_column(String(160), nullable=False)
    meter_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    capacity_kw: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    substation_id: Mapped[int] = mapped_column(ForeignKey("grid_substations.id"), nullable=False)
    substation: Mapped["GridSubstation"] = relationship(back_populates="installations")
    readings: Mapped[list["GenerationReading"]] = relationship(
        back_populates="installation", cascade="all, delete-orphan"
    )

class GenerationReading(Base):
    __tablename__ = "generation_readings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    installation_id: Mapped[int] = mapped_column(ForeignKey("solar_installations.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    power_kw: Mapped[float] = mapped_column(Float, nullable=False)
    cumulative_energy_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    voltage: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    installation: Mapped["SolarInstallation"] = relationship(back_populates="readings")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    district_id: Mapped[int | None] = mapped_column(ForeignKey("districts.id"), nullable=True)
    installation_id: Mapped[int | None] = mapped_column(ForeignKey("solar_installations.id"), nullable=True)
