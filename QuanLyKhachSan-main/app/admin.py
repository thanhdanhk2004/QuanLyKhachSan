from calendar import month

from flask_admin import Admin, BaseView,expose, AdminIndexView
from flask import request

from app import db, app
from flask_admin.contrib.sqla import ModelView
from app.models import Booking, Room, Customer, User, UserRole, RoomType
from flask_login import current_user, logout_user
from flask import redirect
import dao
from datetime import datetime

class AuthenticatedView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role.__eq__(UserRole.ADMIN)



class MyView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role.__eq__(UserRole.ADMIN)


class RoomTypeView(AuthenticatedView):
    column_list = ['name', 'price','max_guests','proportion','coefficient','room']
    can_export = True
    column_searchable_list = ['id','name']
    column_filters = ['id','name']
    can_view_details = True

class RoomView(AuthenticatedView):
    can_view_details = True

class LogoutView(MyView):
    @expose("/")
    def index(self):
        logout_user()
        return redirect("/admin")

class StatsView(MyView):
    @expose("/")
    def index(self):
        kw = request.args.get('kw')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        stats = dao.room_stats(kw=kw, from_date=from_date, to_date=to_date)
        return self.render('admin/stats.html',
                           stats=stats)
class DoanhThuView(MyView):
    @expose("/")
    def index(self):
        year = request.args.get('year', datetime.now().year)
        month_stats = dao.revenue_time(year=year)
        return self.render('admin/doanhthu.html',
                           month_stats=month_stats)

class MyAdminIndex(AdminIndexView):
    @expose('/')
    def index(self):
        stats = dao.roomType_stats()
        return self.render('admin/index.html', stats=stats)

admin = Admin(app, name='ecourseapp',template_mode='bootstrap4', index_view= MyAdminIndex())



admin.add_view(RoomTypeView(RoomType, db.session))
admin.add_view(RoomView(Room, db.session))
admin.add_view(AuthenticatedView(User, db.session))
admin.add_view(StatsView(name="Thống kê loại phòng"))
admin.add_view(DoanhThuView(name="Thống kê doanh thu"))
admin.add_view(LogoutView(name="Đăng xuất"))