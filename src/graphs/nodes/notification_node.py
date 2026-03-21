"""
通知推送节点
功能：通过邮件、微信、飞书等渠道推送交易通知
"""
import os
import json
import smtplib
import ssl
import time
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid
from typing import Dict, Any, List
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from graphs.state import NotificationInput, NotificationOutput
from coze_workload_identity import Client
from cozeloop.decorator import observe


@observe
def send_email(
    subject: str,
    content: str,
    to_addrs: List[str]
) -> Dict[str, Any]:
    """
    发送邮件通知
    
    Args:
        subject: 邮件主题
        content: 邮件内容
        to_addrs: 收件人列表
    
    Returns:
        发送结果
    """
    try:
        # 获取邮件配置
        client = Client()
        email_credential = client.get_integration_credential("integration-email-imap-smtp")
        email_config = json.loads(email_credential)
        
        # 构建邮件
        html_content = f"""
        <html>
        <body>
            <h2 style="color: #333;">{subject}</h2>
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <pre style="white-space: pre-wrap; word-wrap: break-word;">{content}</pre>
            </div>
            <p style="color: #999; font-size: 12px;">
                发送时间: {formatdate(localtime=True)}<br>
                来源: 欧易量化交易系统
            </p>
        </body>
        </html>
        """
        
        msg = MIMEText(html_content, "html", "utf-8")
        msg["From"] = formataddr(("量化交易助手", email_config["account"]))
        msg["To"] = ", ".join(to_addrs)
        msg["Subject"] = Header(subject, "utf-8")
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()
        
        # 发送邮件
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        
        with smtplib.SMTP_SSL(
            email_config["smtp_server"],
            email_config["smtp_port"],
            context=ctx,
            timeout=30
        ) as server:
            server.ehlo()
            server.login(email_config["account"], email_config["auth_code"])
            server.sendmail(email_config["account"], to_addrs, msg.as_string())
            server.quit()
        
        return {"status": "success", "message": f"邮件已发送至 {len(to_addrs)} 位收件人"}
        
    except Exception as e:
        return {"status": "error", "message": f"邮件发送失败: {str(e)}"}


def notification_node(
    state: NotificationInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> NotificationOutput:
    """
    通知推送节点
    
    title: 通知推送
    desc: 通过邮件等多渠道推送交易通知
    integrations: 邮件
    """
    ctx = runtime.context
    
    try:
        channels = []
        success_count = 0
        
        # 获取通知配置
        notification_config = state.notification_config or {}
        
        # 发送邮件
        if notification_config.get("enable_email", True):
            email_recipients = notification_config.get("email_recipients", [])
            
            if email_recipients:
                result = send_email(
                    subject=f"[量化交易] {state.title}",
                    content=state.message,
                    to_addrs=email_recipients
                )
                
                if result.get("status") == "success":
                    channels.append("email")
                    success_count += 1
        
        # 判断是否成功
        success = success_count > 0
        
        return NotificationOutput(
            success=success,
            channels=channels,
            message=f"已通过 {len(channels)} 个渠道发送通知" if success else "通知发送失败"
        )
        
    except Exception as e:
        return NotificationOutput(
            success=False,
            channels=[],
            message=f"通知推送异常: {str(e)}"
        )
