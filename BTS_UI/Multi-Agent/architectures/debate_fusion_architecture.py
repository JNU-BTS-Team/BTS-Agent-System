"""
Debate + Fusion Architecture

流程：
1. 多 agent 初始输出
2. 互相 critique（Debate）
3. 各自修正（Revision）
4. 字段融合（Fusion）
"""

import json


class DebateFusionArchitecture:

    def __init__(self, agents):
        self.agents = agents

        # 字段融合策略
        self.FIELD_STRATEGY = {
            "tumor_location": "confidence",
            "tumor_analysis": "confidence",
            "severity_assessment": "vote",
            "possible_diagnosis": "vote",
            "recommendation": "confidence",
            "need_doctor_review": "vote_bool",
            "confidence": "max",
            "confidence_reason": "best",
            "remarks": "best"
        }

    # ==========================================
    # 主流程
    # ==========================================
    def run(self, input_data, return_trace=False):
        initial_results = self.run_agents(input_data)
        critiques = self.debate(initial_results)
        revised_results = self.revise(initial_results, critiques)
        final_result = self.vote(revised_results)
        if return_trace:
            return final_result, {
                "initial_results": initial_results,
                "critiques": critiques,
                "revised_results": revised_results,
                "final_result": final_result,
            }
        return final_result

    # ==========================================
    # Step 1: 运行所有 agent
    # ==========================================
    def run_agents(self, input_data):

        results = []

        for agent in self.agents:

            print(f"\n[Debate] Running {agent.name}")

            result = agent.run(input_data)

            results.append({
                "agent": agent.name,
                "result": result
            })

        return results

    # ==========================================
    # Step 2: Debate（互评）
    # ==========================================
    def debate(self, results):

        critiques = []

        for agent in self.agents:

            others = [r for r in results if r["agent"] != agent.name]

            prompt = f"""
You are {agent.name}.

Other experts' results:
{json.dumps(others, ensure_ascii=False, indent=2)}

Your task:
- Identify mistakes or inconsistencies
- Point out weak reasoning
- Suggest improvements

Keep it concise. Output in Chinese.
"""

            critique = agent.llm_client.generate(prompt)

            critiques.append({
                "agent": agent.name,
                "critique": critique
            })

        return critiques

    # ==========================================
    # Step 3: Revision（修正）
    # ==========================================
    def revise(self, initial_results, critiques):

        revised_results = []

        for agent in self.agents:

            original = next(r for r in initial_results if r["agent"] == agent.name)

            other_critiques = [
                c["critique"] for c in critiques if c["agent"] != agent.name
            ]

            critique_text = "\n".join(other_critiques)

            prompt = f"""
You are {agent.name}.

Your original output:
{json.dumps(original["result"], ensure_ascii=False, indent=2)}

Other experts' critiques:
{critique_text}

Revise your answer.

IMPORTANT:
- Keep EXACT same JSON schema
- Improve correctness and consistency
- Output ONLY JSON
"""

            response = agent.llm_client.generate(prompt)

            revised = agent.parse_output(response)

            revised_results.append({
                "agent": agent.name,
                "result": revised
            })

        return revised_results


    # ==========================================
    # Step 4: Fusion（字段融合）
    # ==========================================

    def vote(self, results):

        def normalize_confidence(c):
            try:
                c = float(c)
                return max(0.0, min(1.0, c))  # 限制在[0,1]
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

        if not results:
            return {"error": "No valid results"}

        agent_results = [item["result"] for item in results]

        # 最优 agent（仍用于其它字段）
        best_result = max(
            agent_results,
            key=lambda x: normalize_confidence(x.get("confidence", 0))
        )

        final = {}

        for key in best_result.keys():

            # ⭐⭐⭐ 核心修改：confidence 单独处理（输出等级）
            if key == "confidence":
                confs = [
                    normalize_confidence(r.get("confidence", 0))
                    for r in agent_results
                ]

                avg_conf = sum(confs) / len(confs)

                final["confidence"] = map_confidence_level(avg_conf)

                continue

            strategy = self.FIELD_STRATEGY.get(key, "confidence")
            values = [r.get(key) for r in agent_results]

            # ===== vote（字符串）=====
            if strategy == "vote":
                counter = {}
                for v in values:
                    counter[v] = counter.get(v, 0) + 1
                final[key] = max(counter, key=counter.get)

            # ===== bool 投票 =====
            elif strategy == "vote_bool":
                true_count = sum(1 for v in values if v)
                final[key] = true_count >= (len(values) / 2)

            # ===== confidence 选（选最高置信度的值）=====
            elif strategy == "confidence":
                best_value = None
                best_score = -1

                for r in agent_results:
                    score = normalize_confidence(r.get("confidence", 0))
                    if score > best_score:
                        best_score = score
                        best_value = r.get(key)

                final[key] = best_value

            # ===== 最大 confidence（但不影响输出字段）=====
            elif strategy == "max":
                final[key] = best_result.get(key)

            # ===== 直接用最佳 agent =====
            elif strategy == "best":
                final[key] = best_result.get(key)

            else:
                final[key] = best_result.get(key)

        return final
