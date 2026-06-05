class ConfidenceFusionArchitecture:
    def __init__(self, agents, weights=None):
        self.agents = agents
        self.weights = weights or {}

    def run(self, data):

        agent_outputs = {}

        # -----------------------------
        # 1️⃣ 收集 agent 输出
        # -----------------------------
        for agent in self.agents:
            output = agent.run(data)

            agent_name = getattr(agent, "name", agent.__class__.__name__)
            agent_outputs[agent_name] = output

        # -----------------------------
        # 2️⃣ 置信度融合
        # -----------------------------
        scores = {}

        for agent_name, output in agent_outputs.items():
            diagnosis = output.get("possible_diagnosis", "unknown")
            confidence = output.get("confidence_score", 0.5)

            weight = self.weights.get(agent_name, 1.0)

            if diagnosis not in scores:
                scores[diagnosis] = 0

            scores[diagnosis] += weight * confidence

        # -----------------------------
        # 3️⃣ 最终诊断
        # -----------------------------
        if not scores:
            return {"error": "No valid outputs from agents"}

        final_diagnosis = max(scores.items(), key=lambda x: x[1])[0]

        total_score = sum(scores.values())
        final_confidence = (
            scores[final_diagnosis] / total_score if total_score > 0 else 1.0
        )

        # -----------------------------
        # 4️⃣ 选最优报告
        # -----------------------------
        best_agent_name, best_output = max(
            agent_outputs.items(),
            key=lambda x: x[1].get("confidence_score", 0)
        )

        # -----------------------------
        # 5️⃣ 输出
        # -----------------------------
        return {
            "agent_outputs": agent_outputs,
            "fusion_scores": scores,
            "final_diagnosis": final_diagnosis,
            "final_confidence": final_confidence,
            "best_agent": best_agent_name,
            "final_report": best_output
        }