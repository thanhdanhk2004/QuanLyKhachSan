function search_room(){
    event.preventDefault();
    const checkinDate = document.getElementById('checkin_date').value;
    const checkoutDate = document.getElementById('checkout_date').value;
    const room_type =  document.getElementById('room_type_name').value;

    fetch('/api/search', {
        method: 'POST',
        body: JSON.stringify({
            'checkin_date': checkinDate,
            'checkout_date': checkoutDate,
            'room_type': room_type
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
     .then(response => response.json())
     .then(data => {
        if (data.error) {
    // Thông báo lỗi khi có lỗi từ server
    Swal.fire({
        title: 'Lỗi!',
        text: data.error,
        icon: 'error',
        confirmButtonText: 'Chọn ngày khác',
        customClass: {
            confirmButton: 'btn btn-danger'  // Tùy chỉnh giao diện nút "OK"
        }
    });
}else {
            displayAvailableRooms(data.available_rooms);  // Hiển thị các phòng có sẵn
        }
    })
}


function displayAvailableRooms(rooms) {
    const container = document.getElementById('available-rooms-container');
    const roomList = document.getElementById('room-list');
    const noRoom = document.getElementById('no-room');
    roomList.innerHTML = ''; // Xóa nội dung cũ

    if (rooms.length === 0) {
        noRoom.style.display = 'block';
        container.style.display = 'none';
    roomList.style.display = 'none';
    } else {
        rooms.forEach((room) => {
            const li = document.createElement('li');
            li.classList.add('list-group-item');
            li.innerHTML = `
                <div class="form-check mb-3">
    <input class="form-check-input" type="checkbox" value="${room.id}" id="room-${room.id}" name="rooms" onchange="toggleRoomSelection(${room.id})">
    <label class="form-check-label d-flex justify-content-between align-items-center w-100" for="room-${room.id}">
    <div class="d-flex justify-content-between w-100">
    <span class="fw-bold text-dark">${room.name}</span>
    <span class="fw-bold text-dark">${room.typename}</span>
    <span class="fw-bold text-danger">${room.price} VNĐ/đêm</span>
</div>

</label>



</div>
   <div id="guests-form-${room.id}" class="guests-form mt-3" style="display:none;">
        <label for="num_guests-${room.id}" class="form-label">Số lượng khách:</label>
        <input type="number" id="num_guests-${room.id}" name="num_guests-${room.id}" min="1" max="${room.max_guests}" class="form-control" placeholder="Sức chứa tối đa ${ room.max_guests } người" onchange="updateGuestForm(${room.id})">
        <div id="guests-list-${room.id}" class="mt-2"></div>
    </div>
</div>


            `;
            roomList.appendChild(li);
        });
    noRoom.style.display = 'none';
    container.style.display = 'block';
    roomList.style.display = 'block';
    }


}


function toggleRoomSelection(roomId) {
        const numGuestsField = document.getElementById('num_guests-' + roomId);
        const guestsForm = document.getElementById('guests-form-' + roomId);

        // Hiển thị form nhập số lượng khách nếu phòng được chọn
        if (document.getElementById('room-' + roomId).checked) {
            guestsForm.style.display = 'block';
        } else {
            guestsForm.style.display = 'none';
        }
    }

function updateGuestForm(roomId) {
        const numGuests = document.getElementById('num_guests-' + roomId).value;
        const guestsList = document.getElementById('guests-list-' + roomId);

        guestsList.innerHTML = '';
        for (let i = 0; i < numGuests; i++) {
            const guestForm = document.createElement('div');
            guestForm.classList.add('guest-form');
            guestForm.innerHTML = `
    <div class="row g-3">
        <!-- Tên khách -->
        <div class="col-md-3">
            <label for="guest-name-${roomId}-${i}" class="form-label">Tên khách ${i + 1}:</label>
            <input type="text" id="guest-name-${roomId}-${i}" name="guest-name-${roomId}-${i}" class="form-control"  required>
        </div>

        <!-- CMND/CCCD -->
        <div class="col-md-3">
            <label for="guest-idcard-${roomId}-${i}" class="form-label">CMND/CCCD khách ${i + 1}:</label>
            <input type="text" id="guest-idcard-${roomId}-${i}" name="guest-idcard-${roomId}-${i}" class="form-control" required>
        </div>

        <!-- Địa chỉ -->
        <div class="col-md-3">
            <label for="guest-address-${roomId}-${i}" class="form-label">Địa chỉ:</label>
            <input type="text" id="guest-address-${roomId}-${i}" name="guest-address-${roomId}-${i}" class="form-control" required>
        </div>

        <!-- Loại khách -->
        <div class="col-md-3">
            <label for="guest-type-${roomId}-${i}" class="form-label">Loại khách:</label>
            <select id="guest-type-${roomId}-${i}" name="guest-type-${roomId}-${i}" class="form-select" required>
                <option value="domestic">Nội địa</option>
                <option value="international">Quốc tế</option>
            </select>
        </div>
    </div>
`;

            guestsList.appendChild(guestForm);
        }
    }

function checkRoomSelectionBook(event) {
    // Ngừng hành động submit mặc định
    event.preventDefault();

    const rooms = document.querySelectorAll('input[name="rooms"]:checked');
    if (rooms.length === 0) {
        alert('Vui lòng chọn ít nhất một phòng!');
        return false;
    }

    // Kiểm tra thông tin khách hàng cho từng phòng
    let roomData = [];


    for (let room of rooms) {
        const roomId = room.value;
        const numGuests = document.getElementById('num_guests-' + roomId).value;
        let guests = [];

        // Kiểm tra từng khách trong phòng
        for (let i = 0; i < numGuests; i++) {
            const guestName = document.getElementById('guest-name-' + roomId + '-' + i).value;
            const guestIdCard = document.getElementById('guest-idcard-' + roomId + '-' + i).value;
            const guestAddress = document.getElementById('guest-address-' + roomId + '-' + i).value;
            const guestType = document.getElementById('guest-type-' + roomId + '-' + i).value;

            if (!guestName || !guestIdCard || !guestAddress || !guestType) {
                alert('Vui lòng điền đầy đủ thông tin cho khách hàng!');
                return false;
            }

            // Thêm khách vào danh sách
            guests.push({
                name: guestName,
                idCard: guestIdCard,
                address: guestAddress,
                type: guestType
            });
        }

        // Thêm phòng vào dữ liệu gửi
        roomData.push({
            roomId: roomId,
            numGuests: numGuests,
            guests: guests
        });
    }

    // Gửi dữ liệu đã chọn đến server
    const formData = {
        checkinDate: document.getElementById('checkin_date').value,
        checkoutDate: document.getElementById('checkout_date').value,
        rooms: roomData
    };

    // Hiển thị vòng quay loading
    Swal.fire({
        title: 'Đang xử lý...',
        text: 'Vui lòng đợi trong khi chúng tôi hoàn tất đặt phòng.',
        icon: 'info',
        showConfirmButton: false,
        didOpen: () => {
            Swal.showLoading();  // Hiển thị vòng quay loading
        }
    });

    // Gửi yêu cầu đặt phòng
    fetch('/api/confirm', {
        method: 'POST',
        body: JSON.stringify(formData),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Đóng thông báo loading
        Swal.close();

        if (data.success) {
            Swal.fire({
                title: 'Đặt phòng thành công!',
                text: 'Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi.',
                icon: 'success',
                confirmButtonText: 'Đồng ý'
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = '/booking';  // Chuyển hướng sau khi thành công
                }
            });
        } else {
            alert('Có lỗi 1 xảy ra trong quá trình đặt phòng!');
        }
    })
    .catch(error => {
        // Đóng thông báo loading và hiển thị lỗi nếu có
        Swal.close();
        alert('Có lỗi 2 xảy ra trong quá trình đặt phòng!');
    });

    return false;  // Ngừng hành động submit mặc định
}


function checkRoomSelectionRent(event) {
    // Ngừng hành động submit mặc định
    event.preventDefault();

    const rooms = document.querySelectorAll('input[name="rooms"]:checked');
    if (rooms.length === 0) {
        alert('Vui lòng chọn ít nhất một phòng!');
        return false;
    }

    // Kiểm tra thông tin khách hàng cho từng phòng
    let roomData = [];
    const customerName = document.getElementById('customer_name').value;
    const contactPhone = document.getElementById('contact_phone').value;
    if (!customerName) {
        alert('Vui lòng nhập tên khách hàng đặt phòng!');
        return false;
    }
    if (!contactPhone) {
        alert('Vui lòng nhập số điện thoại liên lạc!');
        return false;
    }
    for (let room of rooms) {
        const roomId = room.value;
        const numGuests = document.getElementById('num_guests-' + roomId).value;
        let guests = [];

        // Kiểm tra từng khách trong phòng
        for (let i = 0; i < numGuests; i++) {
            const guestName = document.getElementById('guest-name-' + roomId + '-' + i).value;
            const guestIdCard = document.getElementById('guest-idcard-' + roomId + '-' + i).value;
            const guestAddress = document.getElementById('guest-address-' + roomId + '-' + i).value;
            const guestType = document.getElementById('guest-type-' + roomId + '-' + i).value;

            if (!guestName || !guestIdCard || !guestAddress || !guestType) {
                alert('Vui lòng điền đầy đủ thông tin cho khách hàng!');
                return false;
            }

            // Thêm khách vào danh sách
            guests.push({
                name: guestName,
                idCard: guestIdCard,
                address: guestAddress,
                type: guestType
            });
        }

        // Thêm phòng vào dữ liệu gửi
        roomData.push({
            roomId: roomId,
            numGuests: numGuests,
            guests: guests
        });
    }

    // Gửi dữ liệu đã chọn đến server
    const formData = {
        customerName: customerName,
        contactPhone: contactPhone,
        checkinDate: document.getElementById('checkin_date').value,
        checkoutDate: document.getElementById('checkout_date').value,
        rooms: roomData
    };

    // Gửi yêu cầu đặt phòng
    fetch('/api/rent_cf', {
        method: 'POST',
        body: JSON.stringify(formData),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
    Swal.fire({
        title: 'Thuê phòng thành công!',
        text: 'Chúc bạn một ngày làm việc tốt.',
        icon: 'success',
        confirmButtonText: 'Đồng ý'
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = '/staff/rent';
        }
    });
}  else {
            alert('Có lỗi 1 xảy ra trong quá trình đặt phòng!');
        }
    })
    .catch(error => {
        alert('Có lỗi 2 xảy ra trong quá trình đặt phòng!');
    });

    return false;  // Ngừng hành động submit mặc định
}

function checkRoomSelectionStaff(event) {
    // Ngừng hành động submit mặc định
    event.preventDefault();

    const rooms = document.querySelectorAll('input[name="rooms"]:checked');
    if (rooms.length === 0) {
        alert('Vui lòng chọn ít nhất một phòng!');
        return false;
    }

    // Kiểm tra thông tin khách hàng cho từng phòng
    let roomData = [];
    const customerName = document.getElementById('customer_name').value;
    const contactPhone = document.getElementById('contact_phone').value;
    if (!customerName) {
        alert('Vui lòng nhập tên khách hàng đặt phòng!');
        return false;
    }
    if (!contactPhone) {
        alert('Vui lòng nhập số điện thoại liên lạc!');
        return false;
    }
    for (let room of rooms) {
        const roomId = room.value;
        const numGuests = document.getElementById('num_guests-' + roomId).value;
        let guests = [];

        // Kiểm tra từng khách trong phòng
        for (let i = 0; i < numGuests; i++) {
            const guestName = document.getElementById('guest-name-' + roomId + '-' + i).value;
            const guestIdCard = document.getElementById('guest-idcard-' + roomId + '-' + i).value;
            const guestAddress = document.getElementById('guest-address-' + roomId + '-' + i).value;
            const guestType = document.getElementById('guest-type-' + roomId + '-' + i).value;

            if (!guestName || !guestIdCard || !guestAddress || !guestType) {
                alert('Vui lòng điền đầy đủ thông tin cho khách hàng!');
                return false;
            }

            // Thêm khách vào danh sách
            guests.push({
                name: guestName,
                idCard: guestIdCard,
                address: guestAddress,
                type: guestType
            });
        }

        // Thêm phòng vào dữ liệu gửi
        roomData.push({
            roomId: roomId,
            numGuests: numGuests,
            guests: guests
        });
    }

    // Gửi dữ liệu đã chọn đến server
    const formData = {
        customerName: customerName,
        contactPhone: contactPhone,
        checkinDate: document.getElementById('checkin_date').value,
        checkoutDate: document.getElementById('checkout_date').value,
        rooms: roomData
    };



    // Gửi yêu cầu đặt phòng
    fetch('/api/staff_cf', {
        method: 'POST',
        body: JSON.stringify(formData),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
    Swal.fire({
        title: 'Đặt phòng thành công!',
        text: 'Chúc bạn một ngày làm việc tốt.',
        icon: 'success',
        confirmButtonText: 'Đồng ý'
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = '/staff/staff_booking';
        }
    });
} else {
            alert('Có lỗi 1 xảy ra trong quá trình đặt phòng!');
        }
    })
    .catch(error => {
        alert('Có lỗi 2 xảy ra trong quá trình đặt phòng!');
    });

    return false;  // Ngừng hành động submit mặc định
}


function checkIn(reservationId) {
        // Gửi yêu cầu AJAX đến server
        fetch(`/staff/checkin/${reservationId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ is_checked_in: true })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Cập nhật UI nếu check-in thành công
                alert('Check-in thành công!');
                location.reload();  // Tải lại trang để cập nhật trạng thái
            } else {
                alert('Có lỗi 1 khi  thực hiện check-in.');
            }
        })
        .catch(error => {
            console.error('Lỗi:', error);
            alert('Có lỗi 2 khi thực hiện check-in.');
        });
    }

function checkOut(reservationId) {
        // Gửi yêu cầu AJAX đến server
        fetch(`/staff/checkout/${reservationId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ is_checked_out: true })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
    // Thông báo đẹp khi check-out thành công
    Swal.fire({
        title: 'Check-out thành công!',
        text: 'Phòng đã được trả lại.',
        icon: 'success',
        confirmButtonText: 'OK',
        customClass: {
            confirmButton: 'btn btn-primary' // Có thể tùy chỉnh giao diện button nếu cần
        }
    }).then(() => {
        location.reload();  // Tải lại trang để cập nhật trạng thái
    });
} else {
                alert('Có lỗi khi thực hiện check-in.');
            }
        })
        .catch(error => {
            console.error('Lỗi:', error);
            alert('Có lỗi khi thực hiện check-in.');
        });
    }


function payBill(billId) {
    // Gửi yêu cầu AJAX đến server để thanh toán
    fetch(`/staff/pay_bill/${billId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_paid: true })
    })
    .then(response => response.json())
    .then(data => {
         if (data.success) {
            // Hiển thị thông báo thành công với nút In hóa đơn
            Swal.fire({
                title: 'Thanh toán thành công!',
                text: 'Bạn có muốn in hóa đơn không?',
                icon: 'success',
                showCancelButton: true,
                confirmButtonText: 'In hóa đơn',
                cancelButtonText: 'Đóng',
            }).then((result) => {
                if (result.isConfirmed) {
                    // Gọi hàm in hóa đơn
                    printInvoice(billId);
                }
            });

            // Cập nhật trạng thái nút thanh toán
            const payButton = document.getElementById(`pay-btn-${billId}`);
            payButton.classList.add('disabled');
            payButton.textContent = 'Đã thanh toán';
        } else {
            alert('Có lỗi 1 khi thực hiện thanh toán.');
        }
    })
    .catch(error => {
        console.error('Lỗi:', error);
        alert('Có lỗi 2 khi thực hiện thanh toán.');
    });
}

function addComment(room_type_id) {
    let content = document.getElementById('commentId')
    if (content !== null){
        fetch('/api/comments', {
            method: 'post',
            body: JSON.stringify({
                'room_type_id': room_type_id,
                'content': content.value
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(res => res.json()).then(data=> {
            if (data.status == 201) {
                let c = data.comment

                let area = document.getElementById('commentArea')

                area.innerHTML = `
                                    <div class="row">
                        <div class="col-md-1 col-xs-4">
                            <img src="${c.user.avatar}" class="img-fluid rounded-circle" alt="demo"/>
                        </div>
                        <div class="col-md-11 col-xs-8">
                            <p>${c.content}</p>
                            <p><em>${moment(c.created_date).locale('vi').fromNow()}</em></p>
                        </div>` + area.innerHTML
            } else if (data.status == 404)
            alert(data.err_msg)
        })
    }
}
