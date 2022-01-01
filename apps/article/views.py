from flask import Blueprint, request, g, redirect, url_for, \
    render_template, jsonify, session

from apps.article.models import Article, Article_type, Comment
from apps.user.models import User
from exts import db

article_bp1 = Blueprint('article', __name__, url_prefix='/article')


# 自定义过滤器
@article_bp1.app_template_filter('cdecode')
def content_decode(content):
    content = content.decode('utf-8')
    return content

@article_bp1.route('/publish/', methods=['POST', 'GET'])
def publish_article():
    if request.method == 'POST':
        title = request.form.get('title')
        type_id = request.form.get('type')
        content = request.form.get('content')
        # 添加文章
        article = Article()
        article.title = title
        article.type_id = type_id
        article.content = content
        article.user_id = g.user.id
        db.session.add(article)
        db.session.commit()
        return redirect(url_for('user.index'))


@article_bp1.route('/detail/',methods=["POST","GET"])
def article_detail():
    # 获取文章对象通过id
    article_id = request.args.get('aid')
    article = Article.query.get(article_id)
    # 获取文章分类
    types = Article_type.query.all()
    user_id = session.get('uid')
    user = None
    if user_id:
        user = User.query.get(user_id)
    page = int(request.args.get('page', 1))
    comments = Comment.query.filter(Comment.article_id == article_id).order_by(-Comment.cdatetime).paginate(page=page , per_page=3)

    return render_template('article/detail3.html', article=article, types=types,user=user,comments=comments)


@article_bp1.route('/love/')
def article_love():
    article_id = request.args.get('aid')
    tag = request.args.get('tag')

    article = Article.query.get(article_id)
    if tag == '1':
        article.love_num -= 1
    else:
        article.love_num += 1
    db.session.commit()
    return jsonify(num=article.love_num)

#发表文章的评论
@article_bp1.route("/article_comment/",methods=["POST","GET"],endpoint="comment")
def article_detail():
    if request.method == "POST":
        comment_content = request.form.get('comment')
        user_id = g.user.id
        article_id = request.form.get("aid")
        comment = Comment()
        comment.comment = comment_content
        comment.user_id = user_id
        comment.article_id = article_id
        try:
            db.session.add(comment)
            db.session.commit()
            return redirect(url_for('article.article_detail')+f"?aid={article_id}")
        except Exception as e:
            print(f"出现错误啦{e}")
            db.session.rollback()
            return
    return redirect(url_for('user.index'))

@article_bp1.route('/type_search/')
def type_search():
    uid = session.get("uid")
    user = None
    if uid:
        user = User.query.get(uid)
    types = Article_type.query.all()
    type_id = request.args.get('tid')
    type = Article_type.query.get(type_id)
    return render_template('article/article_type.html',user=user,types=types,type=type)
