class SingleArchitecture:
    """
    Single Agent Architecture
    """

    def __init__(self, agent):

        self.agent = agent
    def run(self, data):

        print("\n===== Running Single Agent Architecture =====")

        result = self.agent.run(data)

        # ===== ⭐ 新增：confidence 分级 =====
        def normalize_confidence(c):
            try:
                c = float(c)
                return max(0.0, min(1.0, c))
            except:
                return 0.0

        def map_confidence_level(score):
            if score < 0.2:
                return "非常不可靠"
            elif score < 0.4:
                return "不太可靠"
            elif score < 0.6:
                return "比较可靠"
            elif score < 0.8:
                return "可靠"
            else:
                return "非常可靠"

        # ⭐ 只在存在 confidence 时处理
        if isinstance(result, dict) and "confidence" in result:

            score = normalize_confidence(result.get("confidence", 0))

            result["confidence"] = map_confidence_level(score)

        print("===== Single Agent Completed =====\n")

        return result
