from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    watched_books = relationship("WatchedBook", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("NotificationLog", back_populates="user", cascade="all, delete-orphan")


class WatchedBook(Base):
    __tablename__ = "watched_books"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(String(50), nullable=False, index=True)
    card_type = Column(String(20), default="Card1")
    title = Column(String(300), nullable=False)
    author = Column(String(200), default="")
    
    # Availability Tracking
    is_available = Column(Boolean, default=None)  # True = has available copy, False = all borrowed, None = unknown
    copies_available = Column(Integer, default=0)
    copies_total = Column(Integer, default=0)
    copies_details = Column(Text, default="[]")  # JSON string of copy locations
    
    notify_on_available = Column(Boolean, default=True)
    last_notified_at = Column(DateTime, nullable=True)
    last_checked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="watched_books")


class NotificationLog(Base):
    __tablename__ = "notifications_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    status = Column(String(50), default="sent")  # sent, failed, skipped
    details = Column(Text, default="")
    sent_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
