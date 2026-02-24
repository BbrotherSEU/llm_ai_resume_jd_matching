#!/usr/bin/env python3
"""
向量搜索工具 - 基于 Chroma 本地向量数据库
完全免费，无需 API Key

安装依赖:
    pip install chromadb sentence-transformers

使用方法:
    python vector_search.py --index           # 构建索引
    python vector_search.py --search "Golang后端"  # 搜索
"""

import os
import json
import argparse
from pathlib import Path

# 配置路径
BASE_DIR = Path(__file__).parent
VECTOR_STORE_DIR = BASE_DIR / "vector-store"
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge-base"

# 尝试导入，优雅处理缺失依赖
try:
    import chromadb
    from chromadb.config import Settings
    # 新版本 Chroma 使用 PersistentClient
    try:
        from chromadb import PersistentClient
        CHROMADB_AVAILABLE = True
        CHROMA_VERSION = "new"
    except ImportError:
        CHROMADB_AVAILABLE = True
        CHROMA_VERSION = "old"
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️  请安装 chromadb: pip install chromadb")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️  请安装 sentence-transformers: pip install sentence-transformers")


class VectorSearcher:
    """向量搜索器 - 使用 Chroma + 本地 Embedding"""
    
    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5"):
        self.model_name = model_name
        self.client = None
        self.model = None
        self.collection = None
        
    def init(self):
        """初始化向量数据库和模型"""
        if not CHROMADB_AVAILABLE or not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("缺少必要依赖，请先安装 chromadb 和 sentence-transformers")
        
        # 初始化 Chroma 客户端（本地持久化）- 兼容新旧版本
        if CHROMA_VERSION == "new":
            self.client = PersistentClient(
                path=str(VECTOR_STORE_DIR)
            )
        else:
            self.client = chromadb.Client(Settings(
                persist_directory=str(VECTOR_STORE_DIR),
                anonymized_telemetry=False
            ))
        
        # 加载本地 Embedding 模型
        print(f"📥 加载模型: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        
        # 获取或创建集合
        try:
            self.collection = self.client.get_collection("skills")
        except:
            self.collection = self.client.create_collection("skills")
        
        print("✅ 向量搜索器初始化完成")
    
    def load_knowledge_base(self):
        """从知识库加载技能映射并构建向量索引"""
        # 加载技能映射
        skills_file = KNOWLEDGE_BASE_DIR / "skills-mapping.json"
        with open(skills_file, 'r', encoding='utf-8') as f:
            skills_data = json.load(f)
        
        # 提取所有技能名称和别名
        skills_to_index = []
        skills_ids = []
        skills_metadata = []
        
        category_count = 0
        skill_count = 0
        
        for category, skills in skills_data.get("categories", {}).items():
            category_count += 1
            for standard_name, aliases in skills.items():
                skill_count += 1
                
                # 添加标准名称
                skills_to_index.append(standard_name)
                skills_ids.append(f"skill_{skill_count}")
                skills_metadata.append({
                    "type": "standard",
                    "category": category,
                    "name": standard_name
                })
                
                # 添加别名
                for alias in aliases:
                    if alias.lower() != standard_name.lower():
                        skills_to_index.append(alias)
                        skills_ids.append(f"alias_{skill_count}_{len(skills_metadata)}")
                        skills_metadata.append({
                            "type": "alias",
                            "category": category,
                            "name": standard_name,
                            "alias_of": standard_name
                        })
        
        # 生成向量
        print(f"📊 正在生成 {len(skills_to_index)} 个技能向量...")
        embeddings = self.model.encode(skills_to_index)
        
        # 写入向量数据库
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=skills_to_index,
            ids=skills_ids,
            metadatas=skills_metadata
        )
        
        print(f"✅ 已索引 {skill_count} 个技能（{category_count} 个类别），共 {len(skills_to_index)} 个条目")
        
        return {
            "total_skills": skill_count,
            "total_entries": len(skills_to_index),
            "categories": category_count
        }
    
    def search_similar_skills(self, query: str, top_k: int = 5) -> list:
        """搜索相似技能"""
        # 生成查询向量
        query_embedding = self.model.encode([query])
        
        # 搜索
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=top_k
        )
        
        # 格式化结果
        similar_skills = []
        for i, (doc, meta, distance) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )):
            similarity = 1 - distance  # 转换距离为相似度
            similar_skills.append({
                "skill": doc,
                "category": meta.get("category", ""),
                "type": meta.get("type", ""),
                "alias_of": meta.get("alias_of", ""),
                "similarity": round(similarity, 4)
            })
        
        return similar_skills
    
    def find_standard_skill(self, skill: str) -> dict:
        """查找技能的标准名称"""
        results = self.search_similar_skills(skill, top_k=3)
        
        if not results:
            return {"found": False, "skill": skill}
        
        # 优先返回标准名称（非别名）
        for r in results:
            if r["type"] == "standard" or r["similarity"] > 0.8:
                return {
                    "found": True,
                    "original": skill,
                    "standard": r.get("alias_of") or r["skill"],
                    "category": r["category"],
                    "similarity": r["similarity"]
                }
        
        return {
            "found": True,
            "original": skill,
            "standard": results[0].get("alias_of") or results[0]["skill"],
            "category": results[0]["category"],
            "similarity": results[0]["similarity"]
        }


def index_knowledge_base():
    """构建知识库向量索引"""
    print("🚀 开始构建向量索引...\n")
    
    searcher = VectorSearcher()
    searcher.init()
    
    result = searcher.load_knowledge_base()
    
    print(f"\n📋 索引构建完成:")
    print(f"   - 技能数量: {result['total_skills']}")
    print(f"   - 总条目数: {result['total_entries']}")
    print(f"   - 类别数量: {result['categories']}")
    print(f"\n📁 索引保存在: {VECTOR_STORE_DIR}")


def search_skill(query: str, top_k: int = 5):
    """搜索相似技能"""
    print(f"🔍 搜索: {query}\n")
    
    searcher = VectorSearcher()
    searcher.init()
    
    results = searcher.search_similar_skills(query, top_k=top_k)
    
    print("📊 搜索结果:")
    print("-" * 60)
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['skill']}")
        print(f"   类别: {r['category']}")
        print(f"   类型: {r['type']} {'(别名)' if r['alias_of'] else ''}")
        print(f"   相似度: {r['similarity']:.2%}")
        print()


def find_standard(query: str):
    """查找标准技能名称"""
    print(f"🔎 查找标准名称: {query}\n")
    
    searcher = VectorSearcher()
    searcher.init()
    
    result = searcher.find_standard_skill(query)
    
    if result["found"]:
        print(f"✅ 原始输入: {result['original']}")
        print(f"📌 标准名称: {result['standard']}")
        print(f"📂 类别: {result['category']}")
        print(f"📊 相似度: {result['similarity']:.2%}")
    else:
        print(f"❌ 未找到匹配: {query}")


def interactive_mode():
    """交互模式"""
    print("=" * 60)
    print("🎯 向量搜索交互模式")
    print("   输入技能名称进行搜索，输入 'quit' 退出")
    print("=" * 60 + "\n")
    
    searcher = VectorSearcher()
    searcher.init()
    
    while True:
        query = input("🔍 请输入技能名称: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("👋 再见!")
            break
        
        if not query:
            continue
        
        find_standard(query)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="向量搜索工具")
    parser.add_argument("--index", action="store_true", help="构建知识库索引")
    parser.add_argument("--search", type=str, help="搜索技能")
    parser.add_argument("--find", type=str, help="查找标准名称")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    
    args = parser.parse_args()
    
    if args.index:
        index_knowledge_base()
    elif args.search:
        search_skill(args.search)
    elif args.find:
        find_standard(args.find)
    elif args.interactive:
        interactive_mode()
    else:
        print(__doc__)
        print("\n示例:")
        print("  python vector_search.py --index              # 构建索引")
        print("  python vector_search.py --search Golang      # 搜索")
        print("  python vector_search.py --find Go            # 查找标准名称")
        print("  python vector_search.py --interactive        # 交互模式")
