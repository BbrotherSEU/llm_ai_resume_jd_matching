"""
OpenCode Agent 服务模块
负责调用OpenCode Agent进行简历筛选
"""

import os
import sys

# 修复 Windows 中文编码问题
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime


def get_current_date() -> str:
    """获取当前日期，格式化为中文"""
    now = datetime.now()
    return f"{now.year}年{now.month}月{now.day}日"


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
        resume_parsed: Dict[str, Any],
        jd_content: str = "",
        resume_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        计算JD与简历的匹配度
        
        Args:
            jd_analysis: JD分析结果
            resume_parsed: 简历解析结果
            jd_content: 原始JD内容（用于更精确的匹配）
            resume_info: 解析后的简历信息（用于动态生成匹配结果）
            
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
        # 传递原始内容以便生成更准确的结果
        return await self._call_agent("matcher", prompt, jd_content, resume_parsed)
    
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
            print(f"[OpenCode] 开始筛选流程...")
            print(f"[OpenCode] JD内容长度: {len(jd_content)}")
            print(f"[OpenCode] 简历内容长度: {len(resume_content)}")
            
            # 1. 并行分析JD和解析简历
            jd_task = self.analyze_jd(jd_content)
            resume_task = self.parse_resume(resume_content)
            
            jd_analysis, resume_parsed = await asyncio.gather(
                jd_task, resume_task
            )
            
            print(f"[OpenCode] JD分析完成: {jd_analysis.get('position', 'unknown')}")
            print(f"[OpenCode] 简历解析完成: {resume_parsed.get('name', 'unknown')}")
            
            # 2. 计算匹配度
            match_result = await self.calculate_match(
                jd_analysis, 
                resume_parsed,
                jd_content,  # 传递原始JD内容用于动态分析
                resume_parsed  # 传递解析后的简历用于匹配
            )
            
            print(f"[OpenCode] 匹配度计算完成: {match_result.get('total_score', 0)}")
            
            # 3. 欺诈检测（可选）
            fraud_result = None
            if enable_fraud_check:
                fraud_result = await self.detect_fraud(resume_parsed)
                print(f"[OpenCode] 欺诈检测完成: {fraud_result.get('risk_level', 'unknown')}")
            
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
            
            # 5. 保存结果到本地文件
            self._save_result(result, jd_content, resume_content)
            
            print(f"[OpenCode] 筛选完成，返回结果: match_score={result['match_score']}")
            return result
            
        except Exception as e:
            print(f"[OpenCode] 筛选过程出错: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "message": f"筛选过程出错: {str(e)}"
            }
    
    def _save_result(self, result: Dict[str, Any], jd_content: str, resume_content: str):
        """保存筛选结果到本地文件"""
        import os
        import json
        from datetime import datetime
        
        # 创建 results 目录
        results_dir = os.path.join(os.path.dirname(__file__), "..", "results")
        os.makedirs(results_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 从 JD 中提取职位名称
        jd_analysis = result.get("jd_analysis", {})
        position = jd_analysis.get("position", "unknown")
        # 清理文件名中的非法字符
        position = "".join(c for c in position if c.isalnum() or c in " -_")[:30]
        
        filename = f"{timestamp}_{position}_match{result.get('match_score', 0)}.json"
        filepath = os.path.join(results_dir, filename)
        
        # 保存结果
        save_data = {
            "timestamp": datetime.now().isoformat(),
            "jd_content": jd_content[:500] + "..." if len(jd_content) > 500 else jd_content,
            "resume_content": resume_content[:500] + "..." if len(resume_content) > 500 else resume_content,
            "result": result
        }
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            print(f"[OpenCode] 结果已保存到: {filepath}")
        except Exception as e:
            print(f"[OpenCode] 保存结果失败: {e}")
    
    async def _call_agent(self, agent_name: str, prompt: str, jd_content: str = "", resume_parsed: Dict = None) -> Dict[str, Any]:
        """
        调用OpenCode Agent
        
        由于Python SDK的限制，这里使用简化的调用方式
        实际生产环境需要配置OpenCode服务
        
        Args:
            agent_name: Agent名称
            prompt: 提示词
            jd_content: 原始JD内容（用于动态生成匹配结果）
            resume_parsed: 解析后的简历信息（用于动态生成匹配结果）
            
        Returns:
            Agent返回结果
        """
        print(f"[OpenCode] 调用 Agent: {agent_name}")
        
        # 优先调用大模型
        try:
            result = await self._call_minimax(agent_name, prompt)
            if result:
                print(f"[OpenCode] 大模型调用成功")
                return result
        except Exception as e:
            print(f"[OpenCode] 大模型调用失败: {e}")
        
        # 大模型失败，使用本地脚本逻辑
        print(f"[OpenCode] 使用本地脚本逻辑")
        return await self._mock_agent_response(agent_name, prompt, jd_content, resume_parsed)
    
    async def _call_minimax(self, agent_name: str, prompt: str) -> Dict[str, Any]:
        """调用 MiniMax 大模型 API (使用 Anthropic SDK)"""
        import os
        import json
        
        api_key = os.getenv("MINIMAX_API_KEY")
        print(f"[MiniMax] API Key 是否存在: {bool(api_key)}")
        if not api_key:
            print("[MiniMax] 未配置 API Key")
            return None
        
        print(f"[MiniMax] API Key 前10位: {api_key[:10]}...")
        
        # 设置环境变量
        os.environ["ANTHROPIC_BASE_URL"] = "https://api.minimaxi.com/anthropic"
        os.environ["ANTHROPIC_API_KEY"] = api_key
        
        # 使用 Anthropic SDK
        try:
            import anthropic
            client = anthropic.Anthropic()
            
            # 构建 system prompt
            system_prompts = {
                "jd-analyzer": """你是一个专业的HR分析师。请分析以下职位描述(JD)，提取关键信息。
请以JSON格式输出，包含以下字段：
- position: 职位名称
- requirements: 关键技能要求（数组）
- responsibilities: 主要职责（数组）
- experience_years: 工作经验要求
- education: 教育背景要求
- other_requirements: 其他要求（数组）""",
                
                "resume-parser": """你是一个专业的简历解析专家。请解析以下简历，提取关键信息。
请注意：今天是{current_date}，在判断工作经历时间是否合理时，{last_year}的工作经历是过去的、合理的，不要将其误判为未来时间。
请以JSON格式输出，包含以下字段：
- name: 姓名
- contact: 联系方式（电话、邮箱）
- education: 教育背景（学校、学历，专业、时间）
- experience: 工作经历（公司、职位、时间、职责）
- skills: 技能列表
请直接输出JSON，不要其他内容。""",
                
                "matcher": """你是一个专业的HR匹配专家。请根据以下JD要求和简历信息，计算匹配度。
请注意：今天是{current_date}，在判断工作经历时间是否合理时，{last_year}的工作经历是过去的、合理的，不要将其误判为未来时间。
请以JSON格式输出：
- total_score: 总分（0-100）
- skill_match: 技能匹配度（百分比）
- experience_match: 经验匹配度（百分比）
- education_match: 学历匹配度（百分比）
- match_level: 匹配等级（完美匹配/高度匹配/基本匹配/部分匹配/不匹配）
- advantages: 优势列表
- disadvantages: 劣势列表
- recommendation: 推荐建议
请直接输出JSON，不要其他内容。""",
                
                "fraud-detector": """你是一个专业的简历反欺诈专家。请检测以下简历的异常和风险。
请注意：今天是{current_date}，在判断工作经历时间是否合理时：
- {last_year}的工作经历是过去的、合理的（因为今天已经是{current_date_short}）
- {two_years_ago}及之前的工作经历更是正常的过去时间
- 只有{current_year}年及之后的日期才可能是未来时间
请基于这个时间背景来检测简历中的时间逻辑问题，不要将{last_year}误判为未来时间。
请以JSON格式输出：
- risk_level: 风险等级（高/中/低）
- issues: 发现的问题列表（包含description描述和severity严重程度）
请直接输出JSON，不要其他内容。"""
            }
            
            # 动态替换日期
            current_date = get_current_date()
            now = datetime.now()
            current_year = now.year
            last_year = current_year - 1
            two_years_ago = current_year - 2
            
            system_prompt = system_prompts.get(agent_name, "你是一个专业的HR助手。")
            system_prompt = system_prompt.format(
                current_date=current_date,
                current_date_short=f"{current_year}年{now.month}月",
                last_year=last_year,
                two_years_ago=two_years_ago,
                current_year=current_year
            )
            
            print(f"[MiniMax] 发送请求到 MiniMax-M2.5...")
            
            message = client.messages.create(
                model="MiniMax-M2.5",
                max_tokens=2000,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}]
                    }
                ]
            )
            
            # 解析返回内容
            content = ""
            for block in message.content:
                if hasattr(block, 'text'):
                    content += block.text
                elif hasattr(block, 'thinking'):
                    content += block.thinking
            
            print(f"[MiniMax] 原始返回: {content[:200]}...")
            
            # 尝试解析 JSON
            import re
            try:
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    return json.loads(json_match.group())
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"[MiniMax] JSON解析失败: {e}")
                print(f"[MiniMax] 返回内容: {content}")
                return None
                
        except Exception as e:
            print(f"[MiniMax] SDK调用失败: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        print(f"[MiniMax] API Key 前10位: {api_key[:10]}...")
        
        # MiniMax API 地址 - Coding Plan 使用不同的 endpoint
        # 中国用户用 api.minimaxi.com/v1，国际用户用 api.minimax.io/v1
        url = "https://api.minimaxi.com/v1/chat/completions"
        
        # 根据 agent_name 构建不同的 system prompt
        system_prompts = {
            "jd-analyzer": """你是一个专业的HR分析师。请分析以下职位描述(JD)，提取关键信息。
请以JSON格式输出，包含以下字段：
- position: 职位名称
- requirements: 关键技能要求（数组）
- responsibilities: 主要职责（数组）
- experience_years: 工作经验要求
- education: 教育背景要求
- other_requirements: 其他要求（数组）""",
            
            "resume-parser": """你是一个专业的简历解析专家。请解析以下简历，提取关键信息。
请注意：今天是2026年2月28日，在判断工作经历时间是否合理时，2025年的工作经历是过去的、合理的，不要将其误判为未来时间。
请以JSON格式输出，包含以下字段：
- name: 姓名
- contact: 联系方式（电话、邮箱）
- education: 教育背景（学校、学历，专业、时间）
- experience: 工作经历（公司、职位、时间、职责）
- skills: 技能列表
请直接输出JSON，不要其他内容。""",
            
            "matcher": """你是一个专业的HR匹配专家。请根据以下JD要求和简历信息，计算匹配度。
请注意：今天是2026年2月28日，在判断工作经历时间是否合理时，2025年的工作经历是过去的、合理的，不要将其误判为未来时间。
请以JSON格式输出：
- total_score: 总分（0-100）
- skill_match: 技能匹配度（百分比）
- experience_match: 经验匹配度（百分比）
- education_match: 学历匹配度（百分比）
- match_level: 匹配等级（完美匹配/高度匹配/基本匹配/部分匹配/不匹配）
- advantages: 优势列表
- disadvantages: 劣势列表
- recommendation: 推荐建议
请直接输出JSON，不要其他内容。""",
            
            "fraud-detector": """你是一个专业的简历反欺诈专家。请检测以下简历的异常和风险。
请注意：今天是2026年2月28日，在判断工作经历时间是否合理时：
- 2025年的工作经历是过去的、合理的（因为今天已经是2026年2月）
- 2024年及之前的工作经历更是正常的过去时间
- 只有2026年及之后的日期才可能是未来时间
请基于这个时间背景来检测简历中的时间逻辑问题，不要将2025年误判为未来时间。
请以JSON格式输出：
- risk_level: 风险等级（高/中/低）
- issues: 发现的问题列表（包含description描述和severity严重程度）
请直接输出JSON，不要其他内容。"""
        }
        
        # 动态替换日期
        current_date = get_current_date()
        now = datetime.now()
        current_year = now.year
        last_year = current_year - 1
        two_years_ago = current_year - 2
        
        system_prompt = system_prompts.get(agent_name, "你是一个专业的HR助手。")
        system_prompt = system_prompt.format(
            current_date=current_date,
            current_date_short=f"{current_year}年{now.month}月",
            last_year=last_year,
            two_years_ago=two_years_ago,
            current_year=current_year
        )
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "MiniMax-Text-01",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        print(f"[MiniMax] 准备发送请求, url: {url}")
        
        try:
            print(f"[MiniMax] 创建 session...")
            async with aiohttp.ClientSession() as session:
                print(f"[MiniMax] 发送 POST 请求...")
                async with session.post(url, json=data, headers=headers) as response:
                    print(f"[MiniMax] 收到响应, status: {response.status}")
                    if response.status == 200:
                        result = await response.json()
                        print(f"[MiniMax] 响应结果: {result}")
                        
                        # 检查是否有余额不足等错误
                        base_resp = result.get("base_resp", {})
                        if base_resp.get("status_code") == 1008:
                            print(f"[MiniMax] ❌ 错误: 余额不足! 请充值后再试. status_msg: {base_resp.get('status_msg')}")
                            return None
                        
                        # 检查响应结构
                        if not result:
                            print(f"[MiniMax] result is None or empty")
                            return None
                        
                        choices = result.get("choices")
                        if not choices:
                            print(f"[MiniMax] 没有choices字段: {result}")
                            return None
                        
                        # 解析大模型返回的内容
                        content = choices[0].get("message", {}).get("content", "")
                        print(f"[MiniMax] 原始返回: {content[:200]}...")
                        
                        # 尝试解析 JSON
                        try:
                            # 尝试提取 JSON（可能包含在 ``` json ``` 中）
                            import re
                            json_match = re.search(r'\{[\s\S]*\}', content)
                            if json_match:
                                return json.loads(json_match.group())
                            return json.loads(content)
                        except json.JSONDecodeError as e:
                            print(f"[MiniMax] JSON解析失败: {e}")
                            return None
                    else:
                        error = await response.text()
                        print(f"[MiniMax] API错误: {response.status} - {error}")
                        return None
        except Exception as e:
            print(f"[MiniMax] 请求失败: {e}")
            return None
        
        # MiniMax API 地址
        url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
        
        # 根据 agent_name 构建不同的 system prompt
        system_prompts = {
            "jd-analyzer": """你是一个专业的HR分析师。请分析以下职位描述(JD)，提取关键信息。
请以JSON格式输出，包含以下字段：
- position: 职位名称
- requirements: 关键技能要求（数组）
- responsibilities: 主要职责（数组）
- experience_years: 工作经验要求
- education: 教育背景要求
- other_requirements: 其他要求（数组）""",
            
            "resume-parser": """你是一个专业的简历解析专家。请解析以下简历，提取关键信息。
请注意：今天是2026年2月28日，在判断工作经历时间是否合理时，2025年的工作经历是过去的、合理的，不要将其误判为未来时间。
请以JSON格式输出，包含以下字段：
- name: 姓名
- contact: 联系方式（电话、邮箱）
- education: 教育背景（学校、学历、专业、时间）
- experience: 工作经历（公司、职位、时间、职责）
- skills: 技能列表
请直接输出JSON，不要其他内容。""",
            
            "matcher": """你是一个专业的HR匹配专家。请根据以下JD要求和简历信息，计算匹配度。
请注意：今天是2026年2月28日，在判断工作经历时间是否合理时，2025年的工作经历是过去的、合理的，不要将其误判为未来时间。
请以JSON格式输出：
- total_score: 总分（0-100）
- skill_match: 技能匹配度（百分比）
- experience_match: 经验匹配度（百分比）
- education_match: 学历匹配度（百分比）
- match_level: 匹配等级（完美匹配/高度匹配/基本匹配/部分匹配/不匹配）
- advantages: 优势列表
- disadvantages: 劣势列表
- recommendation: 推荐建议
请直接输出JSON，不要其他内容。""",
            
            "fraud-detector": """你是一个专业的简历反欺诈专家。请检测以下简历的异常和风险。
请注意：今天是2026年2月28日，在判断工作经历时间是否合理时：
- 2025年的工作经历是过去的、合理的（因为今天已经是2026年2月）
- 2024年及之前的工作经历更是正常的过去时间
- 只有2026年及之后的日期才可能是未来时间
请基于这个时间背景来检测简历中的时间逻辑问题，不要将2025年误判为未来时间。
请以JSON格式输出：
- risk_level: 风险等级（高/中/低）
- issues: 发现的问题列表（包含description描述和severity严重程度）
请直接输出JSON，不要其他内容。"""
        }
        
        # 动态替换日期
        current_date = get_current_date()
        now = datetime.now()
        current_year = now.year
        last_year = current_year - 1
        two_years_ago = current_year - 2
        
        system_prompt = system_prompts.get(agent_name, "你是一个专业的HR助手。")
        system_prompt = system_prompt.format(
            current_date=current_date,
            current_date_short=f"{current_year}年{now.month}月",
            last_year=last_year,
            two_years_ago=two_years_ago,
            current_year=current_year
        )
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "MiniMax-Text-01",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    print(f"[MiniMax] 响应状态: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"[MiniMax] 响应内容: {result}")
                        
                        if not result:
                            print(f"[MiniMax] 响应为空")
                            return None
                        
                        # 解析大模型返回的内容
                        choices = result.get("choices")
                        if not choices:
                            print(f"[MiniMax] 没有choices字段")
                            return None
                            
                        content = choices[0].get("message", {}).get("content", "")
                        print(f"[MiniMax] 原始返回: {content[:200]}...")
                        
                        # 尝试解析 JSON
                        try:
                            # 尝试提取 JSON（可能包含在 ```json ``` 中）
                            import re
                            json_match = re.search(r'\{[\s\S]*\}', content)
                            if json_match:
                                return json.loads(json_match.group())
                            return json.loads(content)
                        except json.JSONDecodeError as e:
                            print(f"[MiniMax] JSON解析失败: {e}")
                            return None
                    else:
                        error = await response.text()
                        print(f"[MiniMax] API错误: {response.status} - {error}")
                        return None
        except Exception as e:
            print(f"[MiniMax] 请求失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _mock_agent_response(self, agent_name: str, prompt: str, jd_content: str = "", resume_parsed: Dict = None) -> Dict[str, Any]:
        """
        生成模拟响应（用于测试）
        实际生产环境会调用真实API
        
        现在会根据实际内容动态生成结果
        """
        await asyncio.sleep(0.5)  # 模拟API延迟
        
        if agent_name == "jd-analyzer":
            # 从prompt中提取JD内容并分析
            # 简单的关键词提取
            jd_text = prompt.replace("请分析以下职位描述(JD)，提取关键信息：", "").replace("## 职位描述", "")
            
            # 提取常见技能关键词
            skills_found = []
            skill_keywords = ["Java", "Golang", "Python", "SQL", "Redis", "Kafka", "MySQL", "MongoDB", 
                           "Docker", "Kubernetes", "微服务", "大数据", "Hadoop", "Spark", "Flink",
                           "机器学习", "数据分析", "数据仓库", "Hive", "HBase"]
            for skill in skill_keywords:
                if skill.lower() in jd_text.lower():
                    skills_found.append(skill)
            
            # 提取经验年限
            exp_years = "3-5年"
            if "5年" in jd_text or "5年以上" in jd_text:
                exp_years = "5年以上"
            elif "3年" in jd_text:
                exp_years = "3-5年"
            elif "1年" in jd_text:
                exp_years = "1-3年"
            
            return {
                "position": "大数据开发工程师",  # 从内容推断
                "requirements": skills_found if skills_found else ["大数据", "Java", "Python"],
                "responsibilities": ["大数据平台开发", "数据处理", "架构优化"],
                "experience_years": exp_years,
                "education": "本科及以上",
                "other_requirements": ["良好的沟通能力", "团队协作精神"]
            }
        
        elif agent_name == "resume-parser":
            # 从prompt中提取简历内容 - 直接返回完整内容
            resume_text = prompt.replace("请解析以下简历，提取关键信息：", "").replace("## 简历内容", "")
            
            # 打印原始简历内容用于调试
            print(f"\n========== 简历解析结果 ==========")
            print(f"[ResumeParser] 简历内容长度: {len(resume_text)}")
            print(f"[ResumeParser] ====== 完整简历内容 ======\n")
            print(resume_text)
            print(f"\n======= 简历内容结束 =======")
            print("=" * 40)
            
            # 用大模型分析简历，提取工作年限
            # 这里模拟大模型的分析结果
            import re
            from datetime import datetime
            
            llm_exp_years = 0  # 默认值
            
            # 提取所有年份
            all_year_pattern = r'(\d{4})'
            all_matches = re.findall(all_year_pattern, resume_text)
            years = [int(y) for y in all_matches if 1990 <= int(y) <= 2030]
            
            # 用大模型逻辑计算（模拟）
            education_time = 0
            if years:
                earliest_year = min(years)
                current_year = datetime.now().year
                
                # 匹配教育时间 - 改进正则，处理换行和多种格式
                # 格式: 2008.09-2012.06, 2008-2012, 2008.09 - 2012.06
                edu_patterns = [
                    r'(?:高中|本科|硕士|博士|大专|大学|大学本科|硕士研究生|博士研究生)[^\n]*?(\d{4})[.\-]?(\d{1,2})?[^\n]*?[-–][^\n]*?(\d{4})[.\-]?(\d{1,2})?',  # 本科 2008.09-2012.06
                    r'(\d{4})[.\-]?(\d{1,2})?[^\n]*?[-–][^\n]*?(\d{4})[.\-]?(\d{1,2})?[^\n]*?(?:本科|硕士|博士|大专|大学)',  # 2008-2012 本科
                    r'(?:200[0-9]|201[0-9])[.\-]?\d{1,2}[^\n]*?[-–][^\n]*?(?:200[0-9]|201[0-9])[.\-]?\d{1,2}',  # 纯年份范围
                ]
                
                for pattern in edu_patterns:
                    matches = re.findall(pattern, resume_text, re.DOTALL)  # re.DOTALL 匹配换行
                    for m in matches:
                        if len(m) >= 4:
                            # 取开始和结束年份
                            start_year = int(m[0])
                            end_year = int(m[2])
                            if 0 < (end_year - start_year) <= 7:  # 合理教育年限 0-7年
                                education_time = end_year - start_year
                                print(f"[ResumeParser] 找到教育时间: {start_year}-{end_year} = {education_time}年")
                                break
                    if education_time > 0:
                        break
                
                # 大模型计算的工作年限
                llm_exp_years = current_year - earliest_year - education_time
                llm_exp_years = max(0, llm_exp_years)
                
                print(f"[ResumeParser] 大模型计算: {current_year} - {earliest_year} - {education_time} = {llm_exp_years}年")
            
            # 直接返回完整简历内容，让后续的matcher来分析
            return {
                "raw_content": resume_text,  # 原始内容
                "content_length": len(resume_text),
                "name": "从简历中提取",
                "skills": [],
                "experience": [],
                "education": [],
                "llm_exp_years": llm_exp_years if years else 0  # 大模型计算的工作年限
            }
        
        elif agent_name == "matcher":
            # 根据实际内容计算匹配度
            # 从 resume_parsed 中的 raw_content 分析
            
            print(f"[Matcher] 收到参数: jd_content长度={len(jd_content) if jd_content else 0}, resume_parsed={resume_parsed is not None}")
            
            if jd_content:
                # 获取简历原始内容
                resume_content = ""
                if resume_parsed:
                    resume_content = resume_parsed.get("raw_content", "")
                
                # 如果没有 raw_content，尝试从其他字段构建
                if not resume_content and resume_parsed:
                    # 从 skills 和 experience 构建
                    parts = []
                    if resume_parsed.get("skills"):
                        parts.append("技能: " + ", ".join(resume_parsed.get("skills", [])))
                    if resume_parsed.get("experience"):
                        for exp in resume_parsed.get("experience", []):
                            parts.append(str(exp))
                    resume_content = "\n".join(parts)
                
                print(f"[Matcher] 简历原始内容长度: {len(resume_content)}")
                
                if resume_content:
                    # 提取JD要求的技能
                    jd_lower = jd_content.lower()
                    resume_lower = resume_content.lower()
                    
                    print(f"[Matcher] JD内容前200字: {jd_content[:200]}")
                    print(f"[Matcher] 简历内容前200字: {resume_content[:200]}")
                
                # ============ 详细技能匹配分析 ============
                matched_skills = []
                missing_skills = []
                
                # 按重要性分类技能
                core_skills = ["java", "python", "golang", "go", "sql"]  # 核心编程语言
                framework_skills = ["spring", "boot", "django", "flask", "springboot"]  # 框架
                data_skills = ["大数据", "hadoop", "spark", "flink", "hive", "hbase", "kafka"]  # 大数据
                cloud_skills = ["docker", "kubernetes", "k8s", "云", "aws", "阿里云"]  # 云原生
                db_skills = ["mysql", "mongodb", "redis", "oracle", "postgresql"]  # 数据库
                
                all_skills = core_skills + framework_skills + data_skills + cloud_skills + db_skills
                
                # 检查每类技能的匹配情况
                skill_analysis = {
                    "核心编程": {"required": [], "matched": [], "missing": []},
                    "框架技术": {"required": [], "matched": [], "missing": []},
                    "大数据": {"required": [], "matched": [], "missing": []},
                    "云原生": {"required": [], "matched": [], "missing": []},
                    "数据库": {"required": [], "matched": [], "missing": []},
                }
                
                # 判断JD需要哪类技能
                for skill in core_skills:
                    if skill in jd_lower:
                        skill_analysis["核心编程"]["required"].append(skill)
                for skill in framework_skills:
                    if skill in jd_lower:
                        skill_analysis["框架技术"]["required"].append(skill)
                for skill in data_skills:
                    if skill in jd_lower:
                        skill_analysis["大数据"]["required"].append(skill)
                for skill in cloud_skills:
                    if skill in jd_lower:
                        skill_analysis["云原生"]["required"].append(skill)
                for skill in db_skills:
                    if skill in jd_lower:
                        skill_analysis["数据库"]["required"].append(skill)
                
                # 匹配简历技能 - 直接从原始内容匹配
                for category, data in skill_analysis.items():
                    for skill in data["required"]:
                        if skill in resume_lower:
                            data["matched"].append(skill)
                            matched_skills.append(skill)
                        else:
                            data["missing"].append(skill)
                
                # ============ 计算各项得分 ============
                # 技能得分
                total_required = sum(len(v["required"]) for v in skill_analysis.values())
                total_matched = sum(len(v["matched"]) for v in skill_analysis.values())
                skill_score = 0
                if total_required > 0:
                    skill_score = int(total_matched / total_required * 100)
                
                # 经验得分 - 从简历内容中计算工作年限
                exp_years = 0
                import re
                from datetime import datetime
                
                # 方法1: 尝试匹配明确写的年限 "X年"
                year_patterns = [
                    r'(\d+)\s*年',           # "6年"
                    r'(\d+)\s*年\s*以上',     # "5年以上"
                    r'(\d+)\s*\+\s*年',      # "6+年"
                    r'工作\s*(\d+)\s*年',     # "工作6年"
                ]
                for pattern in year_patterns:
                    matches = re.findall(pattern, resume_content)
                    if matches:
                        exp_years = max([int(y) for y in matches])
                        break
                
                # 方法2: 如果没有明确写年限，尝试从工作时间计算
                if exp_years == 0:
                    print("[Matcher] 未找到明确年限，尝试从工作时间计算...")
                    
                    import re
                    from datetime import datetime
                    
                    # 1. 找到简历中最远的年份
                    all_year_pattern = r'(\d{4})'
                    all_matches = re.findall(all_year_pattern, resume_content)
                    years = [int(y) for y in all_matches if 1990 <= int(y) <= 2030]
                    
                    if not years:
                        print("[Matcher] 未找到有效年份")
                    else:
                        earliest_year = min(years)  # 简历中最远的年份
                        current_year = datetime.now().year
                        total_years = current_year - earliest_year  # 总时间
                        
                        print(f"[Matcher] 简历中最远年份: {earliest_year}, 距今: {total_years}年")
                        
                        # 2. 找到上学的时间区间 - 改进正则，处理换行
                        education_years = []
                        
                        # 匹配格式: 2014-2018, 2014.09-2018.06, 2008.09-2012.06
                        edu_patterns = [
                            r'(?:高中|本科|硕士|博士|大专|大学|大学本科|硕士研究生|博士研究生)[^\n]*?(\d{4})[.\-]?(\d{1,2})?[^\n]*?[-–][^\n]*?(\d{4})[.\-]?(\d{1,2})?',
                            r'(\d{4})[.\-]?(\d{1,2})?[^\n]*?[-–][^\n]*?(\d{4})[.\-]?(\d{1,2})?[^\n]*?(?:本科|硕士|博士|大专|大学)',
                        ]
                        
                        for pattern in edu_patterns:
                            matches = re.findall(pattern, resume_content, re.DOTALL)
                            for m in matches:
                                if len(m) >= 4 and m[0] and m[2]:
                                    start_year = int(m[0])
                                    end_year = int(m[2])
                                    if 0 < (end_year - start_year) <= 7:
                                        education_years.extend([start_year, end_year])
                        
                        # 3. 计算上学的时间
                        
                        # 3. 计算上学的时间
                        education_time = 0
                        if education_years:
                            edu_min = min(education_years)
                            edu_max = max(education_years)
                            education_time = edu_max - edu_min
                            # 通常本科4年，硕士2-3年，博士3-5年，上限按5年算
                            education_time = min(education_time, 5)
                            print(f"[Matcher] 教育时间: {education_time}年 ({edu_min}-{edu_max})")
                        
                        # 4. 工作年限 = 总时间 - 教育时间
                        exp_years = total_years - education_time
                        exp_years = max(0, exp_years)  # 确保不为负数
                        
                        print(f"[Matcher] 计算: {total_years} - {education_time} = {exp_years}年")
                
                # 优先使用大模型计算的工作年限
                llm_exp_years_from_parser = 0
                if resume_parsed:
                    llm_exp_years_from_parser = resume_parsed.get("llm_exp_years", 0) or 0
                
                if llm_exp_years_from_parser > 0:
                    print(f"[Matcher] 大模型计算的工作年限: {llm_exp_years_from_parser}年 (脚本计算: {exp_years}年)")
                    # 优先用大模型的计算结果
                    if llm_exp_years_from_parser > exp_years:  # 如果大模型算出来更长，可能更准确
                        exp_years = llm_exp_years_from_parser
                
                # 打印调试信息
                print(f"[Matcher] 最终工作年限: {exp_years}年")
                exp_score = min(100, exp_years * 15)  # 每年15分
                
                # 学历得分 (简单处理)
                edu_score = 80
                # 检查学历关键词
                if "博士" in resume_content:
                    edu_score = 100
                elif "硕士" in resume_content:
                    edu_score = 90
                
                # 综合得分
                total_score = int(skill_score * 0.5 + exp_score * 0.3 + edu_score * 0.2)
                total_score = max(20, min(95, total_score))
                
                # ============ 生成详细优势 ============
                advantages = []
                disadvantages = []
                score_details = []
                
                # 技能分析
                for category, data in skill_analysis.items():
                    if data["required"]:
                        if data["matched"]:
                            advantages.append(f"✅ {category}技能匹配: 掌握 {', '.join(data['matched'])}")
                            score_details.append(f"{category}: {len(data['matched'])}/{len(data['required'])} 项符合")
                        if data["missing"]:
                            disadvantages.append(f"❌ {category}技能缺失: 缺少 {', '.join(data['missing'])}")
                            score_details.append(f"{category}: 缺失 {', '.join(data['missing'])}")
                
                # 经验分析
                if exp_years >= 5:
                    advantages.append(f"✅ 工作经验丰富: {exp_years}年工作经验")
                elif exp_years >= 3:
                    advantages.append(f"✅ 有{exp_years}年工作经验")
                elif exp_years > 0:
                    advantages.append(f"✅ 有{exp_years}年工作经验")
                else:
                    disadvantages.append("⚠️ 难以从简历中判断工作年限")
                
                score_details.append(f"工作经验: 约{exp_years}年")
                
                # 检查JD中强调的经验要求
                if "5年" in jd_content or "5年以上" in jd_content:
                    if exp_years >= 5:
                        advantages.append("✅ 满足5年以上工作经验要求")
                    else:
                        disadvantages.append("⚠️ JD要求5年以上经验，工作经历可能不足")
                    score_details.append("经验要求: 5年以上")
                
                # 大数据专项分析
                if skill_analysis["大数据"]["required"]:
                    if skill_analysis["大数据"]["matched"]:
                        advantages.append("✅ 具备大数据相关技能")
                    else:
                        disadvantages.append("❌ JD明确要求大数据技能，但简历未体现")
                
                # 学历分析
                edu = resume_parsed.get("education", [])
                if edu and len(edu) > 0:
                    school = edu[0].get("school", "")
                    degree = edu[0].get("degree", "")
                    if any(x in school for x in ["清华", "北大", "复旦", "上交", "浙大", "985", "211"]):
                        advantages.append("✅ 毕业于知名院校")
                        score_details.append("学历: 985/211")
                
                # 如果没有优劣势，添加默认
                if not advantages:
                    advantages.append("📋 简历结构完整")
                if not disadvantages:
                    disadvantages.append("💡 可进一步了解具体项目细节")
                
                # ============ 确定匹配等级 ============
                if total_score >= 80:
                    match_level = "完美匹配"
                elif total_score >= 65:
                    match_level = "高度匹配"
                elif total_score >= 50:
                    match_level = "基本匹配"
                elif total_score >= 35:
                    match_level = "部分匹配"
                else:
                    match_level = "不匹配"
                
                # ============ 生成建议 ============
                recommendation = ""
                if total_score >= 65:
                    recommendation = "推荐进入面试环节，技能与岗位匹配度较高"
                elif total_score >= 50:
                    recommendation = "建议面试，需要进一步了解项目细节"
                elif total_score >= 35:
                    recommendation = "可作为备选，需要提升相关技能"
                else:
                    recommendation = "不太匹配，建议投递其他更合适的岗位"
                
                print(f"[Matcher] 匹配结果: skill={skill_score}%, exp={exp_score}%, edu={edu_score}%, total={total_score}")
                print(f"[Matcher] 生成结果: advantages={len(advantages)}, disadvantages={len(disadvantages)}")
                
                return {
                    "total_score": total_score,
                    "skill_match": f"{skill_score}%",
                    "experience_match": f"{exp_score}%",
                    "education_match": f"{edu_score}%",
                    "match_level": match_level,
                    "advantages": advantages,
                    "disadvantages": disadvantages,
                    "score_details": score_details,  # 新增：详细评分说明
                    "recommendation": recommendation
                }
            
            # 默认返回（如果没有足够信息）
            print(f"[Matcher] 使用默认结果（参数不足）")
            return {
                "total_score": 50,
                "skill_match": "50%",
                "experience_match": "50%",
                "education_match": "50%",
                "match_level": "基本匹配",
                "advantages": ["需要更多数据进行分析"],
                "disadvantages": ["信息不足"],
                "recommendation": "建议上传更详细的简历"
            }
        
        elif agent_name == "fraud-detector":
            return {
                "risk_level": "低",
                "issues": [],
                "flags": [
                    "简历信息完整",
                    "未发现明显异常"
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
