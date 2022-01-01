import os

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from apps.article.models import Article_type, Article
from apps.user.models import User, Photo, Aboutme, Messageboard
from apps.utils.utils import upload_qiniu, delete_qiniu
from exts import db
from settings import Config

user_bp1 = Blueprint('user', __name__, url_prefix='/user')

required_login_list = ['/user/center/', '/user/change/',
                       '/article/publish/', "/user/upload_photo/"
                       , "/user/photo_del/",
                         "/article/article_comment/",
                        "/user/aboutme/",
                         "/user/show_about/"]



# ****重点*****
@user_bp1.before_app_request
def before_request1():
    if request.path in required_login_list:
        id = session.get('uid')
        if not id:
            return render_template('user/login.html')
        else:
            user = User.query.get(id)
            # g对象，本次请求的对象
            g.user = user


@user_bp1.app_template_filter('cdecode')
def content_decode(content):
    content = content.decode('utf-8')
    return content[:200]

@user_bp1.app_template_filter('cdecode1')
def content_decode(content):
    content = content.decode('utf-8')
    return content


# 首页
@user_bp1.route('/')
def index():
    uid = session.get('uid')

    page = int(request.args.get('page', 1))
    pagination = Article.query.order_by(-Article.pdatetime).paginate(page=page, per_page=5)
    # 获取分类列表
    types = Article_type.query.all()
    # 判断用户是否登录
    if uid:
        user = User.query.get(uid)
        return render_template('user/index.html', user=user, types=types, pagination=pagination)
    else:
        return render_template('user/index.html', types=types, pagination=pagination)


# 用户注册
@user_bp1.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        repassword = request.form.get('repassword')
        phone = request.form.get('phone')
        email = request.form.get('email')
        if password == repassword:
            # 注册用户
            user = User()
            user.username = username
            # 使用自带的函数实现加密：generate_password_hash
            user.password = generate_password_hash(password)
            # print(password)
            user.phone = phone
            user.email = email
            # 添加并提交
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('user.index'))
    return render_template('user/register.html')


# 手机号码验证
@user_bp1.route('/checkphone/', methods=['GET', 'POST'])
def check_phone():
    phone = request.args.get('phone')
    user = User.query.filter(User.phone == phone).all()
    print(user)
    # code: 400 不能用    200 可以用
    if len(user) > 0:
        return jsonify(code=400, msg='此号码已被注册')
    else:
        return jsonify(code=200, msg='此号码可用')


# 用户登录
@user_bp1.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        f = request.args.get('f')
        if f == '1':  # 用户名或者密码
            username = request.form.get('username')
            password = request.form.get('password')
            users = User.query.filter(User.username == username).all()
            for user in users:
                # 如果flag=True表示匹配，否则密码不匹配
                flag = check_password_hash(user.password, password)
                if flag:
                    # 1。cookie实现机制
                    # response = redirect(url_for('user.index'))
                    # response.set_cookie('uid', str(user.id), max_age=1800)
                    # return response
                    # 2。session机制,session当成字典使用
                    session['uid'] = user.id
                    return redirect(url_for('user.index'))
            else:
                return render_template('user/login.html', msg='用户名或者密码有误')
        elif f == '2':  # 手机号码与验证码
            print('----->22222')
            phone = request.form.get('phone')
            code = request.form.get('code')
            # 先验证验证码
            valid_code = session.get(phone)
            print('valid_code:' + str(valid_code))
            if code == valid_code:
                # 查询数据库
                user = User.query.filter(User.phone == phone).first()
                print(user)
                if user:
                    # 登录成功
                    session['uid'] = user.id
                    return redirect(url_for('user.index'))
                else:
                    return render_template('user/login.html', msg='此号码未注册')
            else:
                return render_template('user/login.html', msg='验证码有误！')

    return render_template('user/login.html')


# 发送短信息
@user_bp1.route('/sendMsg/')
def send_message():
    phone = request.form.get("phone")
    session[phone] = "5201314"
    return jsonify(code=200, msg="短信发送成功")

# 用户退出
@user_bp1.route('/logout/')
def logout():
    # 1。 cookie的方式
    # response = redirect(url_for('user.index'))
    # 通过response对象的delete_cookie(key),key就是要删除的cookie的key
    # response.delete_cookie('uid')
    # 2。session的方式
    # del session['uid']
    session.clear()
    return redirect(url_for('user.index'))


# 用户中心
@user_bp1.route('/center/')
def user_center():
    types = Article_type.query.all()
    photos = Photo.query.filter(Photo.user_id == g.user.id).all()
    return render_template('user/center.html', user=g.user, types=types,photos=photos)


# 图片的扩展名
ALLOWED_EXTENSIONS = ['jpg', 'png', 'gif', 'bmp',"jpeg"]


# 用户信息修改
@user_bp1.route('/change/', methods=['GET', 'POST'])
def user_change():
    if request.method == 'POST':
        username = request.form.get('username')
        phone = request.form.get('phone')
        email = request.form.get('email')
        # 只要有文件（图片），获取方式必须使用request.files.get(name)
        icon = request.files.get('icon')
        # print('======>', icon)  # FileStorage
        # 属性： filename 用户获取文件的名字
        # 方法:  save(保存路径)
        icon_name = icon.filename  # 1440w.jpg
        suffix = icon_name.rsplit('.')[-1]
        if suffix in ALLOWED_EXTENSIONS:
            icon_name = secure_filename(icon_name)  # 保证文件名是符合python的命名规则
            file_path = os.path.join(Config.UPLOAD_ICON_DIR, icon_name)
            icon.save(file_path)
            # 保存成功
            user = g.user
            user.username = username
            user.phone = phone
            user.email = email
            path = 'upload/icon/'
            user.icon = path + icon_name
            db.session.commit()
            return redirect(url_for('user.user_center'))
        else:
            return render_template('user/center.html', user=g.user, msg='必须是扩展名是：jpg,png,gif,bmp格式')

        # 查询一下手机号码
        # users = User.query.all()
        # for user in users:
        #     if user.phone == phone:
        #         # 说明数据库中已经有人注册此号码
        #         return render_template('user/center.html', user=g.user,msg='此号码已被注册')
        #

    return render_template('user/center.html', user=g.user)

@user_bp1.route("/upload_photo/",methods=["POST","GET"],endpoint="photo")
def upload_photo():
    if request.method == "POST":
        #获取对应的上传的内容
        photo = request.files.get('photo')
        #工具模块当中封装的一个模块
        ret,info = upload_qiniu(photo)
        if info.status_code == 200:
            photo = Photo()
            photo.photo_name = ret["key"]
            photo.user_id = g.user.id
            db.session.add(photo)
            db.session.commit()
            return "上传成功"
        else:
            return "上传失败！"

@user_bp1.route("/myphoto/")
def myphoto():
    page = int(request.args.get("page",1))
    photos = Photo.query.paginate(page=page,per_page=3)
    user_id = session.get("uid")
    user  = None
    if user_id:
        user = User.query.get(user_id)
        return render_template("user/myphoto.html",photos=photos,user=user)


@user_bp1.route("/photo_del/")
def photo_del():
    pid = request.args.get("pid")
    photo = Photo.query.get(pid)
    photo_name = photo.photo_name
    info = delete_qiniu(file_name=photo_name)
    if info.status_code == 200:
        #数据库进行删除
        db.session.delete(photo)
        db.session.commit()
        return redirect(url_for('user.user_center'))
    else:
        return render_template('user/500.html',err_msg='删除相册图片失败')


@user_bp1.route("/error/")
def error():
    referer = request.headers.get("Referer",None)
    return render_template('user/500.html',err_msg='有误',referer=referer)

@user_bp1.route('/aboutme/',methods=["POST","GET"])
def about_me():
    content = request.form.get("about_content")
    aboutme = Aboutme()
    aboutme.content = content
    aboutme.user_id = g.user.id
    try:
        db.session.add(aboutme)
        db.session.commit()
        return render_template('user/aboutme.html', user=g.user)
    except Exception as e:
        print(f"出现错误啦=====>{e}")
        db.session.rollback()
        return render_template("user/500.html",err_msg="数据库存储出现错误")


@user_bp1.route("/show_about/")
def show_about():
    return render_template("user/aboutme.html",user = g.user )


@user_bp1.route("/board/",methods=['POST',"GET"])
def show_board():
    uid = session.get("uid")
    user = None
    if uid:
        user = User.query.get(uid)
    page = int(request.args.get('page',1))
    boards = Messageboard.query.order_by(-Messageboard.mdatetime).paginate(page=page,per_page=3)
    if request.method == "POST":
        content = request.form.get('board')
        msg_board = Messageboard()
        msg_board.content = content
        if uid:
            msg_board.user_id = uid
            db.session.add(msg_board)
            db.session.commit()
            return redirect(url_for('user.show_board'))
    return render_template("user/board.html",user=user,boards=boards)


@user_bp1.route('/delete_board/')
def delete_board():
    board_id = request.args.get("bid")
    if board_id:
        message = Messageboard.query.get(board_id)
        db.session.delete(message)
        db.session.commit()
        return redirect(url_for("user.user_center"))


