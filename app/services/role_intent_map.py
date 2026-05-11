"""
Role -> Pillar -> Intent map for ESG query routing.

This structure is designed for:
1) Role classification
2) ESG pillar classification
3) Topic intent routing
"""

ROLE_PILLAR_INTENT_MAP = {
    "job_seeker": {
        "E": {
            "focus": "Work environment and sustainability culture",
            "intents": [
                "ghg_emissions",
                "energy",
                "water",
            ],
            "question_templates": [
                "公司在減碳上做了哪些具體行動？",
                "公司用電和再生能源比例如何，會影響工作環境嗎？",
                "公司是否重視水資源管理與環境責任？",
            ],
        },
        "S": {
            "focus": "Employee experience and people practices",
            "intents": [
                "workforce_compensation",
                "workforce_turnover",
                "training_development",
                "harassment_ethics",
                "grievance_mechanism",
            ],
            "question_templates": [
                "員工薪資中位數和福利制度如何？",
                "離職率高嗎？關鍵人才留任狀況如何？",
                "平均訓練時數和職涯發展制度是什麼？",
                "是否發生霸凌或騷擾案件？公司怎麼處理？",
                "是否有匿名申訴與防報復機制？",
            ],
        },
        "G": {
            "focus": "Ethical culture and leadership credibility",
            "intents": [
                "governance",
                "risk_management",
                "executive_compensation",
            ],
            "question_templates": [
                "公司治理是否透明、董事會是否獨立？",
                "公司如何管理重大風險與危機？",
                "高階主管薪酬是否合理且與績效連動？",
            ],
        },
    },
    "investor": {
        "E": {
            "focus": "Transition risk, regulatory exposure, and efficiency",
            "intents": [
                "ghg_emissions",
                "energy",
                "water",
            ],
            "question_templates": [
                "Scope 1/2/3 排放趨勢與減量路徑為何？",
                "再生能源占比與能源效率是否改善？",
                "高水壓地區曝險與用水效率是否可控？",
            ],
        },
        "S": {
            "focus": "Human capital quality and operational resilience",
            "intents": [
                "workforce_compensation",
                "workforce_turnover",
                "training_development",
                "harassment_ethics",
            ],
            "question_templates": [
                "薪酬競爭力是否支撐留才和生產力？",
                "離職率是否顯示營運風險或管理問題？",
                "人才培育投入是否轉化為長期競爭優勢？",
                "人權/騷擾事件是否造成聲譽與法遵風險？",
            ],
        },
        "G": {
            "focus": "Governance quality and capital allocation discipline",
            "intents": [
                "governance",
                "risk_management",
                "executive_compensation",
                "executive_shareholding",
                "financial",
            ],
            "question_templates": [
                "董事會獨立性與多元性是否符合國際水準？",
                "ERM 與氣候風險是否納入董事會監督？",
                "高管薪酬是否與 ESG/KPI 連動且可驗證？",
                "經理人持股結構是否與股東利益一致？",
                "財務表現是否支持永續投資與資本支出？",
            ],
        },
    },
    "esg_department": {
        "E": {
            "focus": "Disclosure quality, target management, and assurance readiness",
            "intents": [
                "ghg_emissions",
                "energy",
                "water",
                "climate",
            ],
            "question_templates": [
                "Scope 1/2/3 盤查邊界與查證狀態是否完整？",
                "能源與再生能源 KPI 達成率是否可追蹤？",
                "水管理指標是否符合揭露框架要求？",
                "氣候風險情境分析是否可對應 TCFD/ISSB？",
            ],
        },
        "S": {
            "focus": "Policy completeness, metrics consistency, and remediation tracking",
            "intents": [
                "workforce_compensation",
                "workforce_turnover",
                "training_development",
                "harassment_ethics",
                "grievance_mechanism",
                "workforce",
            ],
            "question_templates": [
                "薪酬、離職、訓練等人力資本指標口徑是否一致？",
                "DEI、人權與騷擾案件揭露是否完整且可稽核？",
                "申訴機制的受理、處理、結案率是否可追蹤？",
                "員工議題是否滿足 CSA/DJSI 問卷要件？",
            ],
        },
        "G": {
            "focus": "Governance mechanism design and external rating readiness",
            "intents": [
                "governance",
                "risk_management",
                "executive_compensation",
                "executive_shareholding",
                "financial",
            ],
            "question_templates": [
                "董事會治理架構與委員會設計是否符合法規與評比要求？",
                "風險管理流程、三道防線與稽核證據是否完備？",
                "高管薪酬連結 ESG 指標的證據鏈是否可驗證？",
                "是否具備持股與薪酬資料的外部資料串接機制？",
            ],
        },
    },
}


ROLE_PRIORITY_INTENTS = {
    "job_seeker": [
        "workforce_compensation",
        "workforce_turnover",
        "training_development",
        "harassment_ethics",
        "grievance_mechanism",
        "governance",
        "risk_management",
    ],
    "investor": [
        "financial",
        "ghg_emissions",
        "energy",
        "water",
        "risk_management",
        "executive_compensation",
        "executive_shareholding",
        "governance",
    ],
    "esg_department": [
        "ghg_emissions",
        "energy",
        "water",
        "climate",
        "workforce_compensation",
        "workforce_turnover",
        "training_development",
        "harassment_ethics",
        "grievance_mechanism",
        "risk_management",
        "executive_compensation",
        "governance",
    ],
}

