#!/usr/bin/env python3
"""
技能匹配工具 - 纯规则匹配版本
无需安装额外依赖，直接运行

使用方法:
    python skill_matcher.py --find "gin框架"
    python skill_matcher.py --match "简历技能" "JD技能"
    python skill_matcher.py --interactive
"""

import json
import argparse
from pathlib import Path
from difflib import SequenceMatcher

# 配置路径
BASE_DIR = Path(__file__).parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge-base"


class SkillMatcher:
    """技能匹配器 - 基于规则和模糊匹配"""
    
    def __init__(self):
        self.skills_data = None
        self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """加载技能映射知识库"""
        skills_file = KNOWLEDGE_BASE_DIR / "skills-mapping.json"
        with open(skills_file, 'r', encoding='utf-8') as f:
            self.skills_data = json.load(f)
        
        # 构建反向映射表
        self.alias_to_standard = {}
        self.all_skills = set()
        
        for category, skills in self.skills_data.get("categories", {}).items():
            for standard_name, aliases in skills.items():
                self.all_skills.add(standard_name.lower())
                # 添加标准名称
                self.alias_to_standard[standard_name.lower()] = {
                    "standard": standard_name,
                    "category": category
                }
                # 添加别名
                for alias in aliases:
                    if alias.lower() != standard_name.lower():
                        self.alias_to_standard[alias.lower()] = {
                            "standard": standard_name,
                            "category": category
                        }
        
        print(f"✅ 已加载 {len(self.all_skills)} 个技能映射")
    
    def normalize_skill(self, skill: str) -> dict:
        """标准化技能名称"""
        skill_lower = skill.lower().strip()
        
        # 精确匹配
        if skill_lower in self.alias_to_standard:
            return {
                "original": skill,
                "standard": self.alias_to_standard[skill_lower]["standard"],
                "category": self.alias_to_standard[skill_lower]["category"],
                "method": "exact",
                "similarity": 1.0
            }
        
        # 模糊匹配
        best_match = None
        best_score = 0
        
        for alias, info in self.alias_to_standard.items():
            # 计算相似度
            score = SequenceMatcher(None, skill_lower, alias).ratio()
            
            # 中文技能可能有简写/全称差异
            if "golang" in alias or "go语言" in alias:
                if "golang" in skill_lower or "go语言" in skill_lower or skill_lower == "go":
                    score = 0.95
            
            if score > best_score and score > 0.6:
                best_score = score
                best_match = info
        
        if best_match:
            return {
                "original": skill,
                "standard": best_match["standard"],
                "category": best_match["category"],
                "method": "fuzzy",
                "similarity": round(best_score, 2)
            }
        
        # 未找到匹配
        return {
            "original": skill,
            "standard": skill,
            "category": "未知",
            "method": "none",
            "similarity": 0
        }
    
    def match_skills(self, resume_skills: list, jd_skills: list) -> dict:
        """匹配简历技能和JD技能"""
        # 标准化简历技能
        resume_normalized = []
        for skill in resume_skills:
            normalized = self.normalize_skill(skill)
            resume_normalized.append(normalized)
        
        # 标准化JD技能
        jd_normalized = []
        for skill in jd_skills:
            normalized = self.normalize_skill(skill)
            jd_normalized.append(normalized)
        
        # 计算匹配
        matched = []
        unmatched = []
        used_resume_skills = set()  # 记录已匹配的简历技能
        
        for jd_skill in jd_normalized:
            found = False
            for i, resume_skill in enumerate(resume_normalized):
                # 跳过已使用的简历技能
                if i in used_resume_skills:
                    continue
                    
                # 检查标准名称是否相同
                if jd_skill["standard"].lower() == resume_skill["standard"].lower():
                    matched.append({
                        "jd": jd_skill["original"],
                        "resume": resume_skill["original"],
                        "standard": jd_skill["standard"],
                        "similarity": 1.0
                    })
                    used_resume_skills.add(i)
                    found = True
                    break
                # 检查类别是否相同且相似度较高
                elif (jd_skill["category"] == resume_skill["category"] and 
                      resume_skill["similarity"] > 0.7):
                    matched.append({
                        "jd": jd_skill["original"],
                        "resume": resume_skill["original"],
                        "standard": jd_skill["standard"],
                        "similarity": resume_skill["similarity"]
                    })
                    used_resume_skills.add(i)
                    found = True
                    break
            
            if not found:
                unmatched.append(jd_skill)
        
        match_rate = len(matched) / len(jd_normalized) * 100 if jd_normalized else 0
        
        return {
            "match_rate": round(match_rate, 1),
            "matched": matched,
            "unmatched": unmatched,
            "total_jd": len(jd_normalized),
            "total_matched": len(matched)
        }


def find_skill(skill_name: str):
    """查找技能标准名称"""
    matcher = SkillMatcher()
    result = matcher.normalize_skill(skill_name)
    
    print(f"\n🔍 查询: {skill_name}")
    print("=" * 50)
    
    if result["method"] == "none":
        print(f"❌ 未找到匹配")
    else:
        print(f"✅ 原始输入: {result['original']}")
        print(f"📌 标准名称: {result['standard']}")
        print(f"📂 类别: {result['category']}")
        print(f"🔬 匹配方式: {result['method']}")
        print(f"📊 相似度: {result['similarity']:.0%}")


def match_skills(resume_str: str, jd_str: str):
    """匹配技能"""
    matcher = SkillMatcher()
    
    # 解析技能列表
    resume_skills = [s.strip() for s in resume_str.split(",") if s.strip()]
    jd_skills = [s.strip() for s in jd_str.split(",") if s.strip()]
    
    print(f"\n📋 简历技能: {resume_skills}")
    print(f"📋 JD技能: {jd_skills}")
    
    result = matcher.match_skills(resume_skills, jd_skills)
    
    print("\n" + "=" * 50)
    print(f"🎯 匹配率: {result['match_rate']}%")
    print(f"   已匹配: {result['total_matched']}/{result['total_jd']}")
    
    if result["matched"]:
        print("\n✅ 已匹配:")
        for m in result["matched"]:
            print(f"   - JD: {m['jd']} → 简历: {m['resume']} (标准: {m['standard']})")
    
    if result["unmatched"]:
        print("\n❌ 未匹配:")
        for m in result["unmatched"]:
            print(f"   - {m['original']} ({m['category']})")


def interactive():
    """交互模式"""
    print("=" * 50)
    print("🎯 技能匹配交互模式")
    print("   输入技能名称查询，输入 'quit' 退出")
    print("=" * 50)
    
    matcher = SkillMatcher()
    
    while True:
        query = input("\n🔍 请输入技能名称: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("👋 再见!")
            break
        
        if not query:
            continue
        
        result = matcher.normalize_skill(query)
        
        if result["method"] == "none":
            print(f"❌ 未找到: {query}")
        else:
            print(f"✅ 标准名称: {result['standard']} | 类别: {result['category']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="技能匹配工具")
    parser.add_argument("--find", type=str, help="查找技能标准名称")
    parser.add_argument("--match", nargs=2, metavar=("RESUME", "JD"), help="匹配简历和JD技能")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    
    args = parser.parse_args()
    
    if args.find:
        find_skill(args.find)
    elif args.match:
        match_skills(args.match[0], args.match[1])
    elif args.interactive:
        interactive()
    else:
        print(__doc__)
        print("\n示例:")
        print("  python skill_matcher.py --find gin框架")
        print('  python skill_matcher.py --match "Golang,Redis" "Go,缓存"')
        print("  python skill_matcher.py --interactive")
