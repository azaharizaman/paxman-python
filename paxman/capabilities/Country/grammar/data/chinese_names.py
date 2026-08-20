"""Chinese (simplified) country name recognition keys.

Contains the Chinese country name representations the Country name
grammar recognizes. This is recognition-only data — keys are
syntax-normalized forms, and no token is mapped to a canonical country
here. CLDR rule data owns every localized token-to-country decision.

Chinese characters are preserved as-is (they are alphanumeric in Unicode).
Keys are normalized with normalize_name() at module construction.
"""

from __future__ import annotations

from paxman.capabilities.Country.notation import normalize_name

CHINESE_NAME_KEYS: frozenset[str] = frozenset(
    normalize_name(key)
    for key in {
        "中国",
        "美国",
        "日本",
        "韩国",
        "朝鲜",
        "马来西亚",
        "新加坡",
        "泰国",
        "越南",
        "印度尼西亚",
        "菲律宾",
        "俄罗斯",
        "英国",
        "法国",
        "德国",
        "意大利",
        "西班牙",
        "葡萄牙",
        "巴西",
        "墨西哥",
        "加拿大",
        "澳大利亚",
        "新西兰",
        "印度",
        "巴基斯坦",
        "孟加拉国",
        "斯里兰卡",
        "尼泊尔",
        "不丹",
        "马尔代夫",
        "阿富汗",
        "伊朗",
        "伊拉克",
        "沙特阿拉伯",
        "阿联酋",
        "卡塔尔",
        "科威特",
        "巴林",
        "阿曼",
        "约旦",
        "黎巴嫩",
        "叙利亚",
        "以色列",
        "巴勒斯坦",
        "埃及",
        "南非",
        "尼日利亚",
        "肯尼亚",
        "埃塞俄比亚",
        "坦桑尼亚",
        "乌干达",
        "加纳",
        "摩洛哥",
        "阿尔及利亚",
        "苏丹",
        "南苏丹",
        "阿根廷",
        "智利",
        "秘鲁",
        "哥伦比亚",
        "委内瑞拉",
        "古巴",
        "荷兰",
        "比利时",
        "瑞士",
        "瑞典",
        "挪威",
        "丹麦",
        "芬兰",
        "波兰",
        "奥地利",
        "希腊",
        "爱尔兰",
        "匈牙利",
        "乌克兰",
        "土耳其",
        "捷克",
        "罗马尼亚",
        "蒙古",
        "哈萨克斯坦",
    }
)
