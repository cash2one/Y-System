# -*- coding: utf-8 -*-

import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE'))
    SQLALCHEMY_COMMIT_ON_TEARDOWN = bool(os.environ.get('SQLALCHEMY_COMMIT_ON_TEARDOWN'))
    SQLALCHEMY_RECORD_QUERIES = bool(os.environ.get('SQLALCHEMY_RECORD_QUERIES'))
    SQLALCHEMY_TRACK_MODIFICATIONS = bool(os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS'))
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USE_SSL = bool(os.environ.get('MAIL_USE_SSL'))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    YSYS_MAIL_SUBJECT_PREFIX = os.environ.get('YSYS_MAIL_SUBJECT_PREFIX')
    YSYS_MAIL_SENDER = os.environ.get('YSYS_MAIL_SENDER')
    YSYS_ADMIN = os.environ.get('YSYS_ADMIN')

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'ysys-beta.sqlite')


class BetaConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'ysys-beta.sqlite')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'ysys_prod.sqlite')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_SSL', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.YSYS_MAIL_SENDER,
            toaddrs=[cls.YSYS_ADMIN],
            subject=cls.YSYS_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


config = {
    'dev': DevelopmentConfig,
    'beta': BetaConfig,
    'prod': ProductionConfig,

    'default': DevelopmentConfig
}
