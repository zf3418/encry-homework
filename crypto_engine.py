# crypto_engine.py
import pyffx
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import json

class CryptoEngine:
    def __init__(self, password: str, salt: bytes):

        self.main_key = PBKDF2(password, salt, dkLen=32, count=100000, hmac_hash_module=SHA256)
        

        self.fpe_phone = pyffx.Integer(self.main_key, length=11)
        self.fpe_id = pyffx.Integer(self.main_key, length=18)
        self.fpe_cc = pyffx.Integer(self.main_key, length=16)
        self.fpe_string = pyffx.String(self.main_key, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-+', length=0) # length=0 表示变长(需要pyffx支持)或者固定一个长度

    def encrypt_fpe_integer(self, number_str, length):
        val = int(number_str)
        if length == 11:
            return str(self.fpe_phone.encrypt(val))
        elif length == 18:
            return str(self.fpe_id.encrypt(val))
        elif length == 16:
            return str(self.fpe_cc.encrypt(val))
        return number_str

    def decrypt_fpe_integer(self, number_str, length):
        val = int(number_str)
        if length == 11:
            return str(self.fpe_phone.decrypt(val))
        elif length == 18:
            return str(self.fpe_id.decrypt(val))
        elif length == 16:
            return str(self.fpe_cc.decrypt(val))
        return number_str

    def encrypt_fpe_string(self, text):

        try:

            if len(text) < 4: return text
            target = text[:4] 
            rest = text[4:]
            cipher = pyffx.String(self.main_key, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', length=len(target))
            return cipher.encrypt(target) + rest
        except:
            return text 

    def decrypt_fpe_string(self, text):
        try:
            if len(text) < 4: return text
            target = text[:4]
            rest = text[4:]
            cipher = pyffx.String(self.main_key, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', length=len(target))
            return cipher.decrypt(target) + rest
        except:
            return text

    def aes_encrypt_log(self, data: dict):

        nonce = get_random_bytes(12)
        cipher = AES.new(self.main_key, AES.MODE_GCM, nonce=nonce)
        json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
        ciphertext, tag = cipher.encrypt_and_digest(json_bytes)
        return nonce, ciphertext, tag

    def aes_decrypt_log(self, nonce, ciphertext, tag):
        try:
            cipher = AES.new(self.main_key, AES.MODE_GCM, nonce=nonce)
            json_bytes = cipher.decrypt_and_verify(ciphertext, tag)
            return json.loads(json_bytes.decode('utf-8'))
        except ValueError:
            return {"error": "数据完整性校验失败，日志可能被篡改！"}