import hmac
import hashlib
import random
from string import letters
from datetime import datetime
import re

"""
Inheritance
"""
def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

secret = "set to something"

"""
User Stuff
"""
def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)

def valid_username(username):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return username and USER_RE.match(username)

def valid_password(password):
    PASS_RE = re.compile(r"^.{3,20}$")
    return password and PASS_RE.match(password)


"""
To get_datetime()
"""
def get_month(month_int):
    months = dict(January=1, February=2, March=3, April=4, May=5, June=6, July=7, August=8, September=9, October=10, November=11, December=12)
    for month, num in months.iteritems():
        if num == month_int:
            return month

def get_dayofweek(day_int):
    days = dict(Mon=1, Tues=2, Wed=3, Thurs=4, Fri=5, Sat=6, Sun=7)
    for day, num in days.iteritems():
        if num == day_int:
            return day

def get_datetime():
    # populate result dictionary
    result = {}
    mydate = datetime.now()
    result['day_of_month'] = mydate.day
    result['day_of_week'] = get_dayofweek(mydate.weekday())
    result['month'] = get_month(mydate.month)
    result['year'] = mydate.now().year
    time = str(mydate.time())
    index = time.find('.')
    new_time = time[:index]
    result['time'] = new_time
    # return result in string format
    date_list = [str(result['day_of_week']), str(result['month']), str(result['day_of_month']), str(result['time']), str(result['year'])]
    output = " ".join(date_list)
    return output

"""
Version Control
"""
def trunc_version(title):
    index = title.rfind('v')
    return title[:index]


"""
def get_datetime():
    result = {}
    result['day'] = datetime.now().weekday()
    result['month'] = datetime.now().month
    result['year'] = datetime.now().year
    time = str(datetime.now().time())
    index = time.find('.')
    new_time = time[:index]
    result['time'] = new_time
    return result

def convert_datetime(date):
    index = date.find('.')
    new_date = date[:index]
    return new_date
"""