import random
import uuid
from datetime import datetime

from faker import Faker
from sqlalchemy import DECIMAL, TIMESTAMP, Column, String, Text, create_engine
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, sessionmaker

# Database connection URL
# Replace with actual connection string
engine = create_engine("postgresql://postgres:postgres@localhost:5432/postal_service")

# Session setup
Session = sessionmaker(bind=engine)
session = Session()

# Base class for ORM models
Base = declarative_base()


# Define the PackageTracking model for the database
class PackageTracking(Base):
    __tablename__ = "package_tracking"
    __table_args__ = {
        "extend_existing": True
    }  # To allow modification if the table exists

    tracking_code = Column(
        String(50), primary_key=True
    )  # Tracking code for the package
    status = Column(
        String(50), nullable=False
    )  # Status of the package (e.g., shipped, out for delivery)
    last_update = Column(
        TIMESTAMP, default=datetime, nullable=False
    )  # Timestamp for the last update
    location = Column(Text, nullable=False)  # Location of the package
    weight_kg = Column(DECIMAL(10, 2))  # Weight of the package in kilograms
    shipping_type = Column(
        String(50), nullable=False
    )  # Type of shipping (e.g., standard, express)


# Create the table in the database
Base.metadata.create_all(engine)

print("PackageTracking table created successfully!")

# Initialize Faker for generating random data
faker = Faker()

# Define possible values for status and shipping type
statuses = ["Processing", "Shipped", "Out for Delivery", "Delivered", "Delayed"]
shipping_types = ["Standard", "Express"]

# Generate 50 sample package records
packages = []
for _ in range(50):
    package = PackageTracking(
        tracking_code=f"PKG{faker.random_int(min=100000, max=999999)}",  # Random tracking code
        status=random.choice(statuses),  # Random status
        last_update=faker.date_time_this_year(),  # Random last update within this year
        location=faker.city(),  # Random location (city)
        weight_kg=round(
            random.uniform(0.5, 10.0), 2
        ),  # Random weight between 0.5kg and 10.0kg
        shipping_type=random.choice(shipping_types),  # Random shipping type
    )
    session.add(package)

# Insert the records in bulk for efficiency
session.bulk_save_objects(packages)
session.commit()

print("Inserted 50 package records successfully!")


# Define the User model for the database
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    user_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )  # User ID (UUID)
    name = Column(String(100), nullable=False)  # User's name
    email = Column(String(100), unique=True, nullable=False)  # User's email (unique)
    phone_number = Column(String(20), nullable=True)  # User's phone number (optional)
    address = Column(Text, nullable=False)  # User's address
    city = Column(String(50), nullable=False)  # User's city
    postal_code = Column(String(20), nullable=False)  # User's postal code
    country = Column(String(50), nullable=False)  # User's country
    created_at = Column(
        TIMESTAMP, default=datetime, nullable=False
    )  # Account creation timestamp


# Create the table in the database
Base.metadata.create_all(engine)

print("User table created successfully!")

# Generate 50 sample user records using Faker
users = []
for _ in range(50):
    user = User(
        user_id=uuid.uuid4(),  # Generate a new UUID for the user
        name=faker.name(),  # Random name
        email=faker.email(),  # Random email
        phone_number=faker.phone_number()[
            :20
        ],  # Random phone number (max 20 characters)
        address=faker.address(),  # Random address
        city=faker.city(),  # Random city
        postal_code=faker.postcode(),  # Random postal code
        country=faker.country(),  # Random country
        created_at=faker.date_this_decade(),  # Random date in the last decade
    )
    users.append(user)

# Insert the records in bulk for efficiency
session.bulk_save_objects(users)
session.commit()

print("Inserted 50 fake user records successfully!")


# Define the UserLLMInteraction model for logging interactions with an LLM
class UserLLMInteraction(Base):
    __tablename__ = "user_llm_interactions"
    __table_args__ = {"extend_existing": True}

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )  # Unique interaction ID
    question = Column(Text, nullable=False)  # User's question to the LLM
    response = Column(Text, nullable=False)  # LLM's response to the question
    interaction_time = Column(
        TIMESTAMP, default=datetime, nullable=False
    )  # Timestamp of the interaction


# Create the table in the database
Base.metadata.create_all(engine)

print("UserLLMInteraction table created successfully!")
