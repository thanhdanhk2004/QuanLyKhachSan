from datetime import datetime

from sqlalchemy import column, Integer, String, Float, Column, Enum, Boolean, ForeignKey
from app import db, app
from enum import Enum as RoleEnum
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.types import DateTime
import uuid


class UserRole(RoleEnum):
    ADMIN = 1
    USER = 2
    STAFF = 3


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    avatar = Column(String(100),
                    default='https://res.cloudinary.com/dxxwcby8l/image/upload/v1646729533/zuur9gzztcekmyfenkfr.jpg')
    user_role = Column(Enum(UserRole), default=UserRole.USER)
    type = Column(String(50))  # Cột type để lưu trữ polymorphic identity
    comments = relationship('Comment', backref='user', lazy=True)
    reservation = relationship('Reservation', backref='user', lazy=True)

    # Cài đặt polymorphic inheritance
    __mapper_args__ = {
        'polymorphic_identity': 'user',  # Xác định danh tính polymorphic
        'polymorphic_on': 'type'  # Cột này lưu thông tin về loại user
    }


class User_Customer(User):
    __tablename__ = 'user_customer'

    id = Column(Integer, ForeignKey(User.id), primary_key=True)
    phone = Column(String(15), nullable=True)
    customer_tier = Column(String(20), nullable=False, default='NEW')
    annual_spending = Column(Float, nullable=False, default=0.0)
    last_updated_year = Column(Integer, default=datetime.now().year)

    # Override polymorphic_identity để xác định là user_customer
    __mapper_args__ = {
        'polymorphic_identity': 'user_customer'  # Danh tính của User_Customer
    }


class RoomType(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    price = Column(Float, nullable=False)
    max_guests = Column(Integer, nullable=False)
    proportion = Column(Float, nullable=False)
    coefficient = Column(Float, nullable=False)
    room = relationship('Room', backref='roomtype', lazy=True)
    image = Column(String(100), nullable=True)
    description = Column(String(255), nullable=True)
    commnents = relationship('Comment', backref='roomtype', lazy=True)

    def __str__(self):
        return self.name

class Room(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    roomtype_id = Column(Integer, ForeignKey(RoomType.id), nullable=False)
    booking  = relationship('Booking', backref='room', lazy=True)
    is_available = Column(Boolean, default=True, nullable=False)

    def __str__(self):
        return self.name

class Reservation(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(String(100), nullable=False)
    contact_phone = Column(String(15), nullable=False)
    reservation_date = Column(DateTime, default=datetime.now, nullable=False)
    checkin_date = Column(DateTime, nullable=False)
    checkout_date = Column(DateTime, nullable=False)
    reservation_code = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4())[:8])
    is_checked_in = Column(Boolean, default=False, nullable=False)
    is_checked_out = Column(Boolean, default=False, nullable=False)
    booking = relationship('Booking', backref='reservation', lazy=True)
    bill = relationship('Bill', backref='reservation', uselist=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)



class Comment(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String(255), nullable=False)
    room_type_id = Column(Integer, ForeignKey(RoomType.id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now)

    def __str__(self):
        return self.content

class Bill(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    reservation_id = Column(Integer, ForeignKey(Reservation.id), unique=True, nullable=False)  # Quan hệ 1-1
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    total_amount = Column(Float, nullable=False, default=0.0)
    staff_name = Column(String(100), nullable=True)  # Tên nhân viên
    is_paid = Column(Boolean, default=False, nullable=False)  # Trạng thái thanh toán



class Booking(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    reservation_id = Column(Integer, ForeignKey(Reservation.id), nullable=False)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)
    customer = relationship('Customer', backref='booking', lazy=True)
    expense = Column(Float, nullable=False, default=0.0)




class CustomerType(RoleEnum):
    DOMESTIC = "Nội địa"
    INTERNATIONAL = "Quốc tế"

class Customer(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    id_card = Column(db.String(20), nullable=False, unique=False)
    customer_type = Column(Enum(CustomerType), nullable=False)  # Sử dụng Enum
    address = Column(db.String(255), nullable=False)
    booking_id = Column(Integer, ForeignKey(Booking.id), nullable=False)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        import hashlib
        v = User(name='staff', username='staff', email='staff123@gmail.com', password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
                 user_role=UserRole.STAFF)
        db.session.add(v)
        u = User(name='admin', username='admin', email='admin123@gmail.com', password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
                 user_role=UserRole.ADMIN)
        db.session.add(u)


        rt1 = RoomType(name = "Double Bedroom", price=1000000, max_guests = 3, proportion=0.25, coefficient=1.5, image="images/room_type1.jpg")
        rt2 = RoomType(name = "Quad room", price=2000000, max_guests = 5, proportion=0.25, coefficient=1.5, image="images/room_type2.jpg")

        r1 = Room(name="Phòng 101", roomtype=rt1)
        r2 = Room(name="Phòng 102", roomtype=rt1)
        r3 = Room(name="Phòng 103", roomtype=rt2)
        r4 = Room(name="Phòng 104", roomtype=rt2)



        db.session.add_all([r1, r2, r3, r4, rt1, rt2])
        db.session.commit()
