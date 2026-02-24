"""
PDF解析模块 - 支持从PDF文件中提取文本内容
支持多种PDF格式：简历JD、简历文档
"""

import io
from typing import Optional, Union
from pathlib import Path

# 优先使用 pdfminer.six（更稳定）
try:
    from pdfminer.high_level import extract_text
    from pdfminer.layout import LAParams
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False

# 备选方案：PyMuPDF
try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class PDFParseError(Exception):
    """PDF解析异常"""
    pass


class PDFParser:
    """PDF文档解析器"""
    
    def __init__(self):
        # 优先使用 pdfminer（更稳定）
        self.pdfminer = None
        self.pymupdf = None
        
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查可用的PDF解析库"""
        # 尝试导入 pdfminer
        if PDFMINER_AVAILABLE:
            try:
                from pdfminer.high_level import extract_text
                from pdfminer.layout import LAParams
                self.pdfminer = {
                    'extract_text': extract_text,
                    'LAParams': LAParams
                }
            except ImportError:
                pass
        
        # 尝试导入 PyMuPDF
        if PYMUPDF_AVAILABLE:
            try:
                import fitz
                self.pymupdf = fitz
            except ImportError:
                pass
        
        if not self.pdfminer and not self.pymupdf:
            raise ImportError(
                "需要安装PDF解析库，请运行: pip install pdfminer.six PyMuPDF"
            )
    
    def parse(
        self, 
        file_content: Union[bytes, io.BytesIO, str], 
        filename: Optional[str] = None
    ) -> str:
        """
        解析PDF文件并提取文本内容
        
        Args:
            file_content: PDF文件内容（bytes或文件路径）
            filename: 文件名（用于判断文件类型）
            
        Returns:
            提取的文本内容
            
        Raises:
            PDFParseError: 解析失败时抛出
        """
        # 判断是文件路径还是内容
        if isinstance(file_content, (str, Path)):
            return self._parse_from_path(file_content)
        
        # 检测文件类型
        if filename and filename.lower().endswith('.pdf'):
            return self._parse_pdf_bytes(file_content)
        elif filename and filename.lower().endswith(('.txt', '.md', '.text')):
            return self._parse_text(file_content)
        else:
            # 尝试自动检测
            return self._parse_auto(file_content)
    
    def _parse_from_path(self, file_path: Union[str, Path]) -> str:
        """从文件路径解析"""
        path = Path(file_path)
        if not path.exists():
            raise PDFParseError(f"文件不存在: {file_path}")
        
        suffix = path.suffix.lower()
        
        if suffix == '.pdf':
            with open(path, 'rb') as f:
                return self._parse_pdf_bytes(f.read())
        elif suffix in ('.txt', '.md', '.text'):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise PDFParseError(f"不支持的文件类型: {suffix}")
    
    def _parse_pdf_bytes(self, content: bytes) -> str:
        """从PDF字节内容解析文本"""
        # 尝试使用 pdfminer
        if PDFMINER_AVAILABLE:
            try:
                return self._parse_with_pdfminer(content)
            except Exception as e:
                print(f"pdfminer 解析失败: {e}")
        
        # 备选：使用 PyMuPDF
        if PYMUPDF_AVAILABLE:
            try:
                return self._parse_with_pymupdf(content)
            except Exception as e:
                raise PDFParseError(f"PyMuPDF 解析失败: {e}")
        
        raise PDFParseError("无可用的PDF解析库")
    
    def _parse_with_pdfminer(self, content: bytes) -> str:
        """使用 pdfminer.six 解析"""
        laparams = LAParams(
            line_margin=0.5,
            word_margin=0.1,
            char_margin=2.0,
            detect_vertical=False
        )
        
        # 将 bytes 转为 StringIO
        pdf_stream = io.BytesIO(content)
        text = extract_text(pdf_stream, laparams=laparams)
        
        # 清理文本
        text = self._clean_text(text)
        
        if not text.strip():
            raise PDFParseError("PDF解析结果为空")
        
        return text
    
    def _parse_with_pymupdf(self, content: bytes) -> str:
        """使用 PyMuPDF 解析"""
        pdf_stream = io.BytesIO(content)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        
        text_parts = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_parts.append(page.get_text())
        
        doc.close()
        
        text = '\n'.join(text_parts)
        text = self._clean_text(text)
        
        if not text.strip():
            raise PDFParseError("PDF解析结果为空")
        
        return text
    
    def _parse_text(self, content: Union[bytes, str]) -> str:
        """解析纯文本文件"""
        if isinstance(content, bytes):
            # 尝试多种编码
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
                try:
                    return content.decode(encoding)
                except (UnicodeDecodeError, AttributeError):
                    continue
            raise PDFParseError("无法解码文本文件")
        return content
    
    def _parse_auto(self, content: bytes) -> str:
        """自动检测文件类型并解析"""
        # 检查PDF魔数
        if content[:5] == b'%PDF-':
            return self._parse_pdf_bytes(content)
        
        # 尝试作为文本解析
        return self._parse_text(content)
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """清理提取的文本"""
        import re
        
        # 移除多余的空白字符
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # 移除行首行尾空白
            line = line.strip()
            # 跳过纯空白行（保留段落分隔）
            if line:
                cleaned_lines.append(line)
        
        # 合并行，用单个换行符分隔
        text = '\n'.join(cleaned_lines)
        
        # 移除常见的PDF噪声字符
        noise_pattern = r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]'
        text = re.sub(noise_pattern, '', text)
        
        return text


def parse_file(file_path: str) -> str:
    """
    便捷函数：解析文件并提取文本
    
    Args:
        file_path: 文件路径
        
    Returns:
        提取的文本内容
    """
    parser = PDFParser()
    return parser.parse(file_path)


# 测试代码
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python pdf_parser.py <文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        parser = PDFParser()
        text = parser.parse(file_path)
        print("=== 解析结果 ===")
        print(text[:1000])  # 打印前1000字符
        print(f"\n... (共 {len(text)} 字符)")
    except Exception as e:
        print(f"解析失败: {e}")
        sys.exit(1)
