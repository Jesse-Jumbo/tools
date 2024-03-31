# 男、女宿床位數
vacancy_updated = {
    "女宿": {"勝四": 20, "勝三": 72, "勝九": 143, "勝二": 58, "勝八": 228},
    "男宿": {"光一": 276, "勝一": 539, "敬一": 337, "光二": 273}
}

# 男、女宿報名人數
registrations_updated = {
    "女宿": {
        "勝四": [81, 198, 262, 318, 270],
        "勝三": [276, 269, 265, 249, 70],
        "勝九": [335, 342, 273, 136, 43],
        "勝二": [128, 175, 171, 294, 361],
        "勝八": [309, 145, 158, 132, 385]
    },
    "男宿": {
        "光一": [545, 645, 304, 61, 0],
        "勝一": [189, 97, 277, 992, 0],
        "敬一": [302, 188, 667, 398, 0],
        "光二": [519, 625, 307, 104, 0]
    }
}

# 初始化剩餘名額和中籤概率的存儲
probability = {}
remaining_vacancy = {}

# 分別對男宿和女宿計算剩餘名額和中籤概率
for dorm_category in vacancy_updated:
    remaining_vacancy[dorm_category] = {dorm: vacancy_updated[dorm_category][dorm] for dorm in vacancy_updated[dorm_category]}
    probability[dorm_category] = {}

    for i in range(5):
        probability[dorm_category][i + 1] = {}
        for dorm in registrations_updated[dorm_category]:
            # 如果剩餘名額為0，則中籤概率為0
            if remaining_vacancy[dorm_category][dorm] == 0:
                probability[dorm_category][i + 1][dorm] = 0
            else:
                # 計算中籤概率
                prob = remaining_vacancy[dorm_category][dorm] / registrations_updated[dorm_category][dorm][i]
                probability[dorm_category][i + 1][dorm] = prob if prob < 1 else 1  # 概率不會超過1
                # 更新剩餘名額
                remaining_vacancy[dorm_category][dorm] -= min(remaining_vacancy[dorm_category][dorm], registrations_updated[dorm_category][dorm][i])

# 輸出計算結果
# 將计算的中籤概率格式化输出
for dorm_category, prob_by_choice in probability.items():
    print(f"{dorm_category}:")
    for choice, probs in prob_by_choice.items():
        print(f"  第{choice}志願:")
        for dorm, prob in probs.items():
            print(f"    {dorm}: {prob:.2%}")
    print()
