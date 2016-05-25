db_engine = sa.create_engine('sqlite:///db.sqlite')
metadata = sa.MetaData()


# Table definition - video
# 视频列表
video_table = sa.Table("video", metadata,
    # video_id - 视频唯一识别码
    sa.Column('video_id', CHAR, primary_key=True),
    # video_name - 视频名称
    sa.Column('video_name', CHAR),
    # lesson_id - 所属课程的唯一识别码
    sa.Column('lesson_id', CHAR, sa.ForeignKey("lesson.lesson_id")))

# Table definition - lesson
# 课程列表
lesson_table = sa.Table("lesson", metadata,
    # lesson_id - 课程唯一识别码
    sa.Column('lesson_id', CHAR, primary_key=True),
    # lesson_name - 课程名称
    sa.Column('lesson_name', CHAR))

# Table definition - user
# 用户列表
user_table = sa.Table("user", metadata,
    # user_id - 用户唯一识别码
    sa.Column('user_id', CHAR, nullable=True, primary_key=True),
    # role_id - 用户类型唯一识别码
    sa.Column('role_id', CHAR, sa.ForeignKey("role.role_id")),
    # vb_class_id - VB班级唯一识别码
    sa.Column('vb_class_id', CHAR, sa.ForeignKey("vb_class.vb_class_id"), nullable=True),
    # gre_class_id - GRE班级唯一识别码
    sa.Column('gre_class_id', CHAR, sa.ForeignKey("gre_class.gre_class_id"), nullable=True),
    # user_name - 用户姓名
    sa.Column('user_name', CHAR),
    # login_name - 登录名
    sa.Column('login_name', CHAR),
    # login_password - 登录密码
    sa.Column('login_password', CHAR),
    # password_salt - Salt (cryptography)
    sa.Column('password_salt', CHAR),
    # face_id - Face++库中人脸识别符
    sa.Column('face_id', CHAR, nullable=True))

# Table definition - device
# iPad设备列表
device_table = sa.Table("device", metadata,
    # device_id - 设备唯一识别码
    sa.Column('device_id', CHAR, primary_key=True),
    # device_name - 设备名称
    sa.Column('device_name', CHAR),
    # device_code - 设备条码
    sa.Column('device_code', CHAR))

# Table definition - device_video
# 设备-视频映射表
device_video_table = sa.Table("device_video", metadata,
    # device_id - 设备唯一识别码
    sa.Column('device_id', CHAR, sa.ForeignKey("device.device_id")),
    # video_id - 视频唯一识别码
    sa.Column('video_id', CHAR, sa.ForeignKey("video.video_id")))

# Table definition - appointment
# 预约列表
appointment_table = sa.Table("appointment", metadata,
    # appointment_id - 预约记录唯一识别码
    sa.Column('appointment_id', CHAR, primary_key=True),
    # user_id - 用户唯一识别码
    sa.Column('user_id', CHAR, sa.ForeignKey("user.user_id")),
    # period_id - 预约时段唯一识别码
    sa.Column('period_id', CHAR, sa.ForeignKey("period.period_id")),
    # attendance - 是否赴约
    sa.Column('attendance', BINARY, nullable=True))

# Table definition - period
# 预约时段列表
period_table = sa.Table("period", metadata,
    # period_id - 预约时段唯一识别码
    sa.Column('period_id', CHAR, primary_key=True),
    # period_start - 开始时间
    sa.Column('period_start', DATETIME),
    # period_end - 结束时间
    sa.Column('period_end', DATETIME))

# Table definition - progress
# 学习进度
progress_table = sa.Table("progress", metadata,
    # progress_id - 学习进度唯一识别符
    sa.Column('progress_id', CHAR, primary_key=True),
    # user_id - 用户唯一识别码
    sa.Column('user_id', CHAR, sa.ForeignKey("user.user_id")),
    # video_id - 视频唯一识别码
    sa.Column('video_id', CHAR, sa.ForeignKey("video.video_id")),
    # device_in_id - 归还记录唯一识别码
    sa.Column('device_in_id', CHAR, sa.ForeignKey("device_in.device_in_id")))

# Table definition - device_out
# 机器借出记录
device_out_table = sa.Table("device_out", metadata,
    # device_out_id - 借出记录唯一识别码
    sa.Column('device_out_id', CHAR, primary_key=True),
    # borrower_id - 借阅用户唯一识别码
    sa.Column('borrower_id', CHAR, sa.ForeignKey("user.user_id")),
    # agent_id - 经办人唯一识别码
    sa.Column('agent_id', CHAR, sa.ForeignKey("user.user_id")),
    # device_id - 设备唯一识别码
    sa.Column('device_id', CHAR, sa.ForeignKey("device.device_id")),
    # borrow_time - 借出时间
    sa.Column('borrow_time', DATETIME),
    # appointment_id - 预约记录唯一识别码
    sa.Column('appointment_id', CHAR, sa.ForeignKey("appointment.appointment_id"), nullable=True))

# Table definition - device_in
# 机器归还记录
device_in_table = sa.Table("device_in", metadata,
    # device_in_id - 归还记录唯一识别码
    sa.Column('device_in_id', CHAR, primary_key=True),
    # borrower_id - 借出用户唯一识别码
    sa.Column('borrower_id', CHAR, sa.ForeignKey("user.user_id")),
    # agent_id - 经办人唯一识别码
    sa.Column('agent_id', CHAR, sa.ForeignKey("user.user_id")),
    # device_id - 设备唯一识别码
    sa.Column('device_id', CHAR, sa.ForeignKey("device.device_id")),
    # return_time - 归还时间
    sa.Column('return_time', DATETIME),
    # device_out_id - 借出记录唯一识别码
    sa.Column('device_out_id', CHAR, sa.ForeignKey("device_out.device_out_id")))

# Table definition - role
# 角色列表
role_table = sa.Table("role", metadata,
    # role_id - 用户类型唯一识别码
    sa.Column('role_id', CHAR, primary_key=True),
    # role_name - 角色名称
    sa.Column('role_name', CHAR))

# Table definition - vb_class
# VB班级列表
vb_class_table = sa.Table("vb_class", metadata,
    # vb_class_id - VB班级唯一识别码
    sa.Column('vb_class_id', CHAR, primary_key=True),
    # vb_class_name - VB班级名称
    sa.Column('vb_class_name', CHAR))

# Table definition - gre_class
# GRE班级列表
gre_class_table = sa.Table("gre_class", metadata,
    # gre_class_id - GRE班级唯一识别码
    sa.Column('gre_class_id', CHAR, primary_key=True),
    # gre_class_name - GRE班级名称
    sa.Column('gre_class_name', CHAR))


# Mapping Objects
class video():
    def __init__(self, video_id, video_name, lesson_id):
        self.video_id = video_id
        self.video_name = video_name
        self.lesson_id = lesson_id

    def __repr__(self):
        return "<video('%s', '%s', '%s')>" % (self.video_id, self.video_name, self.lesson_id)

class lesson():
    def __init__(self, lesson_id, lesson_name):
        self.lesson_id = lesson_id
        self.lesson_name = lesson_name

    def __repr__(self):
        return "<lesson('%s', '%s')>" % (self.lesson_id, self.lesson_name)

class user():
    def __init__(self, user_id, role_id, vb_class_id, gre_class_id, user_name, login_name, login_password, password_salt, face_id):
        self.user_id = user_id
        self.role_id = role_id
        self.vb_class_id = vb_class_id
        self.gre_class_id = gre_class_id
        self.user_name = user_name
        self.login_name = login_name
        self.login_password = login_password
        self.password_salt = password_salt
        self.face_id = face_id

    def __repr__(self):
        return "<user('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')>" % (self.user_id, self.role_id, self.vb_class_id, self.gre_class_id, self.user_name, self.login_name, self.login_password, self.password_salt, self.face_id)

class device():
    def __init__(self, device_id, device_name, device_code):
        self.device_id = device_id
        self.device_name = device_name
        self.device_code = device_code

    def __repr__(self):
        return "<device('%s', '%s', '%s')>" % (self.device_id, self.device_name, self.device_code)

class device_video():
    def __init__(self, device_id, video_id):
        self.device_id = device_id
        self.video_id = video_id

    def __repr__(self):
        return "<device_video('%s', '%s')>" % (self.device_id, self.video_id)

class appointment():
    def __init__(self, appointment_id, user_id, period_id, attendance):
        self.appointment_id = appointment_id
        self.user_id = user_id
        self.period_id = period_id
        self.attendance = attendance

    def __repr__(self):
        return "<appointment('%s', '%s', '%s', '%s')>" % (self.appointment_id, self.user_id, self.period_id, self.attendance)

class period():
    def __init__(self, period_id, period_start, period_end):
        self.period_id = period_id
        self.period_start = period_start
        self.period_end = period_end

    def __repr__(self):
        return "<period('%s', '%s', '%s')>" % (self.period_id, self.period_start, self.period_end)

class progress():
    def __init__(self, progress_id, user_id, video_id, device_in_id):
        self.progress_id = progress_id
        self.user_id = user_id
        self.video_id = video_id
        self.device_in_id = device_in_id

    def __repr__(self):
        return "<progress('%s', '%s', '%s', '%s')>" % (self.progress_id, self.user_id, self.video_id, self.device_in_id)

class device_out():
    def __init__(self, device_out_id, borrower_id, agent_id, device_id, borrow_time, appointment_id):
        self.device_out_id = device_out_id
        self.borrower_id = borrower_id
        self.agent_id = agent_id
        self.device_id = device_id
        self.borrow_time = borrow_time
        self.appointment_id = appointment_id

    def __repr__(self):
        return "<device_out('%s', '%s', '%s', '%s', '%s', '%s')>" % (self.device_out_id, self.borrower_id, self.agent_id, self.device_id, self.borrow_time, self.appointment_id)

class device_in():
    def __init__(self, device_in_id, borrower_id, agent_id, device_id, return_time, device_out_id):
        self.device_in_id = device_in_id
        self.borrower_id = borrower_id
        self.agent_id = agent_id
        self.device_id = device_id
        self.return_time = return_time
        self.device_out_id = device_out_id

    def __repr__(self):
        return "<device_in('%s', '%s', '%s', '%s', '%s', '%s')>" % (self.device_in_id, self.borrower_id, self.agent_id, self.device_id, self.return_time, self.device_out_id)

class role():
    def __init__(self, role_id, role_name):
        self.role_id = role_id
        self.role_name = role_name

    def __repr__(self):
        return "<role('%s', '%s')>" % (self.role_id, self.role_name)

class vb_class():
    def __init__(self, vb_class_id, vb_class_name):
        self.vb_class_id = vb_class_id
        self.vb_class_name = vb_class_name

    def __repr__(self):
        return "<vb_class('%s', '%s')>" % (self.vb_class_id, self.vb_class_name)

class gre_class():
    def __init__(self, gre_class_id, gre_class_name):
        self.gre_class_id = gre_class_id
        self.gre_class_name = gre_class_name

    def __repr__(self):
        return "<gre_class('%s', '%s')>" % (self.gre_class_id, self.gre_class_name)


# Declare mappings
mapper(video, video_table)
mapper(lesson, lesson_table)
mapper(user, user_table)
mapper(device, device_table)
mapper(device_video, device_video_table)
mapper(appointment, appointment_table)
mapper(period, period_table)
mapper(progress, progress_table)
mapper(device_out, device_out_table)
mapper(device_in, device_in_table)
mapper(role, role_table)
mapper(vb_class, vb_class_table)
mapper(gre_class, gre_class_table)

# Create a session
session = sessionmaker(bind=db_engine)