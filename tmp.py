import os
from kindwise import PlantApi, PlantIdentification, ClassificationLevel, UsageInfo, HealthAssessment
from openai import OpenAI
from datetime import datetime
from uapi import UapiClient
from uapi.errors import UapiError


KINDWISE_TOKEN = "FiO..."
WEATHER_TOKEN = "uapi-"
SILICONFLOW_API_KEY = "sk-"

images = ['lvluo_lesswater.png']


def plantHealthAPI(KINDWISE_API_KEY):
    api = PlantApi(api_key=KINDWISE_API_KEY)
    details = ['common_names', 'taxonomy', 'image']
    disease_details = ['local_name', 'description', 'treatment', 'cause']
    language = ['en']
    similar_images = True
    latitude_longitude = (49.20340, 16.57318)
    health = 'all'
    custom_id = 4
    date_time = datetime.now()
    max_image_size = 1500
    classification_level = ClassificationLevel.SPECIES
    classification_raw = False
    extra_get_params = None
    extra_post_params = None

    identification: PlantIdentification = api.identify(
        images,
        details=details,
        disease_details=disease_details,
        language=language,
        similar_images=similar_images,
        latitude_longitude=latitude_longitude,
        health=health,
        custom_id=custom_id,
        date_time=date_time,
        max_image_size=max_image_size,
        classification_level=classification_level,
        classification_raw=classification_raw,
        extra_get_params=extra_get_params,
        extra_post_params=extra_post_params,
    )
    return identification


def formatIdentification(disease_suggestions):
    diagnosis_info = f"{'=' * 20} 植株健康诊断报告 {'=' * 20}\n"
    for i, disease in enumerate(disease_suggestions, 1):
        details = disease.details
        # 基础信息
        diagnosis_info += f"建议 {i}: {disease.name.upper()}\n"
        diagnosis_info += f"匹配概率: {disease.probability:.2%}\n"
        diagnosis_info += f"本地名称: {details.get('local_name', 'N/A')}\n"
        diagnosis_info += "-" * 50 + "\n"
        # 病因描述
        diagnosis_info += f"【病因描述】:\n{details.get('description')}\n\n"
        # 治疗方案
        treatment = details.get('treatment', {})
        diagnosis_info += "【治疗方案】:\n"
        # 化学治疗
        chemical = treatment.get('chemical', [])
        diagnosis_info += f"  - 化学药剂: {', '.join(chemical) if chemical else '无建议药剂'}\n"
        # 生物/物理治疗
        biological = treatment.get('biological', [])
        if biological:
            diagnosis_info += "  - 生物/物理措施:\n"
            for step in biological:
                diagnosis_info += f"    * {step}\n"
        # 预防措施
        prevention = details.get('prevention', [])
        if prevention:
            diagnosis_info += "\n【预防措施】:\n"
            for prev in prevention:
                diagnosis_info += f"    * {prev}\n"
        # 发病诱因
        if details.get('cause'):
            diagnosis_info += f"\n【发病诱因】: {details.get('cause')}\n"

        diagnosis_info += f"\n{'=' * 60}\n"
        return diagnosis_info


def weatherInfo(WEATHER_API_TOKEN):
    client = UapiClient("https://uapis.cn", token=WEATHER_API_TOKEN)
    try:
        result = client.misc.get_misc_weather(city="天津", adcode="", extended=True, forecast=True, hourly=False,
                                              minutely=False, indices=False, lang="zh")
        print("[DEBUG] WEATHER API RETURN: ", result)
    except UapiError as exc:
        print(f"[ERROR] WEATHER API error: {exc}")

    weather_info = f"--- {result['city']} 未来7天天气关键信息 ---\n"
    weather_info += f"当前实时湿度: {result.get('humidity')}% | 当前紫外线指数: {result.get('uv')}\n"
    weather_info += "\n"

    for day in result.get('forecast', []):
        weather_info += f"{day.get('date')} ({day.get('week')})\n"
        weather_info += f"  温度: {day.get('temp_min')}℃ ~ {day.get('temp_max')}℃\n"
        weather_info += f"  天气: 白天 {day.get('weather_day')} / 夜间 {day.get('weather_night')}\n"
        weather_info += "\n"

    return weather_info


def llm_agent(disease_suggestions, weather_suggestions):
    system_prompt = """
    # Role
    你是一位集植物病理学、环境园艺学与家庭安全防护于一体的“全能植物护理管家”。你不仅精通植物诊疗，更优先关注家庭成员（婴幼儿、宠物）的生命安全。

    # Context & Inputs
    用户将为你提供三类核心信息：
    1. 【植物诊断报告】：来自 Kindwise API，包含病因概率、描述及官方建议。
    2. 【环境与家庭画像】：包含种植环境（室内/阳台/室外）、家庭成员（是否有猫/狗/婴幼儿）。
    3. 【实时天气预报】：所在城市未来 7 天的详细气象数据。

    # Core Constraints (最高指令)
    - **安全第一原则**：若家庭中有宠物或婴幼儿，严禁推荐任何具有挥发性毒性、残留期长或易误食的化学农药。优先推荐物理隔离、修剪或生物防治。
    - **环境匹配原则**：针对室内环境，需考虑通风受限对药剂挥发和水分蒸发的影响。
    - **植物特性提醒**：识别到特定植物（如绿萝、滴水观音）对宠物有毒时，必须主动提醒。

    # Logic Workflow
    1. **安全筛查**：对比诊断建议中的“化学药剂”与“家庭画像”。若有宠物/幼儿，必须否决高风险化学建议，并提供安全替代方案。
    2. **气象联动**：根据天气（如雨、晴、温差）修正诊断报告中的补救方案。
    3. **分阶段执行**：给出“即刻补救”与“长期预防”。

    # Output Format (结构化输出)
    ## 📋 综合画像
    - 植物健康总结：
    - 安全风险评级：(根据宠物/幼儿情况评定：低/中/高)

    ## 🛠️ 补救方案 (已通过家庭安全过滤)
    - **物理处理**：(如修剪、换土、遮荫等)
    - **安全防治**：(推荐无毒的替代方案，或极度谨慎的用药指导)

    ## 🗓️ 动态护理排期 (结合未来7天天气)
    - [日期/天气]：[具体操作建议]

    ## ⚠️ 家居安全特别提醒
    - (针对宠物/幼儿的具体防范建议，以及植物本身毒性的警示)
    """

    user_profile = {
        "location": "室内客餐厅",
        "members": ["1岁幼儿", "一只布偶猫"],
        "preferences": "倾向于有机、无毒的养护方法"
    }

    user_content = f"""
    ### 1. 环境与家庭画像
    - 种植位置：{user_profile['location']}
    - 家庭成员：{', '.join(user_profile['members'])}
    - 用户偏好：{user_profile['preferences']}

    ### 2. 植物诊断报告
    {disease_suggestions}

    ### 3. 未来7天天气预报
    {weather_suggestions}
    """

    client = OpenAI(
        api_key="sk-pdzganvyocumjlprxzejvvrdduwdrzrualtcjvfvzfcofkak",
        base_url="https://api.siliconflow.cn/v1"
    )

    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.5
    )

    print("[DEBUG] LLM AGENT RETURN: \n", response.choices[0].message.content)


if __name__ == '__main__':
    healthInfo = plantHealthAPI(KINDWISE_TOKEN)
    disease_suggestions = healthInfo.result.disease.suggestions
    weather_suggestions = weatherInfo(WEATHER_TOKEN)
    llm_agent(disease_suggestions, weather_suggestions)




