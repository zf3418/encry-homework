# data_processor.py
import re
import spacy
from config import PATTERNS, DECRYPT_PATTERNS 


try:
    nlp = spacy.load("zh_core_web_sm")
except:
    import en_core_web_sm
    nlp = en_core_web_sm.load()

class DataProcessor:
    def __init__(self, crypto_engine):
        self.crypto = crypto_engine
        self.name_map = {} 
        self.reverse_name_map = {}

    def _process_regex(self, text, pattern, encrypt_func, mode='encrypt'):
        """通用正则处理回调"""
        def callback(match):
            original = match.group()
            # 邮箱特殊处理
            if '@' in original:

                parts = original.split('@')
                user_part = parts[0]
                domain_part = parts[1]
                
                processed_user = encrypt_func(user_part)
                return f"{processed_user}@{domain_part}"
            
            # 普通数字处理
            return encrypt_func(original)
        
        return re.sub(pattern, callback, text)

    def encrypt_all(self, text):

        # 1. 姓名 
        doc = nlp(text)
        temp_text = text
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text
                if name not in self.name_map:
                    fake = f"User_{len(self.name_map) + 101}"
                    self.name_map[name] = fake
                    self.reverse_name_map[fake] = name
                temp_text = temp_text.replace(name, self.name_map[name])
        
        # 2. 手机号 
        temp_text = self._process_regex(temp_text, PATTERNS["PHONE"], 
                                      lambda x: self.crypto.encrypt_fpe_integer(x, 11))
        
        # 3. 身份证
        temp_text = self._process_regex(temp_text, PATTERNS["ID_CARD"], 
                                      lambda x: self.crypto.encrypt_fpe_integer(x, 18))
        
        # 4. 银行卡
        temp_text = self._process_regex(temp_text, PATTERNS["CREDIT_CARD"], 
                                      lambda x: self.crypto.encrypt_fpe_integer(x, 16))
        
        # 5. 邮箱
        temp_text = self._process_regex(temp_text, PATTERNS["EMAIL"], 
                                      self.crypto.encrypt_fpe_string)
                                      
        return temp_text

    def decrypt_all(self, text):
        
        # 1. 邮箱
        text = self._process_regex(text, DECRYPT_PATTERNS["EMAIL"], 
                                 self.crypto.decrypt_fpe_string, mode='decrypt')
        
        # 2. 身份证 (18位)
        text = self._process_regex(text, DECRYPT_PATTERNS["ID_CARD_CIPHER"], 
                                 lambda x: self.crypto.decrypt_fpe_integer(x, 18), mode='decrypt')
        
        # 3. 银行卡 (16位)
        text = self._process_regex(text, DECRYPT_PATTERNS["CREDIT_CARD_CIPHER"], 
                                 lambda x: self.crypto.decrypt_fpe_integer(x, 16), mode='decrypt')
        
        # 4. 手机号 (11位) 
        text = self._process_regex(text, DECRYPT_PATTERNS["PHONE_CIPHER"], 
                                 lambda x: self.crypto.decrypt_fpe_integer(x, 11), mode='decrypt')
        
        # 5. 姓名还原
        for fake, real in self.reverse_name_map.items():
            text = text.replace(fake, real)
            
        return text