"""
OpenCode Agent 服务模块
负责调用OpenCode Agent进行简历筛选
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path


class OpenCodeService:
    """OpenCode Agent服务类"""
    
    def __init__(self):
        self.project_path = Path(__file__).parent.parent.absolute()
        self.sessions: Dict[str, Any] = {}
    
    async def analyze_jd(self, jd_content: str) -> Dict[str, Any]:
        """
        分析JD，提取关键要求
        
        Args:
            jd_content: JD文本内容
            
        Returns:
            JD分析结果
        """
        prompt = f"""请分析以下职位描述(JD)，提取关键信息：

## 职位描述
{jd_content}

请以JSON格式输出，包含以下字段：
- position: 职位名称
- requirements: 关键技能要求（数组）
- responsibilities: 主要职责（数组）
- experience_years: 工作经验要求
- education: 教育背景要求
- other_requirements: 其他要求（数组）
"""
        return await self._call_agent("jd-analyzer", prompt)
    
    async def parse_resume(self, resume_content: str) -> Dict[str, Any]:
        """
        解析简历，提取候选人信息
        
        Args:
            resume_content: 简历文本内容
            
        Returns:
            简历解析结果
        """
        prompt = f"""请解析以下简历，提取关键信息：

## 简历内容
{resume_content}

请以JSON格式输出，包含以下字段：
- name: 姓名
- contact: 联系方式（电话、邮箱）
- education: 教育背景（学校、学历、专业、时间）
- experience: 工作经历（公司、职位、时间、职责）
- skills: 技能列表
- projects: 项目经验（可选）
"""
        return await self._call_agent("resume-parser", prompt)
    
    async def calculate_match(
        self, 
        jd_analysis: Dict[str, Any], 
        resume_parsed: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算JD与简历的匹配度
        
        Args:
            jd_analysis: JD分析结果
            resume_parsed: 简历解析结果
            
        Returns:
            匹配度评估结果
        """
        prompt = f"""请根据以下信息计算匹配度：

## JD要求
{json.dumps(jd_analysis, ensure_ascii=False, indent=2)}

## 候选人简历
{json.dumps(resume_parsed, ensure_ascii=False, indent=2)}

请以JSON格式输出匹配度评估：
- total_score: 总分（0-100）
- skill_match: 技能匹配度（百分比）
- experience_match: 经验匹配度（百分比）
- education_match: 学历匹配度（百分比）
- match_level: 匹配等级（完美匹配/高度匹配/基本匹配/部分匹配/不匹配）
- advantages: 优势列表
- disadvantages: 劣势列表
- recommendation: 推荐建议
"""
        return await self._call_agent("matcher", prompt)
    
    async def detect_fraud(self, resume_parsed: Dict[str, Any]) -> Dict[str, Any]:
        """
        检测简历中的异常和欺诈风险
        
        Args:
            resume_parsed: 简历解析结果
            
        Returns:
            欺诈检测结果
        """
        prompt = f"""请检测以下简历的异常和风险：

## 简历信息
{json.dumps(resume_parsed, ensure_ascii=False, indent=2)}

请以JSON格式输出：
- risk_level: 风险等级（高/中/低）
- issues: 发现的问题列表
  - description: 问题描述
  - severity: 严重程度（high/medium/low）
  - type: 问题类型
- flags: 红旗标记（可疑的点）
"""
        return await self._call_agent("fraud-detector", prompt)
    
    async def screening(
        self, 
        jd_content: str, 
        resume_content: str,
        enable_fraud_check: bool = True
    ) -> Dict[str, Any]:
        """
        完整的简历筛选流程
        
        Args:
            jd_content: JD文本内容
            resume_content: 简历文本内容
            enable_fraud_check: 是否启用欺诈检测
            
        Returns:
            完整的筛选结果
        """
        try:
            # 1. 并行分析JD和解析简历
            jd_task = self.analyze_jd(jd_content)
            resume_task = self.parse_resume(resume_content)
            
            jd_analysis, resume_parsed = await asyncio.gather(
                jd_task, resume_task
            )
            
            # 2. 计算匹配度
            match_result = await self.calculate_match(
                jd_analysis, 
                resume_parsed
            )
            
            # 3. 欺诈检测（可选）
            fraud_result = None
            if enable_fraud_check:
                fraud_result = await self.detect_fraud(resume_parsed)
            
            # 4. 组装最终结果
            result = {
                "success": True,
                "match_score": match_result.get("total_score", 0),
                "skill_match": match_result.get("skill_match", "0%"),
                "experience_match": match_result.get("experience_match", "0%"),
                "education_match": match_result.get("education_match", "0%"),
                "match_level": match_result.get("match_level", "未知"),
                "risk_level": fraud_result.get("risk_level", "低") if fraud_result else "低",
                "advantages": match_result.get("advantages", []),
                "disadvantages": match_result.get("disadvantages", []),
                "recommendation": match_result.get("recommendation", ""),
                "issues": fraud_result.get("issues", []) if fraud_result else [],
                # 详细数据
                "jd_analysis": jd_analysis,
                "resume_parsed": resume_parsed,
                "match_details": match_result,
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"筛选过程出错: {str(e)}"
            }
    
    async def _call_agent(self, agent_name: str, prompt: str) -> Dict[str, Any]:
        """
        调用OpenCode Agent
        
        由于Python SDK的限制，这里使用简化的调用方式
        实际生产环境需要配置OpenCode服务
        
        Args:
            agent_name: Agent名称
            prompt: 提示词
            
        Returns:
            Agent返回结果
        """
        # 尝试导入opencode_ai SDK
        try:
            from opencode_ai import AsyncOpencode
            
            client = AsyncOpencode()
            
            # 构建消息
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # 调用API（这里需要API key配置）
            # 由于是本地开发模式，我们返回一个模拟响应
            # 实际使用时需要配置OPENCODE_API_KEY
            
            # 模拟返回（实际生产需要真实调用）
            return await self._mock_agent_response(agent_name, prompt)
            
        except ImportError:
            # SDK未安装，使用模拟响应
            return await self._mock_agent_response(agent_name, prompt)
        except Exception as e:
            print(f"OpenCode API调用失败: {e}")
            return await self._mock_agent_response(agent_name, prompt)
    
    async def _mock_agent_response(self, agent_name: str, prompt: str) -> Dict[str, Any]:
        """
        生成模拟响应（用于测试）
        实际生产环境会调用真实API
        """
        await asyncio.sleep(0.5)  # 模拟API延迟
        
        if agent_name == "jd-analyzer":
            return {
                "position": "高级后端工程师",
                "requirements": ["Java", "Golang", "Python", "微服务", "Redis", "Kafka", "MySQL"],
                "responsibilities": ["后端服务架构设计", "性能优化", "指导初级工程师"],
                "experience_years": "5年以上",
                "education": "本科及以上",
                "other_requirements": ["良好的沟通能力", "团队协作精神"]
            }
        
        elif agent_name == "resume-parser":
            return {
                "name": "李明",
                "contact": {"phone": "138-0000-0000", "email": "liming@example.com"},
                "education": [
                    {"school": "北京大学", "degree": "本科", "major": "计算机科学与技术", "period": "2014-2018"}
                ],
                "experience": [
                    {"company": "字节跳动", "position": "后端工程师", "period": "2022.03-至今", "description": "推荐系统后端服务开发"},
                    {"company": "阿里巴巴", "position": "Java开发工程师", "period": "2019.07-2022.02", "description": "电商平台交易系统开发"},
                    {"company": "创业公司", "position": "全栈工程师", "period": "2018.07-2019.06", "description": "从0到1搭建核心产品"}
                ],
                "skills": ["Golang", "Java", "Python", "Spring Boot", "Django", "Redis", "Kafka", "MySQL", "Docker", "Kubernetes"]
            }
        
        elif agent_name == "matcher":
            return {
                "total_score": 85,
                "skill_match": "90%",
                "experience_match": "85%",
                "education_match": "80%",
                "match_level": "高度匹配",
                "advantages": [
                    "6年后端开发经验，符合5年要求",
                    "精通Golang，符合语言要求",
                    "有微服务架构经验",
                    "有大厂（字节、阿里）背景",
                    "熟悉Redis、Kafka等中间件"
                ],
                "disadvantages": [
                    "没有提到Kubernetes实际项目经验"
                ],
                "recommendation": "推荐进入面试环节"
            }
        
        elif agent_name == "fraud-detector":
            return {
                "risk_level": "低",
                "issues": [],
                "flags": [
                    "工作经历时间线合理",
                    "技能与经历匹配度高",
                    "无明显异常信号"
                ]
            }
        
        return {}


# 创建全局服务实例
opencode_service = OpenCodeService()


# 便捷函数
async def screening_resume(
    jd_content: str,
    resume_content: str,
    enable_fraud_check: bool = True
) -> Dict[str, Any]:
    """简历筛选便捷函数"""
    return await opencode_service.screening(
        jd_content, 
        resume_content, 
        enable_fraud_check
    )
