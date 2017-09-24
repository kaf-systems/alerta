
from datetime import datetime
from uuid import uuid4

from flask import current_app

from alerta.app import db
from alerta.auth.utils import generate_password_hash, check_password_hash
from alerta.utils.api import absolute_url


class User(object):
    """
    User model for BasicAuth only.
    """

    def __init__(self, name, email, password, roles, text, **kwargs):

        self.id = kwargs.get('id', None) or str(uuid4())
        self.name = name
        self.email = email  # => g.user
        self.password = password  # NB: hashed password
        self.roles = ['admin'] if self.email in current_app.config['ADMIN_USERS'] else (roles or ['user'])
        self.create_time = kwargs.get('create_time', None) or datetime.utcnow()
        self.last_login = kwargs.get('last_login', None)
        self.text = text or ""
        self.email_verified = kwargs.get('email_verified', False)

    @property
    def domain(self):
        return self.email.split('@')[1] if '@' in self.email else None

    @classmethod
    def parse(cls, json):
        return User(
            name=json.get('name'),
            email=json.get('email'),
            password=generate_password_hash(json.get('password', None)),
            roles=json.get('roles', list()),
            text=json.get('text', None),
            email_verified=json.get('email_verified', None)
        )

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'href': absolute_url('/user/' + self.id),
            'name': self.name,
            'email': self.email,
            'domain': self.domain,
            'provider': 'basic',
            'roles': self.roles,
            'createTime': self.create_time,
            'lastLogin': self.last_login,
            'text': self.text,
            'email_verified': self.email_verified or False
        }

    def __repr__(self):
        return 'User(id=%r, name=%r, email=%r, roles=%r, email_verified=%r)' % (
            self.id, self.name, self.email, ','.join(self.roles), self.email_verified
        )

    @classmethod
    def from_document(cls, doc):
        return User(
            id=doc.get('id', None) or doc.get('_id'),
            name=doc.get('name', None),
            email=doc.get('email', None) or doc.get('login', None),
            password=doc.get('password', None),
            roles=doc.get('roles', list()),
            create_time=doc.get('createTime', None),
            last_login=doc.get('lastLogin', None),
            text=doc.get('text', None),
            email_verified=doc.get('email_verified', None)
        )

    @classmethod
    def from_record(cls, rec):
        return User(
            id=rec.id,
            name=rec.name,
            email=rec.email,
            password=rec.password,
            roles=rec.roles,
            create_time=rec.create_time,
            last_login=rec.last_login,
            text=rec.text,
            email_verified=rec.email_verified
        )

    @classmethod
    def from_db(cls, r):
        if isinstance(r, dict):
            return cls.from_document(r)
        elif isinstance(r, tuple):
            return cls.from_record(r)
        else:
            return

    def create(self):
        return User.from_db(db.create_user(self))

    @staticmethod
    def get(id):
        return User.from_db(db.get_user(id))

    @staticmethod
    def get_by_email(email):
        return User.from_db(db.get_user_by_email(email))

    @staticmethod
    def find_all(query=None):
        return [User.from_db(user) for user in db.get_users(query)]

    def update_last_login(self):
        return db.update_last_login(self.id)

    def set_email_hash(self, hash):
        return db.set_email_hash(self.id, hash)

    @staticmethod
    def verify_hash(hash):
        return User.from_db(db.get_user_by_hash(hash))

    def set_email_verified(self, verified=True):
        self.update(email_verified=verified)

    def update(self, **kwargs):
        update = dict()
        if 'name' in kwargs:
            update['name'] = kwargs['name']
        if 'email' in kwargs:
            update['email'] = kwargs['email']
        if 'password' in kwargs:
            update['password'] = generate_password_hash(kwargs['password'])
        if 'role' in kwargs:
            update['roles'] = [kwargs['role']]
        elif 'roles' in kwargs:
            update['roles'] = kwargs['roles']
        if 'text' in kwargs:
            update['text'] = kwargs['text']
        if 'email_verified' in kwargs:
            update['email_verified'] = kwargs['email_verified']
        return User.from_db(db.update_user(self.id, **update))

    def delete(self):
        return db.delete_user(self.id)