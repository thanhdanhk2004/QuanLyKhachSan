from datetime import datetime

from flask_login import current_user
from sqlalchemy import false, or_, func
from flask import abort
from app.models import User, Room, Booking, Customer, Reservation, Bill, RoomType, Comment, User_Customer, RoleEnum, \
    UserRole
import hashlib
from app import app, db, mail
import cloudinary.uploader
from sqlalchemy.sql import extract
from flask_mail import Message
from twilio.rest import Client


def get_user_by_id(id):
    return User.query.get(id)

def auth_user(username, password, role=None):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    u = User.query.filter(User.username.__eq__(username.strip()),
                          User.password.__eq__(password))
    if role:
        u = u.filter(User.user_role.__eq__(role))

    return u.first()
def load_rooms():
    query = RoomType.query

    return query.all()

def add_user(name,username,email, password, phone, avatar=None):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    u = User_Customer(name=name, username=username,email=email , password=password, phone=phone)

    if avatar:
        res = cloudinary.uploader.upload(avatar)
        u.avatar = res.get('secure_url')

    db.session.add(u)
    db.session.commit()


def get_room_by_id(room_id):
    return Room.query.get(room_id)


def add_booking(room, reservation):
    b = Booking(room=room, reservation=reservation)
    db.session.add(b)
    db.session.commit()
    return b


def add_reservation(user, customer_name,contact_phone, checkin_date, checkout_date, is_checked_in=false()):
    r = Reservation(user=user, customer_name=customer_name, contact_phone=contact_phone,checkin_date=checkin_date,checkout_date=checkout_date, is_checked_in=is_checked_in)
    db.session.add(r)
    db.session.commit()
    return r

def add_bill(reservation,total_amount):
    b = Bill(reservation=reservation,total_amount=total_amount)
    db.session.add(b)
    db.session.commit()


def load_reservation(search_query=None, reservation_code=None, page=1):
    r = Reservation.query

    # Tìm kiếm theo tên khách hàng hoặc mã đặt phòng
    if search_query:
        r = r.filter(
            Reservation.customer_name.contains(search_query),
            Reservation.is_checked_in == 0
        )

    if reservation_code:
        r = r.filter(
            Reservation.reservation_code.contains(reservation_code),
            Reservation.is_checked_in == 0
        )

    # Lọc theo trạng thái chưa check-in
    r = r.filter(Reservation.is_checked_in == 0)

    r = r.order_by(Reservation.checkin_date)
    # Phân trang
    page_size = app.config["PAGE_SIZE"]
    start = (page - 1) * page_size
    r = r.slice(start, start + page_size)

    return r.all()


def load_ticket(user_id, is_checked_in=None, is_checked_out=None, page=1):
    r = Reservation.query.filter(Reservation.user_id == user_id)


    if is_checked_in is not None:
        r = r.filter(Reservation.is_checked_in == is_checked_in)

    if is_checked_out is not None:
        r = r.filter(Reservation.is_checked_out == is_checked_out)

    # Phân trang
    page_size = app.config["PAGE_SIZE"]
    start = (page - 1) * page_size
    r = r.offset(start).limit(page_size)

    return r.all()

def load_checkout(search_query=None, page=1):
    r = Reservation.query
    if search_query:
        r = r.filter(
            Reservation.customer_name.contains(search_query),
            Reservation.is_checked_in == 1,
            Reservation.is_checked_out == 0
            )
    else:
        r = r.filter(Reservation.is_checked_in == 1,
                     Reservation.is_checked_out == 0
                     )

    r = r.order_by(Reservation.checkout_date)

    page_size = app.config["PAGE_SIZE"]
    start = (page - 1) * page_size
    r = r.slice(start, start + page_size)

    return r.all()


def count_checkout(search_query=None):
    r = Reservation.query
    if search_query:
        r = r.filter(
            Reservation.customer_name.contains(search_query),
            Reservation.is_checked_in == 1,
            Reservation.is_checked_out == 0
        )
    else:
        r = r.filter(Reservation.is_checked_in == 1,
                     Reservation.is_checked_out == 0
                     )

    return r.count()


def count_reservation(search_query=None, reservation_code=None):
    r = Reservation.query

    if search_query:
        r = r.filter(
            Reservation.customer_name.contains(search_query),
            Reservation.is_checked_in == 0
        )

    if reservation_code:
        r = r.filter(
            Reservation.reservation_code.contains(reservation_code),
            Reservation.is_checked_in == 0
        )

    # Đếm tổng số kết quả
    return r.count()


def add_customer(booking, name, id_card, customer_type, address):
    c = Customer(booking=booking, name=name, id_card=id_card, address=address, customer_type=customer_type)

    db.session.add(c)
    db.session.commit()


def calculate_expense(booking):
    price_per_day = booking.room.roomtype.price  # Giá mỗi ngày của phòng
    proportion = booking.room.roomtype.proportion  # Tỷ lệ phụ thu nếu số khách đạt tối đa
    coefficient = booking.room.roomtype.coefficient  # Hệ số phụ thu cho khách quốc tế
    surcharge = 1.0  # Phụ thu (nếu cần thêm logic sau này)
    max_guests = booking.room.roomtype.max_guests

    stay_duration = (booking.reservation.checkout_date - booking.reservation.checkin_date).days + 1


    price = price_per_day * stay_duration

    # Kiểm tra loại khách và điều chỉnh giá
    for customer in booking.customer:
        if customer.customer_type.value == 'Quốc tế':
            price *= coefficient
            break

    if len(booking.customer) >= max_guests:
        price += price * proportion

    # Cập nhật chi phí cho booking
    booking.expense = price
    db.session.commit()

    return price

def is_accessible(user_role, required_role):
    return user_role == required_role

def find_available_rooms(checkin_date, checkout_date, room_type=None):
    query = Room.query

    # Nếu có loại phòng, lọc theo loại phòng
    if room_type:
        query = query.filter(Room.roomtype.has(name=room_type))

    available_rooms = []

    # Truy vấn tất cả các phòng không bị đặt trong khoảng thời gian
    rooms = query.all()
    for room in rooms:
        is_available = True
        for booking in room.booking:
            reservation = booking.reservation  # Lấy Reservation liên kết với Booking
            # Kiểm tra xem phòng đã được đặt trong khoảng thời gian yêu cầu chưa
            if (checkin_date < reservation.checkout_date and checkout_date > reservation.checkin_date):
                is_available = False
                break

        if is_available:
            available_rooms.append(room)

    return available_rooms

def get_room_type_by_id(room_type_id):
    return RoomType.query.get(room_type_id)

def add_comment(content, room_type_id):
    c = Comment(content=content, room_type_id=room_type_id, user=current_user)

    db.session.add(c)
    db.session.commit()

    return c

def get_comments(room_type_id, page=1):
    page_size = app.config["PAGE_SIZE"]
    start = (page - 1) * page_size

    return Comment.query.filter(Comment.room_type_id.__eq__(room_type_id)).order_by(-Comment.id).slice(start, start + page_size).all()

def count_comment(room_type_id):
    return Comment.query.filter(Comment.room_type_id.__eq__(room_type_id)).count()


def update_annual_spending(user_id, amount):
    # Truy vấn từ bảng User_Customer
    user = User_Customer.query.get(user_id)
    if not user:
        raise ValueError("User_Customer with the given ID does not exist.")

    current_year = datetime.now().year

    # Nếu năm hiện tại khác với last_updated_year, reset annual_spending
    if user.last_updated_year != current_year:
        user.annual_spending = 0.0
        user.last_updated_year = current_year

    # Cộng dồn tổng chi tiêu
    user.annual_spending += amount
    db.session.commit()


def roomType_stats():
    return db.session.query(RoomType.id, RoomType.name, func.count(Room.id))\
        .join(Room, RoomType.id.__eq__(Room.roomtype_id), isouter=True)\
        .group_by(RoomType.id, RoomType.name).all()

def room_stats(kw=None, from_date=None, to_date=None):
    query = db.session.query(
        RoomType.id,
        RoomType.name,
        func.sum(
            func.greatest(
                func.datediff(func.least(Reservation.checkout_date, to_date), func.greatest(Reservation.checkin_date, from_date)),
                0
            )
        ).label('total_days')
    ).join(Room, RoomType.id == Room.roomtype_id)\
     .join(Booking, Room.id == Booking.room_id)\
     .join(Reservation, Booking.reservation_id == Reservation.id)

    if kw:
        query = query.filter(RoomType.name.contains(kw))

    # Lọc theo thời gian nếu có
    if from_date and to_date:
        query = query.filter(
            Reservation.checkin_date <= to_date,
            Reservation.checkout_date >= from_date  # Ngày check-out phải lớn hơn hoặc bằng from_date
        )
    elif from_date:
        query = query.filter(Reservation.checkout_date >= from_date)
    elif to_date:
        query = query.filter(Reservation.checkin_date <= to_date)

    if not from_date and not to_date:
        # Không lọc, lấy tất cả dữ liệu
        query = query

    query = query.group_by(RoomType.id, RoomType.name)

    return query.all()



def revenue_time(year):
    return db.session.query(extract('month', Bill.created_at), func.sum(Bill.total_amount))\
        .filter(extract('year', Bill.created_at) == year, Bill.is_paid == True)\
        .group_by(extract('month', Bill.created_at))\
        .order_by(extract('month', Bill.created_at)).all()

def send_email(subject, recipients, body):
    try:
        msg = Message(subject=subject, recipients=recipients, body=body)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Lỗi khi gửi email: {e}")
        return False


def get_discount_by_customer_type(customer_type):
    discount_map = {
        "VVIP": 15,
        "VIP": 10,
        "NORMAL": 3,
        "NEW": 5
    }
    return discount_map.get(customer_type)


def check_access_for_staff():

    if not (current_user.is_authenticated and current_user.user_role == UserRole.STAFF):
        abort(403, description="Bạn không có quyền truy cập trang này.")


def send_booking_confirmation(customer_name,phone_number, room_len, price, checkin_date, checkout_date):

    account_sid = 'AC7f09d332a643ab5d7633b0154438cbd5'
    auth_token = '1945c4c802cf1b9f7752338429b70425'


    client = Client(account_sid, auth_token)


    from_number = '+12185494406'


    message_body = f"Xin chào {customer_name} Bạn đã đặt {room_len} phòng tại T&T Hotel. Ngày nhận phòng: {checkin_date}, Ngày trả phòng: {checkout_date} với giá {price} VND. Chúc bạn có một kỳ nghỉ tuyệt vời tại T&T Hotel!"

    # Gửi SMS
    message = client.messages.create(
        body=message_body,
        from_=from_number,
        to=phone_number
    )

    print(f"Message sent: {message.sid}")