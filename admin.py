from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, jsonify
from datetime import datetime, timedelta
import json

class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class UserAdmin(SecureModelView):
    column_exclude_list = ['password_hash']
    column_searchable_list = ['username']
    column_filters = ['created_at', 'is_admin']
    
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.set_password(form.password.data)

class MessageAdmin(SecureModelView):
    column_searchable_list = ['content']
    column_filters = ['is_spam', 'checked_at', 'user_id']
    column_default_sort = ('checked_at', True)

class AnalyticsView(BaseView):
    @expose('/')
    def index(self):
        if not (current_user.is_authenticated and current_user.is_admin):
            return redirect(url_for('login'))

        from app import Message, db
        from sqlalchemy import func, cast, Date

        # Get daily statistics
        daily_stats = db.session.query(
            cast(Message.checked_at, Date).label('date'),
            func.count(Message.id).label('total_messages'),
            func.sum(cast(Message.is_spam, db.Integer)).label('spam_messages')
        ).group_by(cast(Message.checked_at, Date)).all()

        # Format statistics for template
        stats = [{
            'date': stat.date.strftime('%Y-%m-%d'),
            'total_messages': stat.total_messages,
            'spam_messages': stat.spam_messages or 0,
            'spam_ratio': (stat.spam_messages or 0) / stat.total_messages if stat.total_messages > 0 else 0
        } for stat in daily_stats]

        # Calculate overall statistics
        total_messages = sum(s['total_messages'] for s in stats)
        total_spam = sum(s['spam_messages'] for s in stats)

        return self.render('admin/analytics.html',
                         stats=stats,
                         total_messages=total_messages,
                         total_spam=total_spam)
