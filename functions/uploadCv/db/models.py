import hashlib
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    TIMESTAMP,
    ForeignKey,
    text,
    Index,
    Date,
    Boolean,
    SmallInteger,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


def generate_skill_hash(category, subcategory, subsubcategory, tools):
    """Generate deterministic SHA-256 hash for a skill"""
    key = f"{category}|{subcategory}|{subsubcategory}|{tools}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def generate_certificate_hash(certProvider, certName):
    """Generate a deterministic SHA256 hash from certificate provider and name."""
    key = f"{certProvider.strip().lower()}_{certName.strip().lower()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


class MasterSkills(Base):
    __tablename__ = "MasterSkills"

    hashId = Column(String(64), primary_key=True)
    category = Column(String, nullable=True)
    subcategory = Column(String, nullable=True)
    subsubcategory = Column(String, nullable=True)
    tools = Column(String, nullable=True)
    L1 = Column(Text, nullable=True)
    L2 = Column(Text, nullable=True)
    L3 = Column(Text, nullable=True)

    def __init__(self, category, subcategory, subsubcategory, tools, **kwargs):
        self.category = category
        self.subcategory = subcategory
        self.subsubcategory = subsubcategory
        self.tools = tools
        self.hashId = generate_skill_hash(category, subcategory, subsubcategory, tools)
        for k, v in kwargs.items():
            setattr(self, k, v)


class Employee(Base):
    __tablename__ = "Employee"

    id = Column(Integer, primary_key=True, autoincrement=True)
    empId = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    jobTitle = Column(String, nullable=True)
    department = Column(String, nullable=True)
    managerEmail = Column(String, nullable=True)

    __table_args__ = (Index("ix_employee_managerEmail", "managerEmail"),)


class EmployeeSkills(Base):
    __tablename__ = "EmployeeSkills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    empId = Column(Integer, ForeignKey("Employee.id"), nullable=False)
    skillHashId = Column(String(64), nullable=False)
    levelSelected = Column(String, nullable=True)
    approvedByEmail = Column(String, nullable=True)
    approvalStatus = Column(String, nullable=True)
    rejectionReason = Column(Text, nullable=True)
    requestedAt = Column(TIMESTAMP, nullable=True)
    reviewedAt = Column(TIMESTAMP, nullable=True)

    __table_args__ = (
        Index("ix_employee_skills_empId", "empId"),
        Index("ix_employee_skills_skillHashId", "skillHashId"),
    )


class MasterCertificate(Base):
    __tablename__ = "MasterCertificate"

    hashId = Column(String(64), primary_key=True)
    certProvider = Column(String(255), nullable=False)
    certName = Column(String(255), nullable=False)
    certLevel = Column(String(50), nullable=True)
    validYears = Column(Integer, nullable=True)
    isActive = Column(SmallInteger, nullable=False)

    def __init__(
        self,
        certProvider,
        certName,
        certLevel=None,
        validYears=None,
        isActive=0,
        **kwargs,
    ):
        self.certProvider = certProvider
        self.certName = certName
        self.certLevel = certLevel
        self.validYears = validYears
        self.isActive = isActive
        self.hashId = generate_certificate_hash(certProvider, certName)

        # Allow flexible attribute setting (if new columns are added later)
        for k, v in kwargs.items():
            setattr(self, k, v)


class EmployeeCertificate(Base):
    __tablename__ = "EmployeeCertificate"

    id = Column(Integer, primary_key=True, autoincrement=True)
    empId = Column(String(255), nullable=False)
    certHashId = Column(String(64), nullable=False)
    certProvider = Column(String(255), nullable=False)
    certName = Column(String(255), nullable=False)
    certLevel = Column(String(50), nullable=True)

    # Later
    yearAchieved = Column(Integer, nullable=True)
    expiryDate = Column(Date, nullable=True)
    certLink = Column(String, nullable=True)
    certIdExternal = Column(String(255), nullable=True)
    isVerified = Column(SmallInteger, default=False)

    # Current Priority
    approvedByEmail = Column(String, nullable=True)
    approvalStatus = Column(String, nullable=True)
    rejectionReason = Column(Text, nullable=True)
    requestedAt = Column(TIMESTAMP, nullable=True)
    reviewedAt = Column(TIMESTAMP, nullable=True)
