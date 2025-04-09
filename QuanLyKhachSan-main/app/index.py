from os import rename
import math
from flask import render_template, request, redirect, Request, jsonify, session, Blueprint, make_response, current_app, abort
import dao
from app import app, login, db
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime, timedelta
from app.models import Booking, Room, UserRole, Reservation, Bill, RoomType, User, User_Customer, Comment
from xhtml2pdf import pisa
import io
from twilio.rest import Client



staff_bp = Blueprint('staff', __name__, url_prefix='/staff')
@staff_bp.route('/')
def dashboard():
    if current_user.is_authenticated and current_user.user_role != UserRole.STAFF:
        abort(403, description="Bạn không có quyền truy cập trang này.")
    rooms = Room.query.all()
    return render_template('staff/index.html', rooms=rooms)



@app.route('/generate_bill/<int:bill_id>')
def generate_bill(bill_id):
    bill = db.session.get(Bill, bill_id)

    if not bill:
        return "Bill not found", 404

    reservation = bill.reservation
    bookings = reservation.booking


    data = {
        "hotel_name": "T&T Hotel",
        "bill_id": bill.id,
        "created_at": bill.created_at.strftime('%d-%m-%Y %H:%M:%S'),
        "total_amount": "{:,.2f}".format(bill.total_amount),
        "is_paid": "Da thanh toan" if bill.is_paid else "chua thanh toán",
        "staff_name": bill.staff_name,
        "customer_name": reservation.customer_name,
        "contact_phone": reservation.contact_phone,
        "checkin_date": reservation.checkin_date.strftime('%d-%m-%Y %H:%M:%S'),
        "checkout_date": reservation.checkout_date.strftime('%d-%m-%Y %H:%M:%S'),
        "bookings": [{
            "room_name": b.room.name,
            "expense": "{:,.2f}".format(b.expense)
        } for b in bookings]
    }


    html = render_template('staff/bill_template.html', data=data)


    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        src=html, dest=pdf_buffer
    )

    if pisa_status.err:
        return f"Error while creating PDF: {pisa_status.err}", 500


    pdf_buffer.seek(0)

    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=bill_{bill.id}.pdf'

    return response



@staff_bp.route('/logout_staff')
def logout_staff_process():
    logout_user()
    session.clear()
    return redirect('/staff')


@staff_bp.route('/checkin', methods=['GET'])
def checkin():
    dao.check_access_for_staff()
    current_time = datetime.now()

    search_query = request.args.get('search')
    reservation_code = request.args.get('reservation_code')  # Mã đặt phòng

    page = request.args.get('page', 1)

    # Load các đặt phòng theo các tham số tìm kiếm
    reservation = dao.load_reservation(search_query=search_query, reservation_code=reservation_code, page=int(page))

    total = dao.count_reservation(search_query=search_query,
                                  reservation_code=reservation_code)  # Cập nhật đếm theo điều kiện tìm kiếm
    page_size = app.config["PAGE_SIZE"]
    pages = math.ceil(total / page_size)

    # Trả về giao diện với dữ liệu đã phân trang
    return render_template('staff/checkin.html', reservation=reservation, pages=pages, search_query=search_query,
                           reservation_code=reservation_code, current_time=current_time)


@staff_bp.route('/rent')
def make_rental():
    dao.check_access_for_staff()
    room_types = RoomType.query.all()
    return render_template('staff/rent.html', room_types=room_types)

@staff_bp.route('/staff_booking',  methods=['get', 'post'])
def booking_by_staff():
    dao.check_access_for_staff()
    room_types = RoomType.query.all()
    return render_template('staff/booking.html', room_types=room_types)


@staff_bp.route('/checkout',methods=['GET'])
def checkout():
    dao.check_access_for_staff()
    search_query = request.args.get('search')
    reservation_code = request.args.get('reservation_code')

    page = request.args.get('page', 1)
    rent = dao.load_checkout(search_query, page=int(page))

    total = dao.count_checkout(search_query)  # Hàm đếm số lượng booking thỏa mãn tìm kiếm
    page_size = app.config["PAGE_SIZE"]
    pages = math.ceil(total / page_size)  # Tính tổng số trang

    # Trả về giao diện với dữ liệu đã phân trang
    return render_template('staff/checkout.html', rent=rent, pages=pages, search_query=search_query)


@staff_bp.route('/checkin/<int:reservation_id>', methods=['POST'])
def check_in(reservation_id):

    reservation = Reservation.query.get_or_404(reservation_id)

    reservation.is_checked_in = True
    for booking in reservation.booking:  # Giả sử reservation.booking chứa danh sách các phòng đã đặt
        room = Room.query.get(booking.room_id)  # Lấy thông tin phòng từ booking
        if room:
            room.is_available= False

    db.session.commit()

    return jsonify({'success': True})

@staff_bp.route('/checkout/<int:reservation_id>', methods=['POST'])
def check_out(reservation_id):
    # Lấy reservation từ cơ sở dữ liệu
    reservation = Reservation.query.get_or_404(reservation_id)

    # Cập nhật trạng thái checkout
    reservation.is_checked_out = True
    for booking in reservation.booking:
        room = Room.query.get(booking.room_id)
        if room:
            room.is_available = True
    current_time = datetime.now()
    if reservation.checkout_date != current_time:
        reservation.checkout_date = current_time
    # Lưu thay đổi vào cơ sở dữ liệu
    db.session.commit()

    # Trả về phản hồi dưới dạng JSON
    return jsonify({"success": True})


@staff_bp.route('/pay_bill/<int:bill_id>', methods=['POST'])
def pay_bill(bill_id):
    bill = Bill.query.get_or_404(bill_id)

    bill.is_paid = True
    bill.staff_name = current_user.username
    bill.created_at = datetime.now()

    used_id = bill.reservation.user_id
    user = User.query.get(used_id)
    if isinstance(user, User_Customer):
        dao.update_annual_spending(user_id=used_id, amount=bill.total_amount)
        if user.annual_spending >= 50000000:
            user.customer_tier="VVIP"
        elif user.annual_spending >= 25000000:
            user.customer_tier = "VIP"
        elif user.annual_spending >= 0:
            user.customer_tier = "NORMAL"

    db.session.commit()
    return jsonify({"success": True})



@app.route("/")
def index():
    room = dao.load_rooms()

    return render_template('index.html', RoomType=room)

@app.route('/login', methods=['get', 'post'])
def login_process():
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.auth_user(username=username, password=password)
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.user_role.value
            login_user(user)
            return redirect('/')

    return render_template('login.html')

@app.route('/login-admin', methods=['post'])
def login_admin_process():
    username = request.form.get('username')
    password = request.form.get('password')
    user = dao.auth_user(username=username, password=password, role=UserRole.ADMIN)
    if user:
        login_user(user)

    return redirect('/admin')

@app.route('/login-staff', methods=['post'])
def login_staff_process():
    username = request.form.get('username')
    password = request.form.get('password')
    user = dao.auth_user(username=username, password=password, role=UserRole.STAFF)
    if user:
        login_user(user)

    return redirect('/staff')


@app.route('/room_type/<int:room_type_id>')
def room_detail(room_type_id):
    room_type = dao.get_room_type_by_id(room_type_id)
    comments = dao.get_comments(room_type_id=room_type_id, page=int(request.args.get('page', 1)))

    return render_template('details.html', comments=comments, room_type=room_type,
                           pages=math.ceil(dao.count_comment(room_type_id=room_type_id)/app.config["COMMENT_SIZE"]))

@app.route('/logout')
def logout_process():
    logout_user()
    session.clear()
    return redirect('/login')


@login.user_loader
def get_user_by_id(user_id):
    return dao.get_user_by_id(user_id)


@app.route('/register', methods=['get', 'post'])
def register_process():
    err_msg = ''
    if request.method.__eq__("POST"):
        # email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if password.__eq__(confirm):
            data = request.form.copy()
            del data['confirm']

            dao.add_user(avatar=request.files.get('avatar'), **data)

            return redirect('/login')
        else:
            err_msg = 'Mật khẩu không khớp!'

    return render_template('register.html', err_msg=err_msg)

@app.route('/booking', methods=['get'])
def booking():
    room_types = RoomType.query.all()
    return render_template('booking.html', room_types=room_types)


@app.route('/member', methods=['get'])
def member_cus():
    user = current_user

    return render_template('member.html', user=user)

@app.route('/api/search', methods=['POST'])
def search_rooms():
    data = request.get_json()
    checkin_date = data.get('checkin_date')
    checkout_date = data.get('checkout_date')
    room_type = data.get('room_type')

    try:
        checkin_date = datetime.strptime(checkin_date, '%Y-%m-%d')
        checkout_date = datetime.strptime(checkout_date, '%Y-%m-%d')
        checkin_date = checkin_date.replace(hour=14, minute=0, second=0, microsecond=0)
        checkout_date = checkout_date.replace(hour=12, minute=0, second=0, microsecond=0)
    except ValueError:
        return jsonify({"error": "Ngày bạn nhập không hợp lệ!"})

    max_checkin_date = datetime.today() + timedelta(days=28)
    if checkin_date > max_checkin_date:
        return jsonify({"error": f"Ngày nhận phòng không được quá {max_checkin_date.strftime('%d-%m-%Y')}!"})

    if checkout_date <= checkin_date:
        return jsonify({"error": "Ngày trả phòng phải sau ngày nhận phòng!"})

    if checkin_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
        return jsonify({"error": "Ngày nhận phòng phải tối thiểu từ ngày hôm nay!"})

    available_rooms = dao.find_available_rooms(checkin_date, checkout_date,room_type)

    return jsonify({
        "available_rooms": [{
            "id": room.id,
            "name": room.name,
            "price": room.roomtype.price,
            "typename": room.roomtype.name,
            "max_guests": room.roomtype.max_guests
        } for room in available_rooms]
    })



@app.route('/api/confirm', methods=['POST'])
@login_required
def booking_cf():
    data = request.get_json()
    checkin_date = datetime.strptime(data['checkinDate'], '%Y-%m-%d')
    checkout_date = datetime.strptime(data['checkoutDate'], '%Y-%m-%d')
    checkin_date = checkin_date.replace(hour=14, minute=0, second=0, microsecond=0)
    checkout_date = checkout_date.replace(hour=12, minute=0, second=0, microsecond=0)
    user = current_user
    customer_name = user.name
    contact_phone = user.phone
    customer_tier = user.customer_tier
    discount = dao.get_discount_by_customer_type(customer_tier)
    reservation = dao.add_reservation(user=user,customer_name=customer_name,contact_phone=contact_phone, checkin_date=checkin_date, checkout_date=checkout_date, is_checked_in=False)
    rooms = data['rooms']
      # Duyệt qua các phòng đã chọn
    for room_data in rooms:
        room_id = room_data['roomId']
        num_guests = room_data['numGuests']
        room = dao.get_room_by_id(room_id)
        booking = dao.add_booking(room=room, reservation=reservation)
        for guest_data in room_data['guests']:
            guest_name = guest_data['name']
            guest_idcard = guest_data['idCard']
            guest_address = guest_data['address']
            guest_type = guest_data['type']
            dao.add_customer(booking=booking,name=guest_name,id_card=guest_idcard, customer_type=guest_type,address=guest_address)
        dao.calculate_expense(booking)
    total_amount = sum(booking.expense for booking in reservation.booking)
    total_amount_after = total_amount / 100 * (100-discount)
    dao.add_bill(reservation=reservation, total_amount=total_amount_after)

    email_subject = "Xác nhận đặt phòng - T&T Hotel"
    email_recipients = [user.email]  # Email khách hàng
    email_body = f"""
       Kính chào {customer_name},

       Cảm ơn quý khách đã đặt phòng tại T&T Hotel. Dưới đây là thông tin chi tiết đặt phòng của quý khách:
       - Mã đặt phòng: { reservation.reservation_code }
       - Ngày nhận phòng: {checkin_date.strftime('%d-%m-%Y %H:%M')}
       - Ngày trả phòng: {checkout_date.strftime('%d-%m-%Y %H:%M')}
       - Số phòng: {len(rooms)}
       - Ưu đãi thành viên : -{discount}%. 
       - Tổng tiền: {total_amount_after:,.2f} VND
        
       Trân trọng,
       Đội ngũ T&T Hotel
       """
    dao.send_email(email_subject, email_recipients, email_body)
    if customer_tier == 'NEW':
        user.customer_tier = 'NORMAL'
    db.session.commit()

    return jsonify({'success': True})

@app.route('/api/rent_cf', methods=['POST'])
def renting_cf():
    data = request.get_json()
    is_checked_in = True
    total_amount = 0.0
    checkin_date = datetime.strptime(data['checkinDate'], '%Y-%m-%d')
    checkout_date = datetime.strptime(data['checkoutDate'], '%Y-%m-%d')
    checkin_date = checkin_date.replace(hour=14, minute=0, second=0, microsecond=0)
    checkout_date = checkout_date.replace(hour=12, minute=0, second=0, microsecond=0)
    customer_name = data['customerName']
    contact_phone = data['contactPhone']
    reservation = dao.add_reservation(user=current_user, customer_name=customer_name,contact_phone=contact_phone, checkin_date=checkin_date,
                                      checkout_date=checkout_date, is_checked_in=is_checked_in)
    rooms = data['rooms']
    # Duyệt qua các phòng đã chọn
    for room_data in rooms:
        room_id = room_data['roomId']
        num_guests = room_data['numGuests']
        room = dao.get_room_by_id(room_id)
        room.is_available = False
        booking = dao.add_booking(room=room, reservation=reservation)

        for guest_data in room_data['guests']:
            guest_name = guest_data['name']
            guest_idcard = guest_data['idCard']
            guest_address = guest_data['address']
            guest_type = guest_data['type']
            dao.add_customer(booking=booking,name=guest_name,id_card=guest_idcard, customer_type=guest_type,address=guest_address)
        expense = dao.calculate_expense(booking)
        total_amount = total_amount + expense

    dao.add_bill(reservation=reservation, total_amount=total_amount)
    db.session.commit()

    return jsonify({'success': True})


@app.route('/api/staff_cf', methods=['POST'])
def staffbook_cf():
    data = request.get_json()
    is_checked_in = False
    total_amount = 0.0
    checkin_date = datetime.strptime(data['checkinDate'], '%Y-%m-%d')
    checkout_date = datetime.strptime(data['checkoutDate'], '%Y-%m-%d')
    checkin_date = checkin_date.replace(hour=14, minute=0, second=0, microsecond=0)
    checkout_date = checkout_date.replace(hour=12, minute=0, second=0, microsecond=0)
    customer_name = data['customerName']
    contact_phone = data['contactPhone']
    reservation = dao.add_reservation(user=current_user, customer_name=customer_name,contact_phone=contact_phone, checkin_date=checkin_date,
                                      checkout_date=checkout_date, is_checked_in=is_checked_in)
    rooms = data['rooms']
    # Duyệt qua các phòng đã chọn
    for room_data in rooms:
        room_id = room_data['roomId']
        num_guests = room_data['numGuests']
        room = dao.get_room_by_id(room_id)
        booking = dao.add_booking(room=room, reservation=reservation)

        for guest_data in room_data['guests']:
            guest_name = guest_data['name']
            guest_idcard = guest_data['idCard']
            guest_address = guest_data['address']
            guest_type = guest_data['type']
            dao.add_customer(booking=booking,name=guest_name,id_card=guest_idcard, customer_type=guest_type,address=guest_address)
        expense = dao.calculate_expense(booking)
        total_amount = total_amount + expense
    dao.send_booking_confirmation(customer_name=customer_name,phone_number=contact_phone,room_len=len(rooms), price=total_amount, checkin_date=checkin_date, checkout_date=checkout_date)
    dao.add_bill(reservation=reservation, total_amount=total_amount)
    db.session.commit()

    return jsonify({'success': True})

@app.route('/ticket', methods=['GET'])
def get_ticket():
    user_id = current_user.id
    status = request.args.get('status')  # Lấy giá trị status từ URL nếu có

    # Lọc phiếu đặt phòng theo tình trạng (nếu có status)
    if status == 'not_checked_in':
        reservation = dao.load_ticket(user_id=user_id, is_checked_in=False, page=1)
    elif status == 'checked_in':
        reservation = dao.load_ticket(user_id=user_id, is_checked_in=True, page=1)
    elif status == 'checked_out':
        reservation = dao.load_ticket(user_id=user_id, is_checked_out=True, page=1)
    else:
        # Trả về tất cả các phiếu nếu không có filter status
        reservation = dao.load_ticket(user_id=user_id, page=1)

    return render_template('ticket.html', reservation=reservation)


@app.route('/api/comments', methods=['POST'])
@login_required
def add_comment():
    data = request.json
    content = data.get('content')
    room_type_id = data.get('room_type_id')

    try:
        c = dao.add_comment(content=content, room_type_id=room_type_id)
    except:
        return {'status': 404, 'err_msg': 'loiloiloi!!!!'}

    return {'status': 201, 'comment': {
        'id': c.id,
        'content': c.content,
        'created_date': c.created_date,
        'user': {
            'username': current_user.username,
            'avatar': current_user.avatar
        }
    }}


if __name__ == "__main__":
    app.register_blueprint(staff_bp)
    from app import admin
    app.run(debug=True)