import os
from dotenv import load_dotenv

from deta import Deta
load_dotenv(".env")


DETA_key="c0ek0nwj_5x388wVo2BSLPJFhZymp51xwSYDikHBW"
deta=Deta(DETA_key)
DETA_key=os.getenv("DETA_key")
db=deta.Base("users_db")
def insert_user(username,name,password):
    return db.put({"key":username,"name":name,"password":password})
insert_user("aa","bb","asd")
def fetch_all_users():
    """Returns a dict of all users"""
    res = db.fetch()
    return res.items


def get_user(username):
    """If not found, the function will return None"""
    return db.get(username)


def update_user(username, updates):
    """If the item is updated, returns None. Otherwise, an exception is raised"""
    return db.update(updates, username)


def delete_user(username):
    """Always returns None, even if the key does not exist"""
    return db.delete(username)
