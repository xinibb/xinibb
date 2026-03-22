"""
通知模块 - 消息推送

支持：
- 邮件通知
- 微信推送
- 飞书推送
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from datetime import datetime
import aiohttp
import asyncio


logger = logging.getLogger(__name__)


class NotificationManager:
    """
    通知管理器
    
    统一管理各种通知渠道
    """
    
    def __init__(
        self,
        email_config: Optional[Dict[str, str]] = None,
        wechat_webhook: Optional[str] = None,
        feishu_webhook: Optional[str] = None
    ):
        """
        初始化通知管理器
        
        Args:
            email_config: 邮件配置
            wechat_webhook: 微信机器人Webhook
            feishu_webhook: 飞书机器人Webhook
        """
        self.email_config = email_config
        self.wechat_webhook = wechat_webhook
        self.feishu_webhook = feishu_webhook
        self.logger = logging.getLogger(__name__)
        
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    # ==================== 邮件通知 ====================
    
    async def send_email(
        self,
        to: List[str],
        subject: str,
        content: str,
        html: bool = False
    ) -> bool:
        """
        发送邮件
        
        Args:
            to: 收件人列表
            subject: 主题
            content: 内容
            html: 是否为HTML格式
            
        Returns:
            是否发送成功
        """
        if not self.email_config:
            self.logger.warning("未配置邮件，跳过发送")
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender']
            msg['To'] = ', '.join(to)
            msg['Subject'] = subject
            
            # 添加正文
            if html:
                msg.attach(MIMEText(content, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP(
                self.email_config['smtp_server'],
                int(self.email_config.get('smtp_port', 587))
            ) as server:
                server.starttls()
                server.login(
                    self.email_config['sender'],
                    self.email_config['password']
                )
                server.sendmail(
                    self.email_config['sender'],
                    to,
                    msg.as_string()
                )
            
            self.logger.info(f"邮件发送成功: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"邮件发送失败: {e}")
            return False
    
    # ==================== 微信通知 ====================
    
    async def send_wechat(self, content: str) -> bool:
        """
        发送微信消息
        
        Args:
            content: 消息内容
            
        Returns:
            是否发送成功
        """
        if not self.wechat_webhook:
            self.logger.warning("未配置微信Webhook，跳过发送")
            return False
        
        try:
            session = await self._get_session()
            
            data = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
            
            async with session.post(self.wechat_webhook, json=data) as response:
                result = await response.json()
                
                if result.get("errcode") == 0:
                    self.logger.info("微信消息发送成功")
                    return True
                else:
                    self.logger.error(f"微信消息发送失败: {result}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"微信消息发送失败: {e}")
            return False
    
    # ==================== 飞书通知 ====================
    
    async def send_feishu(self, content: str, title: str = "交易通知") -> bool:
        """
        发送飞书消息
        
        Args:
            content: 消息内容
            title: 消息标题
            
        Returns:
            是否发送成功
        """
        if not self.feishu_webhook:
            self.logger.warning("未配置飞书Webhook，跳过发送")
            return False
        
        try:
            session = await self._get_session()
            
            data = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": title
                        },
                        "template": "blue"
                    },
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "tag": "plain_text",
                                "content": content
                            }
                        },
                        {
                            "tag": "div",
                            "text": {
                                "tag": "plain_text",
                                "content": f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        }
                    ]
                }
            }
            
            async with session.post(self.feishu_webhook, json=data) as response:
                result = await response.json()
                
                if result.get("StatusCode") == 0:
                    self.logger.info("飞书消息发送成功")
                    return True
                else:
                    self.logger.error(f"飞书消息发送失败: {result}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"飞书消息发送失败: {e}")
            return False
    
    # ==================== 综合通知 ====================
    
    async def notify_all(
        self,
        message: str,
        title: str = "交易通知",
        channels: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        多渠道通知
        
        Args:
            message: 消息内容
            title: 消息标题
            channels: 通知渠道列表（email/wechat/feishu），None则全部发送
            
        Returns:
            各渠道发送结果
        """
        results = {}
        
        # 默认所有渠道
        if channels is None:
            channels = ['wechat', 'feishu']
        
        tasks = []
        
        if 'email' in channels and self.email_config:
            tasks.append(('email', self.send_email(
                self.email_config.get('recipients', []),
                title,
                message
            )))
        
        if 'wechat' in channels:
            tasks.append(('wechat', self.send_wechat(message)))
        
        if 'feishu' in channels:
            tasks.append(('feishu', self.send_feishu(message, title)))
        
        # 并行发送
        for channel, task in tasks:
            try:
                result = await task
                results[channel] = result
            except Exception as e:
                self.logger.error(f"{channel} 通知失败: {e}")
                results[channel] = False
        
        return results
    
    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()
