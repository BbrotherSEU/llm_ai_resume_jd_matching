"""
FastAPI 后端服务 - HR简历筛选系统
提供REST API接口，支持PDF文件上传和简历筛选
"""

import os
import io
from typing import Optional
from pathlib import Path

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json

from pdf_parser import PDFParser
from opencode_service import screening_resume
import glob

# 创建FastAPI应用
app = FastAPI(
    title="HR简历筛选系统 API",
    description="基于大模型的简历筛选服务，支持JD与简历匹配度评估",
    version="1.0.0"
)

# 配置CORS跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== 数据模型 ==============

class ScreeningOptions(BaseModel):
    """筛选选项"""
    enable_fraud_check: bool = True


class ScreeningRequest(BaseModel):
    """筛选请求"""
    jd_content: str
    resume_content: str
    options: Optional[ScreeningOptions] = None


class ScreeningResponse(BaseModel):
    """筛选响应"""
    success: bool
    message: str
    data: Optional[dict] = None


# ============== 工具函数 ==============

def parse_uploaded_file(file: UploadFile) -> str:
    """
    解析上传的文件（支持PDF和TXT）
    
    Args:
        file: 上传的文件对象
        
    Returns:
        解析后的文本内容
    """
    # 读取文件内容
    content = file.file.read()
    
    # 判断文件类型
    filename = file.filename.lower()
    
    parser = PDFParser()
    
    try:
        if filename.endswith('.pdf'):
            return parser._parse_pdf_bytes(content)
        elif filename.endswith(('.txt', '.md', '.text')):
            # 解码文本
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            raise HTTPException(status_code=400, detail="无法解码文本文件")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")


# ============== API路由 ==============

@app.get("/")
async def root():
    """健康检查"""
    return {
        "status": "ok",
        "service": "HR简历筛选系统",
        "version": "1.0.0"
    }


@app.get("/api/v1/health")
async def health_check():
    """API健康检查"""
    return {"status": "healthy"}


@app.post("/api/v1/screening", response_model=ScreeningResponse)
async def screening_with_content(request: ScreeningRequest):
    """
    筛选简历（直接传入文本内容）
    
    Args:
        request: 包含JD和简历内容的请求
        
    Returns:
        筛选结果
    """
    try:
        jd_content = request.jd_content
        resume_content = request.resume_content
        
        # 文本长度检查
        if not jd_content or len(jd_content.strip()) < 20:
            return ScreeningResponse(
                success=False,
                message="JD内容过短"
            )
        
        if not resume_content or len(resume_content.strip()) < 20:
            return ScreeningResponse(
                success=False,
                message="简历内容过短"
            )
        
        # 获取选项
        enable_fraud = True
        if request.options:
            enable_fraud = request.options.enable_fraud_check
        
        # 调用OpenCode Agent进行筛选
        result = await screening_resume(
            jd_content,
            resume_content,
            enable_fraud
        )
        
        if result.get("success"):
            return ScreeningResponse(
                success=True,
                message="筛选完成",
                data=result
            )
        else:
            return ScreeningResponse(
                success=False,
                message=result.get("message", "筛选失败")
            )
        
    except Exception as e:
        return ScreeningResponse(
            success=False,
            message=f"筛选失败: {str(e)}"
        )


@app.post("/api/v1/screening/file")
async def screening_with_files(
    jd_file: UploadFile = File(..., description="职位描述文件(PDF/TXT)"),
    resume_file: UploadFile = File(..., description="简历文件(PDF/TXT)"),
    enable_fraud_check: bool = Form(True, description="是否启用欺诈检测")
):
    """
    筛选简历（通过文件上传）
    
    支持的文件格式：
    - PDF (.pdf)
    - 文本 (.txt, .md)
    """
    try:
        print(f"\n=== 收到筛选请求 ===")
        print(f"JD文件: {jd_file.filename}")
        print(f"简历文件: {resume_file.filename}")
        print(f"欺诈检测: {enable_fraud_check}")
        
        # 解析JD文件
        jd_content = parse_uploaded_file(jd_file)
        print(f"JD解析完成，长度: {len(jd_content)}")
        
        # 解析简历文件
        resume_content = parse_uploaded_file(resume_file)
        print(f"简历解析完成，长度: {len(resume_content)}")
        
        # 调用OpenCode Agent进行筛选
        result = await screening_resume(
            jd_content,
            resume_content,
            enable_fraud_check
        )
        
        print(f"筛选结果: success={result.get('success')}, match_score={result.get('match_score')}")
        
        if result.get("success"):
            return {
                "success": True,
                "message": "筛选完成",
                "data": {
                    "jd_file": jd_file.filename,
                    "resume_file": resume_file.filename,
                    # 筛选结果
                    "match_score": result.get("match_score", 0),
                    "skill_match": result.get("skill_match", "0%"),
                    "experience_match": result.get("experience_match", "0%"),
                    "education_match": result.get("education_match", "0%"),
                    "match_level": result.get("match_level", "未知"),
                    "risk_level": result.get("risk_level", "低"),
                    "advantages": result.get("advantages", []),
                    "disadvantages": result.get("disadvantages", []),
                    "issues": result.get("issues", []),
                    "recommendation": result.get("recommendation", ""),
                    # 模型来源信息
                    "model_source": result.get("model_source", "unknown"),
                    "model_source_display": result.get("model_source_display", "未知"),
                    "model_sources": result.get("model_sources", {}),
                    # 详细分析（可选返回）
                    "jd_analysis": result.get("jd_analysis"),
                    "resume_parsed": result.get("resume_parsed"),
                }
            }
        else:
            return {
                "success": False,
                "message": result.get("message", "筛选失败"),
                "data": None
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"处理失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"处理失败: {str(e)}",
            "data": None
        }


@app.post("/api/v1/parse")
async def parse_document(file: UploadFile = File(..., description="要解析的文档")):
    """
    解析文档（仅解析，不进行筛选）
    
    用于测试PDF解析功能
    """
    try:
        content = parse_uploaded_file(file)
        
        # 打印解析内容的前1000字符用于调试
        print(f"\n=== 解析文件: {file.filename} ===")
        print(f"内容长度: {len(content)}")
        print(f"内容前1000字:\n{content[:1000]}")
        print("=" * 50)
        
        return {
            "success": True,
            "message": "解析成功",
            "data": {
                "filename": file.filename,
                "content_length": len(content),
                "content_preview": content[:1000] + "..." if len(content) > 1000 else content,
                "full_content": content  # 返回完整内容用于调试
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "message": f"解析失败: {str(e)}"
        }


@app.get("/api/v1/history")
async def get_screening_history(limit: int = 20):
    """
    获取筛选历史记录列表
    
    Args:
        limit: 返回记录数量，默认20条
        
    Returns:
        历史记录列表
    """
    try:
        results_dir = os.path.join(os.path.dirname(__file__), "..", "results")
        
        # 获取所有结果文件
        pattern = os.path.join(results_dir, "*.json")
        files = glob.glob(pattern)
        
        # 按修改时间排序，最新的在前
        files.sort(key=os.path.getmtime, reverse=True)
        
        # 限制数量
        files = files[:limit]
        
        history = []
        for filepath in files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                result = data.get("result", {})
                
                # 提取摘要信息
                history.append({
                    "id": os.path.basename(filepath).replace(".json", ""),
                    "timestamp": data.get("timestamp", ""),
                    "position": result.get("jd_analysis", {}).get("position", "未知"),
                    "candidate": result.get("resume_parsed", {}).get("name", "未知"),
                    "match_score": result.get("match_score", 0),
                    "match_level": result.get("match_level", "未知"),
                    "risk_level": result.get("risk_level", "未知"),
                    "model_source": result.get("model_source", "unknown"),
                    "model_source_display": result.get("model_source_display", "未知"),
                })
            except Exception as e:
                print(f"读取历史记录失败: {filepath}, {e}")
                continue
        
        return {
            "success": True,
            "data": {
                "total": len(history),
                "items": history
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"获取历史记录失败: {str(e)}"
        }


@app.get("/api/v1/history/{record_id}")
async def get_screening_detail(record_id: str):
    """
    获取单条筛选记录的详细信息
    
    Args:
        record_id: 记录ID（文件名）
        
    Returns:
        详细筛选结果
    """
    try:
        results_dir = os.path.join(os.path.dirname(__file__), "..", "results")
        filepath = os.path.join(results_dir, f"{record_id}.json")
        
        if not os.path.exists(filepath):
            return {
                "success": False,
                "message": "记录不存在"
            }
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return {
            "success": True,
            "data": data
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"获取详情失败: {str(e)}"
        }


# ============== 启动配置 ==============

if __name__ == "__main__":
    import uvicorn
    
    # 获取端口，默认 8888
    port = int(os.getenv("PORT", "8888"))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
