import streamlit as st
import base64
from config import SYSTEM_SALT
from crypto_engine import CryptoEngine
from data_processor import DataProcessor
from llm_client import LLMClient

st.set_page_config(page_title="大模型隐私计算网关", layout="wide", page_icon="🛡️")

st.title("🛡️ 大模型隐私计算网关 (MPC Gateway)")
st.markdown("""
> **系统简介：** 本系统实现了基于FPE (格式保留加密)的隐私保护代理。
> 支持对 手机号、身份证、银行卡、邮箱、人名 进行实时脱敏，确保敏感数据永远不会以此明文形式离开本地环境。
""")

with st.sidebar:
    st.header("安全初始化")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    st.subheader("密钥派生 (KDF)")
    user_password = st.text_input("输入主密码", type="password", help="使用 PBKDF2 算法派生密钥")
    
    if st.button("启动隐私加密"):
        if not user_password:
            st.error("设置加密密码！")
        else:
            try:
                engine = CryptoEngine(user_password, SYSTEM_SALT)
                st.session_state.processor = DataProcessor(engine)
                st.session_state.engine = engine
                st.session_state.active = True
                st.success("已就绪，等待输入！")
                st.info(f"生成密钥指纹: {base64.b64encode(engine.main_key[:6]).decode()}...")
            except Exception as e:
                st.error(f"初始化失败: {e}")

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.chat_input("请输入包含敏感信息的 Prompt...")

if user_input and st.session_state.get("active"):
    if not api_key:
        st.warning("请填写 API Key")
        st.stop()
        
    processor = st.session_state.processor
    llm = LLMClient(api_key)

    encrypted_prompt = processor.encrypt_all(user_input)
    
    with st.spinner("正在进行隐私计算推理..."):
        raw_response = llm.chat(encrypted_prompt)
        
    final_response = processor.decrypt_all(raw_response)
    
    log_entry = {"user": user_input, "bot": final_response}
    nonce, cipher, tag = st.session_state.engine.aes_encrypt_log(log_entry)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.info("原始输入")
        st.write(user_input)
        
    with col2:
        st.warning("LLM 视角 (密文)")
        st.code(encrypted_prompt, language="text")
        st.caption("LLM 仅能看到格式保留的密文，无法获取真实身份。")
        
    with col3:
        st.success("解密结果")
        st.write(final_response)

    with st.expander("查看 AES-GCM 加密审计日志 (Hex)"):
        st.text(f"Nonce: {nonce.hex()}")
        st.text(f"Tag:   {tag.hex()}")
        st.text(f"Cipher: {cipher.hex()[:50]}...")

elif user_input and not st.session_state.get("active"):
    st.error("请先在左侧输入密码启动加密！")