#!/usr/bin/env python3
"""
行业分析报告生成器
调用 FMP API 获取所有行业分类，分析现有映射，生成建议报告
"""

import requests
import json
import os
from dotenv import load_dotenv
from typing import Dict, List, Any

# 加载环境变量
load_dotenv()

def get_fmp_industries() -> List[str]:
    """从 FMP API 获取所有行业分类"""
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        raise ValueError("FMP_API_KEY environment variable is required")
    
    url = f"https://financialmodelingprep.com/api/v3/industries-list?apikey={api_key}"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"FMP API 请求失败: {response.status_code}")
    
    industries = response.json()
    if isinstance(industries, list):
        return industries
    else:
        raise Exception(f"意外的响应格式: {type(industries)}")

def load_current_mapping() -> Dict[str, str]:
    """加载当前的行业映射配置"""
    try:
        import yaml
        with open('industry_templates.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get('industry_mapping', {})
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {}

def suggest_template_for_industry(industry: str) -> str:
    """为新行业建议合适的模板"""
    industry_lower = industry.lower()
    
    # 金融相关
    if any(keyword in industry_lower for keyword in ['bank', 'financial', 'credit', 'insurance', 'asset', 'investment', 'capital', 'mortgage']):
        if 'insurance' in industry_lower:
            return 'insurance'
        return 'banking'
    
    # 科技相关
    if any(keyword in industry_lower for keyword in ['software', 'technology', 'semiconductor', 'internet', 'electronic', 'gaming', 'communication', 'information']):
        return 'technology'
    
    # 医疗相关
    if any(keyword in industry_lower for keyword in ['drug', 'medical', 'biotechnology', 'healthcare', 'pharmaceutical']):
        return 'healthcare'
    
    # 能源相关
    if any(keyword in industry_lower for keyword in ['oil', 'gas', 'energy', 'coal', 'renewable', 'petroleum', 'uranium', 'solar']):
        return 'energy'
    
    # 消费品相关
    if any(keyword in industry_lower for keyword in ['beverage', 'food', 'packaged', 'household', 'personal', 'textile', 'apparel', 'footwear', 'tobacco']):
        return 'consumer_goods'
    
    # 零售相关
    if any(keyword in industry_lower for keyword in ['retail', 'store', 'dealership', 'grocery', 'discount', 'department']):
        return 'retail'
    
    # 工业相关
    if any(keyword in industry_lower for keyword in ['aerospace', 'defense', 'industrial', 'machinery', 'metal', 'electrical', 'building', 'manufacturing']):
        return 'industrial'
    
    # 房地产相关
    if any(keyword in industry_lower for keyword in ['reit', 'real estate', 'property', 'development']):
        return 'real_estate'
    
    # 通信相关
    if any(keyword in industry_lower for keyword in ['telecom', 'entertainment', 'broadcasting', 'publishing', 'media']):
        return 'telecommunications'
    
    # 材料相关
    if any(keyword in industry_lower for keyword in ['chemical', 'steel', 'aluminum', 'copper', 'gold', 'silver', 'agricultural']):
        return 'materials'
    
    # 公用事业相关
    if any(keyword in industry_lower for keyword in ['utility', 'electric', 'water', 'power']):
        return 'utilities'
    
    # 运输相关
    if any(keyword in industry_lower for keyword in ['airline', 'railroad', 'trucking', 'shipping', 'transportation', 'airport']):
        return 'transportation'
    
    # 默认使用通用模板
    return 'general'

def get_template_reasoning(industry: str, template: str) -> str:
    """获取模板选择的理由"""
    reasoning_map = {
        'banking': '金融服务业，重视财务稳健性和风险管理',
        'technology': '科技行业，重视成长性和创新能力',
        'healthcare': '医疗保健行业，重视研发投入和专利保护',
        'energy': '能源行业，受大宗商品价格影响大',
        'consumer_goods': '消费品行业，防御性较强，现金流稳定',
        'retail': '零售业，受经济周期影响，重视运营效率',
        'industrial': '工业制造业，周期性行业，技术壁垒较高',
        'real_estate': '房地产行业，重视租金收入和资产价值',
        'telecommunications': '通信服务业，基础设施投资大，监管环境复杂',
        'materials': '材料行业，大宗商品价格敏感，周期性明显',
        'utilities': '公用事业，防御性最强，监管定价',
        'transportation': '运输业，经济周期敏感，运营效率重要',
        'general': '通用模板，适用于大多数未分类行业'
    }
    return reasoning_map.get(template, '通用模板，适用于大多数未分类行业')

def generate_report():
    """生成完整的行业分析报告"""
    print("🚀 开始生成行业分析报告...")
    print("=" * 80)
    
    # 1. 获取 FMP 行业列表
    print("📊 步骤 1: 获取 FMP 所有行业分类")
    try:
        industries = get_fmp_industries()
        print(f"✅ 成功获取 {len(industries)} 个行业分类")
    except Exception as e:
        print(f"❌ 获取行业分类失败: {e}")
        return
    
    # 2. 加载当前映射
    print("\n📋 步骤 2: 分析现有行业映射")
    current_mapping = load_current_mapping()
    existing_industries = set(current_mapping.keys())
    print(f"✅ 当前配置包含 {len(existing_industries)} 个已映射行业")
    
    # 3. 分析新行业
    print("\n🔍 步骤 3: 分析新行业并提供建议")
    new_industries = []
    mapped_industries = []
    
    for industry in industries:
        if industry in existing_industries:
            mapped_industries.append({
                "industry": industry,
                "template": current_mapping[industry],
                "status": "已映射"
            })
        else:
            suggested_template = suggest_template_for_industry(industry)
            reasoning = get_template_reasoning(industry, suggested_template)
            new_industries.append({
                "industry": industry,
                "suggested_template": suggested_template,
                "reasoning": reasoning,
                "status": "需要映射"
            })
    
    # 4. 生成报告
    print("\n📈 分析结果汇总")
    print("=" * 80)
    print(f"总行业数量: {len(industries)}")
    print(f"已映射行业: {len(mapped_industries)}")
    print(f"新行业数量: {len(new_industries)}")
    print(f"映射覆盖率: {len(mapped_industries)/len(industries)*100:.1f}%")
    
    # 5. 按模板分组统计
    print("\n📊 按模板分组统计")
    print("-" * 50)
    template_counts = {}
    for item in new_industries:
        template = item['suggested_template']
        template_counts[template] = template_counts.get(template, 0) + 1
    
    for template, count in sorted(template_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{template:20}: {count:3d} 个行业")
    
    # 6. 生成 YAML 映射建议
    print("\n📝 YAML 映射建议")
    print("-" * 50)
    print("# 新增行业映射建议")
    print("# 请将以下内容添加到 industry_templates.yaml 的 industry_mapping 部分")
    print()
    
    for item in new_industries:
        industry = item['industry']
        template = item['suggested_template']
        reasoning = item['reasoning']
        print(f'  "{industry}": "{template}"  # {reasoning}')
    
    # 7. 生成详细清单
    print("\n📋 详细行业清单")
    print("=" * 80)
    print("已映射行业:")
    print("-" * 40)
    for item in sorted(mapped_industries, key=lambda x: x['industry']):
        print(f"✅ {item['industry']} → {item['template']}")
    
    print("\n新行业建议:")
    print("-" * 40)
    for item in sorted(new_industries, key=lambda x: x['industry']):
        print(f"🆕 {item['industry']} → {item['suggested_template']} ({item['reasoning']})")
    
    # 8. 保存报告到文件
    report_data = {
        "summary": {
            "total_industries": len(industries),
            "mapped_industries": len(mapped_industries),
            "new_industries": len(new_industries),
            "coverage_rate": len(mapped_industries)/len(industries)*100
        },
        "template_distribution": template_counts,
        "mapped_industries": mapped_industries,
        "new_industries": new_industries,
        "yaml_suggestion": "\n".join([
            f'  "{item["industry"]}": "{item["suggested_template"]}"  # {item["reasoning"]}'
            for item in new_industries
        ])
    }
    
    with open('industry_analysis_report.json', 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 详细报告已保存到: industry_analysis_report.json")
    print("\n🎉 行业分析报告生成完成！")

if __name__ == "__main__":
    generate_report()
