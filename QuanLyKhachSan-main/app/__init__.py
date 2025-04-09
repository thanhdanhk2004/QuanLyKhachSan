from flask import Flask
from urllib.parse import quote
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary
from flask_mail import Mail

app = Flask(__name__)
app.secret_key = "HHabiadfh8if$55FDY"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/quanlydb?charset=utf8mb4" % quote('Admin@123')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 50
app.config["COMMENT_SIZE"] = 3

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Thay bằng server bạn dùng
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'nguyentrunganhtuan201004@gmail.com'  # Email của bạn
app.config['MAIL_PASSWORD'] = 'doua whjv kdiv lhpd' # Mật khẩu ứng dụng hoặc API key
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'

mail = Mail(app)
db = SQLAlchemy(app)
login = LoginManager(app)

cloudinary.config(
    cloud_name = "dqtk7akkz",
    api_key = "175943162423538",
    api_secret = "yUVCdUHmqdgTU5OMH68op0ADdsc", # Click 'View API Keys' above to copy your API secret
    secure=True
)